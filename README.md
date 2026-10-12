# ✨ EventDhara AI Image Metadata Studio

An intelligent event styling intelligence platform and chatbot built with **Python**, **Streamlit**, **Groq Vision API**, and **OpenPyXL**.

Automatically captures Pinterest Pin images headlessly, inspects them using Groq's high-speed Vision AI, extracts structured professional event metadata, and maintains a styled master Excel catalog: `EventDhara_Metadata.xlsx`.

---

## 🚀 Key Features

1. **Headless Pinterest Image Retrieval:**
   - Automatically downloads the highest-resolution available image directly from Pinterest links (including `pinterest.com/pin/...`, `pin.it/...` shortlinks, and `i.pinimg.com` CDN links).
   - Upgrades resolution from `/736x/` or `/474x/` to uncompressed `/originals/`.
   - Never opens a browser window.
   - Detects login walls, age restrictions, or deleted pins with helpful fallbacks.

2. **Groq Vision AI Analysis:**
   - Powered by Meta's `llama-3.2-11b-vision-preview` (ultra-fast) or `llama-3.2-90b-vision-preview` (high-capacity).
   - Generates fact-based, rich metadata without hallucinating:
     - **Serial Number & Image ID** (`ED-IMG-0001`, `ED-IMG-0002`...)
     - **Image Name & Title**
     - **Short Description & Detailed Long Description**
     - **Image Inclusions** (identifiable furniture, fabrics, flowers, props, lighting)
     - **Keywords & Search Tags** (SEO-ready comma-separated tags)
     - **Event Category & Theme** (e.g., Wedding, Haldi, Royal Rajasthani, Bohemian)
     - **Color Palette, Venue Type & Lighting Atmosphere**
     - **Original Pinterest URL & Local Image Path**

3. **Executive-Grade Excel Generation (`EventDhara_Metadata.xlsx`):**
   - Formatted with dark slate headers (`#1E293B`), white bold text, and freeze panes (`A2`).
   - Alternating row zebra striping (`#F8FAFC`).
   - Auto-filters enabled across all columns.
   - Automatic text wrapping on descriptions and inclusions.
   - Sequential serial numbers guaranteed (`1, 2, 3...`).
   - Content hash (MD5) and URL deduplication prevents duplicate entries while preserving historical records.

4. **Multi-Mode UI:**
   - **💬 AI Pin Chatbot:** Single URL analysis with live status progress and side-by-side view (Image on left, Metadata table on right).
   - **⚡ Batch URL Processor:** Bulk process multiple URLs; automatically continues if any individual link fails.
   - **📤 Fallback Image Uploader:** Direct file upload (JPG/PNG/WEBP) for private or restricted Pinterest pins.
   - **📊 Master Catalog Explorer:** Search, filter by category/theme, and 1-click download `EventDhara_Metadata.xlsx`.

---

## 📂 Project Structure

```
Event_Dhara/
├── app.py                      # Streamlit Studio application & UI
├── requirements.txt            # Python dependencies
├── .env.example                # Example environment variables
├── .env                        # Active environment variables (Groq API Key)
├── run_app.bat                 # 1-Click Windows batch launcher
├── README.md                   # Documentation and Windows instructions
├── modules/
│   ├── __init__.py             # Package initializer
│   ├── config.py               # Paths, schema, model configuration
│   ├── utils.py                # Hashing, resizing, base64, sanitization
│   ├── pinterest_scraper.py    # Headless Pinterest image scraper
│   ├── vision_analyzer.py      # Groq Vision AI integration & prompt
│   └── excel_manager.py        # OpenPyXL master Excel engine & deduplication
├── images/                     # Saved high-res downloaded & uploaded images
└── data/                       # Backups and auxiliary data
```

---

## 🪟 Windows Setup Instructions

### Prerequisites
- **Python 3.10+** (Tested on Python 3.11, 3.12, 3.13)
- Windows PowerShell or Command Prompt
- Free Groq API Key from [https://console.groq.com/keys](https://console.groq.com/keys)

### Step 1: Open Terminal in Project Folder
Open PowerShell or Command Prompt in `d:\Porjects\Event_Dhara`:
```powershell
cd d:\Porjects\Event_Dhara
```

### Step 2: Install Dependencies
Install all required libraries using pip:
```powershell
python -m pip install -r requirements.txt
```

### Step 3: Configure Groq API Key
You can configure the key in either of two ways:
1. **Option A (In `.env` file):**
   Open `.env` in any text editor and paste your key:
   ```env
   GROQ_API_KEY=gsk_your_actual_groq_api_key_here
   ```
2. **Option B (Directly in the Streamlit UI):**
   You can also launch the app and paste the key directly in the left sidebar password input. It will be verified and automatically saved into `.env`.

### Step 4: Run the Application
You can run the app with either:
- **Option 1 (Double-Click):** Double click `run_app.bat` in File Explorer.
- **Option 2 (Terminal):**
  ```powershell
  python -m streamlit run app.py
  ```
The application will launch automatically in your browser at `http://localhost:8501`.

---

## 🧪 Testing and Verification

To verify the installation and components, you can run a dry-run test:

```powershell
python -c "from modules.pinterest_scraper import PinterestScraper; from modules.excel_manager import ExcelManager; print('Modules loaded successfully!')"
```

### What has been tested:
1. **Pinterest URL Extraction:** Tested with active Pinterest pins, verifying HTTP redirects, OpenGraph image parsing, and full resolution upgrade from `/736x/` to `/originals/`.
2. **Headless Image Downloading & Hashing:** Verified image download to `images/`, PIL image integrity checking, and MD5 hash generation.
3. **OpenPyXL Excel Generation & Formatting:** Verified header styling, zebra striping, text wrapping, auto-filters, sequential numbering, and URL + hash duplicate prevention.
4. **Login Restriction Handling:** Tested error reporting and fallback mechanism for restricted pins.

### What requires user credentials:
- **Groq Vision API Invocations:** The Vision AI integration code is fully implemented and tested with the official `groq` SDK (`v1.7.0`). Live vision completion requires the user's free Groq API key from [console.groq.com](https://console.groq.com/keys).
