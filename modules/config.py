import os
from pathlib import Path
from dotenv import load_dotenv

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
IMAGES_DIR = BASE_DIR / "images"
DATA_DIR = BASE_DIR / "data"
EXCEL_FILE_PATH = BASE_DIR / "EventDhara_Metadata.xlsx"
ENV_FILE_PATH = BASE_DIR / ".env"

# Ensure directories exist
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Load environment variables
load_dotenv(dotenv_path=ENV_FILE_PATH)

# Groq Vision Configuration
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
DEFAULT_VISION_MODEL = "qwen/qwen3.8-27b"
AVAILABLE_VISION_MODELS = [
    "qwen/qwen3.8-27b",
]

# Request Headers for Scraping
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/[IP_ADDRESS] Safari/537.36"
)

REQUEST_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.pinterest.com/",
}

# Excel Columns Definition
EXCEL_COLUMNS = [
    "S.No",
    "Image ID",
    "Image Name",
    "Title",
    "Event Category",
    "Event Theme",
    "Short Description",
    "Long Description",
    "Image Inclusions",
    "Keywords and Search Tags",
    "Color Palette",
    "Setting / Venue",
    "Lighting / Ambience",
    "Original Pinterest URL",
    "Local Image Path",
    "Image Hash (MD5)",
    "Analyzed At"
]

# Excel Column Widths
COLUMN_WIDTHS = {
    1: 8,    # S.No
    2: 18,   # Image ID
    3: 26,   # Image Name
    4: 32,   # Title
    5: 20,   # Event Category
    6: 24,   # Event Theme
    7: 42,   # Short Description
    8: 58,   # Long Description
    9: 50,   # Image Inclusions
    10: 42,  # Keywords and Search Tags
    11: 26,  # Color Palette
    12: 22,  # Setting / Venue
    13: 24,  # Lighting / Ambience
    14: 38,  # Original Pinterest URL
    15: 34,  # Local Image Path
    16: 35,  # Image Hash (MD5)
    17: 22   # Analyzed At
}

# UI Styling Constants
EXCEL_HEADER_BG = "1E293B"      # Dark Slate
EXCEL_HEADER_FG = "FFFFFF"      # White
EXCEL_ZEBRA_BG = "F8FAFC"       # Light Slate
EXCEL_BORDER_COLOR = "CBD5E1"   # Slate border
