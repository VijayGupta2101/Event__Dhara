import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from modules.config import BASE_DIR, IMAGES_DIR, DATA_DIR, EXCEL_FILE_PATH
from modules.pinterest_scraper import PinterestScraper
from modules.excel_manager import ExcelManager
from modules.vision_analyzer import VisionAnalyzer
from modules.utils import compute_md5, sanitize_filename, format_image_id

def run_verification():
    print("==================================================")
    print("   EventDhara AI Studio System Verification")
    print("==================================================")

    # 1. Directory Structure
    print("\n[1/5] Verifying directories...")
    assert IMAGES_DIR.exists(), f"Images directory missing: {IMAGES_DIR}"
    assert DATA_DIR.exists(), f"Data directory missing: {DATA_DIR}"
    print("  ✓ Images and data directories exist.")

    # 2. Excel Engine & Styling
    print("\n[2/5] Verifying Excel Engine (openpyxl)...")
    test_excel_path = DATA_DIR / "verification_test.xlsx"
    if test_excel_path.exists():
        test_excel_path.unlink()

    mgr = ExcelManager(test_excel_path)
    assert test_excel_path.exists(), "Excel file was not created"

    # Test append
    sample_rec = {
        "Image Name": "test_mandap.jpg",
        "Title": "Grand Floral Mandap",
        "Event Category": "Wedding",
        "Event Theme": "Royal Rajasthani",
        "Short Description": "A luxury mandap setup.",
        "Long Description": "A breathtaking mandap stage adorned with roses and hydrangeas.",
        "Image Inclusions": "Floral arch, brass urlis, red carpet",
        "Keywords and Search Tags": "wedding decor, royal mandap",
        "Color Palette": "Red, Gold, Ivory",
        "Setting / Venue": "Outdoor Lawn",
        "Lighting / Ambience": "Warm Fairy Light Glow",
        "Original Pinterest URL": "https://www.pinterest.com/pin/14073817581534067/",
        "Local Image Path": "images/test_mandap.jpg",
        "Image Hash (MD5)": "1234567890abcdef1234567890abcdef",
        "Analyzed At": "2026-10-11 18:00:00"
    }

    res = mgr.append_record(sample_rec)
    assert res["success"] is True, f"Failed to append record: {res}"
    assert res["sno"] == 1, f"Expected S.No 1, got {res['sno']}"
    assert res["image_id"] == "ED-IMG-0001", f"Expected ED-IMG-0001, got {res['image_id']}"
    print(f"  ✓ Record appended successfully as S.No #{res['sno']} ({res['image_id']}).")

    # Test Duplicate Prevention (URL)
    dup_res = mgr.append_record(sample_rec)
    assert dup_res["success"] is False, "Duplicate URL was not caught"
    assert dup_res["is_duplicate"] is True, "Duplicate flag not set"
    print("  ✓ Duplicate URL prevention verified.")

    # Test DataFrame retrieval
    df = mgr.get_as_dataframe()
    assert len(df) == 1, f"Expected 1 record in DataFrame, got {len(df)}"
    print("  ✓ DataFrame export verified.")

    # Clean up test excel
    if test_excel_path.exists():
        test_excel_path.unlink()

    # 3. Utilities & Sanitization
    print("\n[3/5] Verifying utility functions...")
    clean_name = sanitize_filename("Grand Royal Mandap / Wedding #1?")
    assert clean_name == "grand_royal_mandap_wedding_1", f"Unexpected clean name: {clean_name}"
    img_id = format_image_id(42)
    assert img_id == "ED-IMG-0042", f"Unexpected image ID: {img_id}"
    print("  ✓ Sanitization & ID formatting verified.")

    # 4. Pinterest Headless Scraper
    print("\n[4/5] Verifying Pinterest Scraper (live headless extraction)...")
    scraper = PinterestScraper()
    test_pin_url = "https://www.pinterest.com/pin/14073817581534067/"
    scrape_result = scraper.extract_and_download(test_pin_url, output_dir=DATA_DIR, image_name_prefix="VERIFY")
    assert scrape_result["success"] is True, f"Scrape failed: {scrape_result.get('error')}"
    assert Path(scrape_result["local_path"]).exists(), "Downloaded image file missing"
    assert scrape_result["width"] > 0 and scrape_result["height"] > 0, "Invalid image dimensions"
    print(f"  ✓ Image downloaded: {scrape_result['filename']} ({scrape_result['width']}x{scrape_result['height']} px)")
    print(f"  ✓ High-res URL: {scrape_result['image_url']}")

    # Clean up downloaded test image
    if Path(scrape_result["local_path"]).exists():
        Path(scrape_result["local_path"]).unlink()

    # 5. Vision AI Client Initialization
    print("\n[5/5] Verifying Vision Analyzer client...")
    vis = VisionAnalyzer(api_key="mock_key_for_test")
    assert vis.model == "llama-3.2-11b-vision-preview"
    json_parse_test = vis._clean_and_parse_json('```json\n{"title": "Test Decor", "event_category": "Wedding"}\n```')
    assert json_parse_test.get("title") == "Test Decor", "JSON cleaning failed"
    print("  ✓ Vision analyzer JSON parser verified.")

    print("\n==================================================")
    print("   ALL TESTS PASSED! System is 100% operational.")
    print("==================================================")

if __name__ == "__main__":
    run_verification()
