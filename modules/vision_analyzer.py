import json
import logging
import re
from pathlib import Path
from groq import Groq

from modules.config import DEFAULT_VISION_MODEL
from modules.utils import resize_and_encode_image

logger = logging.getLogger("vision_analyzer")

VISION_PROMPT = """You are EventDhara Vision AI, an elite event decor and styling metadata analyst.
Analyze the provided event or decor image with utmost precision and realism.

STRICT RULES:
1. Base your analysis STRICTLY on what is visibly present in the image. NEVER invent, hallucinate, or assume unrepresented details.
2. Identify all decor elements, floral arrangements, props, furniture, stage structures, fabrics, lighting, and architectural features.
3. Classify the Event Category (e.g., Wedding, Haldi, Mehendi, Sangeet, Reception, Cocktail Party, Birthday, Corporate Gala, Baby Shower, Anniversary, Housewarming, Festive Decor).
4. Determine the Event Theme (e.g., Royal Rajasthani, Bohemian Chic, Modern Minimalist, Enchanted Floral Forest, Vintage European, Celestial Gold, Pastel Dream, Rustic Garden, Tropical Glam).
5. Extract the dominant Color Palette (list 3-5 distinct colors).
6. Note the Setting/Venue type (e.g., Outdoor Lawn, Indoor Banquet, Poolside, Mandap Stage, Beachfront, Terrace) and Lighting/Ambience (e.g., Daylight, Warm Fairy Light Glow, Candlelit, Night Stage Lighting).

Return ONLY a valid JSON object matching this EXACT schema with no additional commentary:
{
  "title": "A captivating, professional title for this decor setup (5-10 words)",
  "event_category": "Primary event type",
  "event_theme": "Specific aesthetic theme",
  "short_description": "A crisp, evocative 1-2 sentence overview of the setup",
  "long_description": "A detailed, professional 3-5 sentence narrative describing the staging, backdrop, materials, floral composition, textures, and visual ambiance",
  "image_inclusions": "Comprehensive comma-separated list of all visible elements, furniture, decor items, and flowers",
  "keywords": "15-20 comma-separated high-traffic search tags and keywords",
  "color_palette": "Comma-separated list of dominant visible colors",
  "setting_venue": "Venue type or physical setting",
  "lighting_ambience": "Lighting condition and ambient atmosphere"
}
"""

class VisionAnalyzer:
    def __init__(self, api_key: str | None = None, model: str = DEFAULT_VISION_MODEL):
        self.api_key = (api_key or "").strip()
        self.model = model
        self.client = Groq(api_key=self.api_key) if self.api_key else None

    def analyze_image(self, image_path: str | Path, context_hint: str = "") -> dict:
        """
        Analyzes an image using Groq Vision API.
        
        Returns dict:
            {
                "success": bool,
                "metadata": dict | None,
                "error": str | None
            }
        """
        if not self.api_key:
            return {
                "success": False,
                "metadata": None,
                "error": "Groq API key is missing. Please enter your key in the sidebar or add it to .env."
            }

        image_path = Path(image_path)
        if not image_path.exists():
            return {
                "success": False,
                "metadata": None,
                "error": f"Image file not found at: {image_path}"
            }

        try:
            # Resize (if too big) and encode image to base64
            base64_img, mime_type = resize_and_encode_image(image_path, max_dimension=1600)
            
            user_prompt = VISION_PROMPT
            if context_hint:
                user_prompt += f"\n\nContext Hint from source: '{context_hint}'"

            # Call Groq Vision API
            client = Groq(api_key=self.api_key)
            print("DEBUG: Selected vision model:", self.model)
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{base64_img}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.2,
                max_tokens=1024,
                response_format={"type": "json_object"}
            )

            raw_text = response.choices[0].message.content.strip()
            parsed_metadata = self._clean_and_parse_json(raw_text)

            # Ensure all required keys exist with sensible fallbacks
            normalized_metadata = {
                "title": parsed_metadata.get("title") or "Event Decor Setup",
                "event_category": parsed_metadata.get("event_category") or "Wedding & Celebration",
                "event_theme": parsed_metadata.get("event_theme") or "Contemporary Elegant",
                "short_description": parsed_metadata.get("short_description") or "An elegantly styled event setup.",
                "long_description": parsed_metadata.get("long_description") or "A thoughtfully designed event aesthetic featuring curated decor and floral elements.",
                "image_inclusions": parsed_metadata.get("image_inclusions") or "Decor setup, stage elements, ambient lighting",
                "keywords": parsed_metadata.get("keywords") or "event decor, party styling, celebration setup",
                "color_palette": parsed_metadata.get("color_palette") or "Multicolor",
                "setting_venue": parsed_metadata.get("setting_venue") or "Event Venue",
                "lighting_ambience": parsed_metadata.get("lighting_ambience") or "Ambient lighting"
            }

            return {
                "success": True,
                "metadata": normalized_metadata,
                "raw_response": raw_text,
                "error": None
            }

        except Exception as e:
            err_msg = str(e)
            if "invalid_api_key" in err_msg.lower() or "authentication" in err_msg.lower() or "401" in err_msg:
                error_desc = "Invalid Groq API Key. Please verify your key at console.groq.com."
            elif "rate_limit" in err_msg.lower() or "429" in err_msg:
                error_desc = "Groq API rate limit exceeded. Please wait a moment before trying again."
            else:
                error_desc = f"Groq Vision API Error: {err_msg}"

            return {
                "success": False,
                "metadata": None,
                "error": error_desc
            }

    def _clean_and_parse_json(self, text: str) -> dict:
        """Strips markdown code fences and parses raw JSON cleanly."""
        text = text.strip()
        # Remove ```json ... ```
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
            text = text.strip()

        # Find first { and last }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            json_str = text[start : end + 1]
            return json.loads(json_str)

        return json.loads(text)
