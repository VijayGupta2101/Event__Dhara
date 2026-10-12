import re
import json
import logging
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from PIL import Image
import io

from modules.config import REQUEST_HEADERS, IMAGES_DIR
from modules.utils import compute_md5, sanitize_filename

logger = logging.getLogger("pinterest_scraper")

class PinterestScraper:
    def __init__(self, session: requests.Session | None = None):
        self.session = session or requests.Session()
        self.session.headers.update(REQUEST_HEADERS)

    def extract_and_download(
        self,
        url: str,
        output_dir: Path | str = IMAGES_DIR,
        image_name_prefix: str = "ED_PIN"
    ) -> dict:
        """
        Retrieves the image from a Pinterest URL or direct image link without opening a browser.
        Attempts to fetch the highest available resolution (originals).
        
        Returns dict:
            {
                "success": bool,
                "local_path": str,
                "filename": str,
                "image_url": str,
                "image_hash": str,
                "title_hint": str,
                "width": int,
                "height": int,
                "file_size": int,
                "error": str | None,
                "is_login_restricted": bool
            }
        """
        url = url.strip()
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        if not url:
            return {"success": False, "error": "Empty URL provided", "is_login_restricted": False}

        # Check if URL scheme is missing
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        # 1. Handle direct Pinterest image links or direct image URLs
        parsed = urlparse(url)
        is_direct_image = any(
            parsed.path.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]
        )

        image_url = None
        title_hint = ""

        if is_direct_image:
            image_url = url
            title_hint = Path(parsed.path).stem
        else:
            # 2. Fetch HTML page with redirects enabled (handles pin.it & international domains)
            try:
                resp = self.session.get(url, timeout=15, allow_redirects=True)
            except requests.exceptions.RequestException as e:
                return {
                    "success": False,
                    "error": f"Network error connecting to Pinterest: {str(e)}",
                    "is_login_restricted": False
                }

            # Check if redirected to a login wall
            final_url = resp.url.lower()
            if "/login" in final_url or "accounts.google.com" in final_url:
                return {
                    "success": False,
                    "error": "This Pinterest Pin is private or requires login. Use the Fallback Image Upload option.",
                    "is_login_restricted": True
                }

            if resp.status_code == 404:
                return {
                    "success": False,
                    "error": "Pinterest Pin not found (404). It may have been deleted.",
                    "is_login_restricted": False
                }

            if resp.status_code != 200:
                return {
                    "success": False,
                    "error": f"Pinterest returned HTTP {resp.status_code}",
                    "is_login_restricted": False
                }

            soup = BeautifulSoup(resp.text, "html.parser")

            # Extract title if present
            og_title = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "og:title"})
            if og_title and og_title.get("content"):
                title_hint = og_title["content"].strip()
            elif soup.title and soup.title.string:
                title_hint = soup.title.string.strip()

            # Clean generic title suffixes
            title_hint = re.sub(r"\s*\|\s*Pinterest.*$", "", title_hint, flags=re.IGNORECASE)

            # Strategy A: OpenGraph image meta tag
            og_img = soup.find("meta", property="og:image") or soup.find("meta", attrs={"name": "og:image"})
            if og_img and og_img.get("content"):
                candidate_url = og_img["content"].strip()
                # Ensure it's not a tiny generic icon
                if not candidate_url.endswith("/favicon.ico") and "badge" not in candidate_url:
                    image_url = candidate_url

            # Strategy B: Twitter Image meta tag
            if not image_url:
                tw_img = soup.find("meta", attrs={"name": "twitter:image"})
                if tw_img and tw_img.get("content"):
                    image_url = tw_img["content"].strip()

            # Strategy C: Schema JSON-LD
            if not image_url:
                for script in soup.find_all("script", type="application/ld+json"):
                    try:
                        data = json.loads(script.string or "{}")
                        if isinstance(data, dict):
                            if "image" in data:
                                img_val = data["image"]
                                if isinstance(img_val, str):
                                    image_url = img_val
                                    break
                                elif isinstance(img_val, dict) and "url" in img_val:
                                    image_url = img_val["url"]
                                    break
                    except Exception:
                        pass

            # Strategy D: Regex scan for full-size i.pinimg.com image URL
            if not image_url:
                match = re.search(r'"image":\s*"(https://i\.pinimg\.com/[^"]+)"', resp.text)
                if match:
                    image_url = match.group(1).replace(r"\/", "/")

            # Strategy E: Preload links
            if not image_url:
                preload = soup.find("link", rel="preload", as_="image")
                if preload and preload.get("href") and "pinimg.com" in preload.get("href"):
                    image_url = preload["href"]

            if not image_url:
                return {
                    "success": False,
                    "error": "Could not locate a public image on this Pinterest page. Use the Fallback Image Upload option.",
                    "is_login_restricted": False
                }

        # 3. Upgrade resolution to full quality (originals) if applicable
        high_res_url = image_url
        if "i.pinimg.com" in image_url:
            for size_tag in ["/736x/", "/564x/", "/474x/", "/236x/"]:
                if size_tag in image_url:
                    upgrade_candidate = image_url.replace(size_tag, "/originals/")
                    try:
                        head_chk = self.session.head(upgrade_candidate, timeout=5)
                        if head_chk.status_code == 200:
                            high_res_url = upgrade_candidate
                            break
                    except Exception:
                        pass

        # 4. Download image content
        try:
            img_resp = self.session.get(high_res_url, timeout=20)
            if img_resp.status_code != 200 and high_res_url != image_url:
                # Fall back to original candidate URL if upgrade failed
                img_resp = self.session.get(image_url, timeout=20)

            if img_resp.status_code != 200:
                return {
                    "success": False,
                    "error": f"Failed to download image: HTTP {img_resp.status_code}",
                    "is_login_restricted": False
                }

            image_bytes = img_resp.content

            # Validate image integrity with PIL
            with Image.open(io.BytesIO(image_bytes)) as pil_img:
                width, height = pil_img.size
                format_ext = (pil_img.format or "JPEG").lower()
                if format_ext == "jpeg":
                    format_ext = "jpg"

        except Exception as e:
            return {
                "success": False,
                "error": f"Invalid image downloaded or decoding failed: {str(e)}",
                "is_login_restricted": False
            }

        # 5. Compute hash and create unique filename
        img_hash = compute_md5(image_bytes)
        clean_hint = sanitize_filename(title_hint, max_length=30)
        filename = f"{image_name_prefix}_{clean_hint}_{img_hash[:8]}.{format_ext}"
        local_file_path = output_dir / filename

        # 6. Save image to disk
        try:
            with open(local_file_path, "wb") as f:
                f.write(image_bytes)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to save image to disk: {str(e)}",
                "is_login_restricted": False
            }

        return {
            "success": True,
            "local_path": str(local_file_path),
            "filename": filename,
            "image_url": high_res_url,
            "image_hash": img_hash,
            "title_hint": title_hint,
            "width": width,
            "height": height,
            "file_size": len(image_bytes),
            "error": None,
            "is_login_restricted": False
        }
