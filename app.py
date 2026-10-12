import os
import time
from pathlib import Path
from datetime import datetime
import streamlit as pd_st  # alias if needed
import streamlit as st
import pandas as pd
from PIL import Image

from modules.config import (
    BASE_DIR,
    IMAGES_DIR,
    DATA_DIR,
    EXCEL_FILE_PATH,
    ENV_FILE_PATH,
    DEFAULT_VISION_MODEL,
    AVAILABLE_VISION_MODELS,
    GROQ_API_KEY
)
from modules.pinterest_scraper import PinterestScraper
from modules.vision_analyzer import VisionAnalyzer
from modules.excel_manager import ExcelManager
from modules.utils import (
    compute_md5,
    sanitize_filename,
    format_image_id,
    save_env_key,
    format_file_size
)

# Streamlit Page Setup
st.set_page_config(
    page_title="EventDhara AI | Image Metadata Studio",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-End Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, sans-serif;
    }
    
    h1, h2, h3, h4 {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 600;
        letter-spacing: -0.02em;
    }
    
    /* Main Background & Accent Styling */
    .brand-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #0F172A 100%);
        border: 1px solid rgba(245, 158, 11, 0.25);
        padding: 24px 32px;
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
    }
    
    .brand-title {
        color: #F8FAFC;
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .brand-subtitle {
        color: #94A3B8;
        font-size: 1.05rem;
        margin-top: 6px;
        margin-bottom: 0;
    }
    
    .brand-gold {
        color: #F59E0B;
        font-weight: 700;
    }
    
    /* Card Styles */
    .metric-card {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px 20px;
        text-align: center;
    }
    
    .metric-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #F59E0B;
    }
    
    .metric-lbl {
        font-size: 0.85rem;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 4px;
    }
    
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    .badge-success { background: #064E3B; color: #34D399; border: 1px solid #059669; }
    .badge-warn { background: #78350F; color: #FBBF24; border: 1px solid #D97706; }
    .badge-info { background: #1E1B4B; color: #818CF8; border: 1px solid #4F46E5; }
    
    .inclusion-tag {
        display: inline-block;
        background: #334155;
        color: #E2E8F0;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.82rem;
        margin: 2px 4px 2px 0;
    }
    
    .keyword-tag {
        display: inline-block;
        background: #1E293B;
        border: 1px solid #475569;
        color: #CBD5E1;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.78rem;
        margin: 2px 3px 2px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_processed" not in st.session_state:
    st.session_state.last_processed = None

# Initialize Singletons
excel_mgr = ExcelManager(EXCEL_FILE_PATH)
scraper = PinterestScraper()

# Sidebar Setup
with st.sidebar:
    st.markdown("### 🏛️ **EventDhara Studio**")
    st.caption("AI-Powered Event Decor Intelligence")
    st.divider()

    # Groq API Key Configuration
    st.markdown("#### 🔑 **Groq Vision API**")
    current_key = os.getenv("GROQ_API_KEY", GROQ_API_KEY).strip()
    
    api_key_input = st.text_input(
        "Groq API Key",
        value=current_key,
        type="password",
        placeholder="gsk_...",
        help="Obtain a free Groq API key at https://console.groq.com/keys"
    )

    if api_key_input != current_key:
        os.environ["GROQ_API_KEY"] = api_key_input
        save_env_key("GROQ_API_KEY", api_key_input, ENV_FILE_PATH)
        st.success("API Key updated and saved to `.env`!", icon="✅")

    # API Status Indicator
    if api_key_input:
        st.markdown('<span class="status-badge badge-success">● Groq Vision Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge badge-warn">● API Key Missing</span>', unsafe_allow_html=True)
        st.info("Get a free API key at [console.groq.com](https://console.groq.com/keys) to analyze images.")

    # Vision Model Selector
    selected_model = st.selectbox(
        "Vision Model",
        options=AVAILABLE_VISION_MODELS,
        index=0,
        help="llama-3.2-11b-vision-preview is ultra-fast. llama-3.2-90b-vision-preview provides deepest aesthetic reasoning."
    )

    st.divider()

    # Master Excel Status & Quick Download
    st.markdown("#### 📑 **Master Excel File**")
    st.text(f"File: {EXCEL_FILE_PATH.name}")
    
    all_records = excel_mgr.get_existing_records()
    st.text(f"Total Entries: {len(all_records)} records")

    if EXCEL_FILE_PATH.exists():
        with open(EXCEL_FILE_PATH, "rb") as f:
            excel_bytes = f.read()
        st.download_button(
            label="📥 Download Master Excel",
            data=excel_bytes,
            file_name="EventDhara_Metadata.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    st.divider()
    st.markdown("#### 📁 **Storage Locations**")
    st.caption(f"**Images:** `{IMAGES_DIR}`")
    st.caption(f"**Excel:** `{EXCEL_FILE_PATH}`")
    st.caption(f"**Data:** `{DATA_DIR}`")


# Header Banner
st.markdown("""
<div class="brand-header">
    <div class="brand-title">
        ✨ Event<span class="brand-gold">Dhara</span> AI Image Metadata Studio
    </div>
    <div class="brand-subtitle">
        Automated Pinterest Image Harvester & Groq Vision AI Metadata Engine for Event Professionals
    </div>
</div>
""", unsafe_allow_html=True)

# Main Application Tabs
tab_chat, tab_batch, tab_upload, tab_catalog = st.tabs([
    "💬 AI Pin Chatbot",
    "⚡ Batch URL Processor",
    "📤 Fallback Image Uploader",
    "📊 Master Excel Catalog"
])

# -------------------------------------------------------------
# TAB 1: AI PIN CHATBOT / SINGLE URL PROCESSOR
# -------------------------------------------------------------
with tab_chat:
    st.markdown("### 🎯 **Analyze Pinterest Pin via URL**")
    st.markdown("Paste a Pinterest pin URL (`pinterest.com/pin/...` or `pin.it/...`) or direct image link to automatically scrape the image, generate rich AI metadata, and save to Excel.")

    col_in, col_btn = st.columns([5, 1])
    with col_in:
        url_input = st.text_input(
            "Pinterest Pin URL",
            placeholder="https://www.pinterest.com/pin/14073817581534067/ or https://pin.it/...",
            label_visibility="collapsed"
        )
    with col_btn:
        analyze_clicked = st.button("🚀 Analyze Pin", use_container_width=True, type="primary")

    # Sample Pins for quick testing
    st.markdown("<small style='color:#94A3B8;'>Quick Samples:</small>", unsafe_allow_html=True)
    sample_col1, sample_col2, sample_col3 = st.columns(3)
    with sample_col1:
        if st.button("📌 Sample Pin 1 (Design)", use_container_width=True):
            url_input = "https://www.pinterest.com/pin/14073817581534067/"
            analyze_clicked = True
    with sample_col2:
        if st.button("📌 Sample Direct CDN Image", use_container_width=True):
            url_input = "https://i.pinimg.com/originals/7b/e8/8b/7be88baf2c69294cd294571a2ff3313a.jpg"
            analyze_clicked = True
    with sample_col3:
        force_reanalyze = st.checkbox("Force re-process if duplicate", value=False)

    if analyze_clicked and url_input:
        clean_url = url_input.strip()

        # Step 1: Duplicate Pre-Check
        dup_info = excel_mgr.check_duplicate(url=clean_url)
        if dup_info["is_duplicate"] and not force_reanalyze:
            rec = dup_info["existing_record"]
            st.warning(
                f"⚠️ **Duplicate URL Detected:** This pin has already been logged as **S.No #{rec.get('S.No')}** (Image ID: `{rec.get('Image ID')}`). Check 'Force re-process' if you wish to re-analyze.",
                icon="⚠️"
            )
            st.session_state.last_processed = rec
        else:
            status_container = st.container()
            with status_container:
                progress_bar = st.progress(10, text="1/4 📥 Retrieving high-res image from Pinterest...")
                
                # Step 2: Download Image Headlessly
                download_res = scraper.extract_and_download(clean_url, output_dir=IMAGES_DIR)

                if not download_res["success"]:
                    progress_bar.empty()
                    if download_res.get("is_login_restricted"):
                        st.error(
                            f"🔒 **Access Restricted:** {download_res['error']}\n\n"
                            f"👉 **Solution:** Download the image manually from Pinterest and use the **'Fallback Image Uploader'** tab.",
                            icon="🚫"
                        )
                    else:
                        st.error(f"❌ **Scraping Failed:** {download_res['error']}", icon="❌")
                else:
                    image_path = download_res["local_path"]
                    img_hash = download_res["image_hash"]
                    progress_bar.progress(35, text="2/4 🔍 Checking image hash deduplication...")

                    # Check image hash duplicate
                    hash_dup_info = excel_mgr.check_duplicate(image_hash=img_hash)
                    if hash_dup_info["is_duplicate"] and not force_reanalyze:
                        progress_bar.empty()
                        rec = hash_dup_info["existing_record"]
                        st.warning(
                            f"⚠️ **Duplicate Image Content Detected:** An identical image already exists under **S.No #{rec.get('S.No')}** (Image ID: `{rec.get('Image ID')}`).",
                            icon="⚠️"
                        )
                        st.session_state.last_processed = rec
                    else:
                        progress_bar.progress(60, text="3/4 🧠 Groq Vision AI analyzing decor, florals, and ambience...")
                        
                        # Step 3: Groq Vision AI Analysis
                        active_key = os.getenv("GROQ_API_KEY", api_key_input).strip()
                        analyzer = VisionAnalyzer(api_key=active_key, model=selected_model)
                        
                        analysis_res = analyzer.analyze_image(
                            image_path=image_path,
                            context_hint=download_res.get("title_hint", "")
                        )

                        if not analysis_res["success"]:
                            progress_bar.empty()
                            st.error(
                                f"❌ **Vision Analysis Error:** {analysis_res['error']}\n\n"
                                f"Make sure a valid Groq API Key is set in the sidebar.",
                                icon="🚨"
                            )
                        else:
                            progress_bar.progress(85, text="4/4 📑 Writing to EventDhara_Metadata.xlsx...")
                            meta = analysis_res["metadata"]

                            # Step 4: Build Record & Save to Excel
                            record = {
                                "Image Name": download_res["filename"],
                                "Title": meta.get("title", ""),
                                "Event Category": meta.get("event_category", ""),
                                "Event Theme": meta.get("event_theme", ""),
                                "Short Description": meta.get("short_description", ""),
                                "Long Description": meta.get("long_description", ""),
                                "Image Inclusions": meta.get("image_inclusions", ""),
                                "Keywords and Search Tags": meta.get("keywords", ""),
                                "Color Palette": meta.get("color_palette", ""),
                                "Setting / Venue": meta.get("setting_venue", ""),
                                "Lighting / Ambience": meta.get("lighting_ambience", ""),
                                "Original Pinterest URL": clean_url,
                                "Local Image Path": f"images/{download_res['filename']}",
                                "Image Hash (MD5)": img_hash,
                                "Analyzed At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }

                            save_res = excel_mgr.append_record(record, force=force_reanalyze)
                            progress_bar.progress(100, text="✨ Analysis complete and saved to Excel!")
                            time.sleep(0.5)
                            progress_bar.empty()

                            if save_res["success"]:
                                record["S.No"] = save_res["sno"]
                                record["Image ID"] = save_res["image_id"]
                                st.session_state.last_processed = record
                                st.session_state.chat_history.insert(0, record)
                                st.success(f"🎉 **{save_res['message']}**", icon="✅")
                            else:
                                st.warning(f"⚠️ {save_res['message']}", icon="⚠️")

    # Display Side-by-Side Results
    if st.session_state.last_processed:
        item = st.session_state.last_processed
        st.divider()
        st.markdown(f"### 📋 **Analysis Result: {item.get('Title', 'Event Decor')}**")

        col_img, col_data = st.columns([1, 1.25], gap="large")

        with col_img:
            st.markdown("#### 🖼️ **Image Preview**")
            local_rel_path = item.get("Local Image Path", "")
            full_img_path = BASE_DIR / local_rel_path if local_rel_path else None
            
            if full_img_path and full_img_path.exists():
                st.image(str(full_img_path), use_container_width=True)
                with open(full_img_path, "rb") as f:
                    img_data = f.read()
                st.download_button(
                    label="💾 Download Image",
                    data=img_data,
                    file_name=Path(local_rel_path).name,
                    mime="image/jpeg",
                    use_container_width=True
                )
            else:
                st.info("Image file path: " + str(local_rel_path))

            # Image Quick Specs
            st.markdown(f"""
            <div style="background:#1E293B; border:1px solid #334155; padding:12px; border-radius:8px; margin-top:10px;">
                <p style="margin:0; font-size:0.85rem; color:#94A3B8;"><b>Image ID:</b> <code style="color:#F59E0B;">{item.get('Image ID', 'N/A')}</code></p>
                <p style="margin:4px 0 0 0; font-size:0.85rem; color:#94A3B8;"><b>Serial No:</b> #{item.get('S.No', 'N/A')}</p>
                <p style="margin:4px 0 0 0; font-size:0.85rem; color:#94A3B8;"><b>MD5 Hash:</b> <code style="font-size:0.75rem;">{item.get('Image Hash (MD5)', 'N/A')[:16]}...</code></p>
                <p style="margin:4px 0 0 0; font-size:0.85rem; color:#94A3B8;"><b>Processed:</b> {item.get('Analyzed At', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)

        with col_data:
            st.markdown("#### 📊 **AI Generated Metadata**")

            # Category & Theme Badges
            st.markdown(f"""
            <div style="margin-bottom:12px;">
                <span class="status-badge badge-success">📂 {item.get('Event Category', 'Uncategorized')}</span>
                <span class="status-badge badge-info">🎨 Theme: {item.get('Event Theme', 'Classic')}</span>
                <span class="status-badge badge-warn">📍 {item.get('Setting / Venue', 'Venue')}</span>
            </div>
            """, unsafe_allow_html=True)

            # Metadata Table View
            table_data = {
                "Property": [
                    "Title",
                    "Event Category",
                    "Event Theme",
                    "Color Palette",
                    "Setting / Venue",
                    "Lighting / Ambience",
                    "Short Description",
                    "Long Description",
                    "Original URL",
                    "Local Path"
                ],
                "Value": [
                    item.get("Title", ""),
                    item.get("Event Category", ""),
                    item.get("Event Theme", ""),
                    item.get("Color Palette", ""),
                    item.get("Setting / Venue", ""),
                    item.get("Lighting / Ambience", ""),
                    item.get("Short Description", ""),
                    item.get("Long Description", ""),
                    item.get("Original Pinterest URL", ""),
                    item.get("Local Image Path", "")
                ]
            }
            st.table(pd.DataFrame(table_data))

            # Inclusions Pills
            st.markdown("##### 🔍 **Image Inclusions (Visible Elements):**")
            inclusions_text = item.get("Image Inclusions", "")
            if inclusions_text:
                inclusions_list = [inc.strip() for inc in inclusions_text.split(",") if inc.strip()]
                tags_html = "".join([f'<span class="inclusion-tag">✓ {inc}</span>' for inc in inclusions_list])
                st.markdown(tags_html, unsafe_allow_html=True)

            # Keywords Tags
            st.markdown("<div style='margin-top:14px;'>", unsafe_allow_html=True)
            st.markdown("##### 🏷️ **Keywords & Search Tags:**")
            keywords_text = item.get("Keywords and Search Tags", "")
            if keywords_text:
                keywords_list = [k.strip() for k in keywords_text.split(",") if k.strip()]
                kw_html = "".join([f'<span class="keyword-tag">#{k}</span>' for k in keywords_list])
                st.markdown(kw_html, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # Chat Transcript / Recents
    if len(st.session_state.chat_history) > 1:
        with st.expander(f"📜 Previous Analyses in Session ({len(st.session_state.chat_history) - 1})"):
            for prev in st.session_state.chat_history[1:]:
                st.markdown(f"**#{prev.get('S.No')}** - **{prev.get('Title')}** ({prev.get('Event Category')}) — `{prev.get('Image ID')}`")


# -------------------------------------------------------------
# TAB 2: BATCH URL PROCESSOR
# -------------------------------------------------------------
with tab_batch:
    st.markdown("### ⚡ **Batch Pinterest URL Processor**")
    st.markdown("Process multiple Pinterest links simultaneously. The pipeline continues uninterrupted even if individual links fail.")

    batch_input = st.text_area(
        "Enter Pinterest URLs (one per line):",
        placeholder="https://www.pinterest.com/pin/14073817581534067/\nhttps://pin.it/...\nhttps://i.pinimg.com/...",
        height=140
    )

    batch_cols = st.columns([3, 1, 1])
    with batch_cols[0]:
        skip_duplicates = st.checkbox("Automatically skip previously logged duplicate URLs", value=True)
    with batch_cols[2]:
        start_batch_btn = st.button("🚀 Process Batch URLs", type="primary", use_container_width=True)

    if start_batch_btn and batch_input:
        raw_urls = [line.strip() for line in batch_input.splitlines() if line.strip()]
        if not raw_urls:
            st.warning("Please provide at least one valid URL.")
        else:
            st.info(f"Initiating batch processing for **{len(raw_urls)}** URLs...")
            active_key = os.getenv("GROQ_API_KEY", api_key_input).strip()
            analyzer = VisionAnalyzer(api_key=active_key, model=selected_model)

            batch_progress = st.progress(0, text="Starting batch pipeline...")
            results_log = []

            for i, target_url in enumerate(raw_urls):
                step_text = f"Processing ({i+1}/{len(raw_urls)}): {target_url[:45]}..."
                batch_progress.progress(int((i / len(raw_urls)) * 100), text=step_text)

                # Check duplicate
                if skip_duplicates:
                    dup = excel_mgr.check_duplicate(url=target_url)
                    if dup["is_duplicate"]:
                        results_log.append({
                            "URL": target_url,
                            "Status": "Skipped (Duplicate)",
                            "S.No": dup["existing_record"].get("S.No"),
                            "Image ID": dup["existing_record"].get("Image ID"),
                            "Title": dup["existing_record"].get("Title", "Existing")
                        })
                        continue

                # Scrape
                down_res = scraper.extract_and_download(target_url, output_dir=IMAGES_DIR)
                if not down_res["success"]:
                    results_log.append({
                        "URL": target_url,
                        "Status": f"Failed: {down_res['error'][:40]}",
                        "S.No": "-",
                        "Image ID": "-",
                        "Title": "Scraping Failed"
                    })
                    continue

                # Vision Analysis
                vis_res = analyzer.analyze_image(
                    image_path=down_res["local_path"],
                    context_hint=down_res.get("title_hint", "")
                )
                if not vis_res["success"]:
                    results_log.append({
                        "URL": target_url,
                        "Status": f"AI Error: {vis_res['error'][:40]}",
                        "S.No": "-",
                        "Image ID": "-",
                        "Title": "Vision Failed"
                    })
                    continue

                # Save to Excel
                meta = vis_res["metadata"]
                new_rec = {
                    "Image Name": down_res["filename"],
                    "Title": meta.get("title", ""),
                    "Event Category": meta.get("event_category", ""),
                    "Event Theme": meta.get("event_theme", ""),
                    "Short Description": meta.get("short_description", ""),
                    "Long Description": meta.get("long_description", ""),
                    "Image Inclusions": meta.get("image_inclusions", ""),
                    "Keywords and Search Tags": meta.get("keywords", ""),
                    "Color Palette": meta.get("color_palette", ""),
                    "Setting / Venue": meta.get("setting_venue", ""),
                    "Lighting / Ambience": meta.get("lighting_ambience", ""),
                    "Original Pinterest URL": target_url,
                    "Local Image Path": f"images/{down_res['filename']}",
                    "Image Hash (MD5)": down_res["image_hash"],
                    "Analyzed At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                save_out = excel_mgr.append_record(new_rec)
                results_log.append({
                    "URL": target_url,
                    "Status": "Success ✅" if save_out["success"] else "Excel Warning",
                    "S.No": save_out.get("sno", "-"),
                    "Image ID": save_out.get("image_id", "-"),
                    "Title": meta.get("title", "")
                })

            batch_progress.progress(100, text="Batch processing completed!")
            st.success(f"Batch completed! Processed {len(raw_urls)} URLs.")
            st.dataframe(pd.DataFrame(results_log), use_container_width=True)


# -------------------------------------------------------------
# TAB 3: FALLBACK IMAGE UPLOADER
# -------------------------------------------------------------
with tab_upload:
    st.markdown("### 📤 **Fallback Direct Image Upload**")
    st.markdown("When a Pinterest pin is private, restricted behind authentication, or if you have local event photography, upload the file directly.")

    upload_col1, upload_col2 = st.columns([1, 1], gap="large")

    with upload_col1:
        uploaded_file = st.file_uploader(
            "Upload Event Image (JPG, PNG, WEBP)",
            type=["jpg", "jpeg", "png", "webp"],
            help="Upload an event decor image directly to bypass Pinterest scraping."
        )
        source_url_note = st.text_input(
            "Original Pinterest URL (Optional)",
            placeholder="https://pinterest.com/pin/... or leave blank",
            help="Preserves reference to the original pin if known."
        )
        title_hint_manual = st.text_input(
            "Event Notes / Title Hint (Optional)",
            placeholder="e.g. Sangeet Stage with fairy lights"
        )
        process_upload_btn = st.button("🚀 Analyze Uploaded Image", type="primary", use_container_width=True)

    with upload_col2:
        if uploaded_file:
            st.image(uploaded_file, caption="Preview of Uploaded Image", use_container_width=True)

    if process_upload_btn and uploaded_file:
        file_bytes = uploaded_file.getvalue()
        file_hash = compute_md5(file_bytes)

        # Check duplicate
        dup_chk = excel_mgr.check_duplicate(image_hash=file_hash)
        if dup_chk["is_duplicate"]:
            rec = dup_chk["existing_record"]
            st.warning(
                f"⚠️ **Duplicate Image:** This exact image has already been cataloged as **S.No #{rec.get('S.No')}** (`{rec.get('Image ID')}`).",
                icon="⚠️"
            )
        else:
            with st.spinner("Saving image and running Groq Vision AI analysis..."):
                # Save locally
                clean_name = sanitize_filename(Path(uploaded_file.name).stem, max_length=25)
                ext = Path(uploaded_file.name).suffix.lower() or ".jpg"
                filename = f"UPLOAD_{clean_name}_{file_hash[:8]}{ext}"
                local_path = IMAGES_DIR / filename
                with open(local_path, "wb") as f:
                    f.write(file_bytes)

                # Vision AI
                active_key = os.getenv("GROQ_API_KEY", api_key_input).strip()
                analyzer = VisionAnalyzer(api_key=active_key, model=selected_model)
                vis_res = analyzer.analyze_image(local_path, context_hint=title_hint_manual)

                if not vis_res["success"]:
                    st.error(f"❌ **Analysis Failed:** {vis_res['error']}")
                else:
                    meta = vis_res["metadata"]
                    rec_to_save = {
                        "Image Name": filename,
                        "Title": meta.get("title", ""),
                        "Event Category": meta.get("event_category", ""),
                        "Event Theme": meta.get("event_theme", ""),
                        "Short Description": meta.get("short_description", ""),
                        "Long Description": meta.get("long_description", ""),
                        "Image Inclusions": meta.get("image_inclusions", ""),
                        "Keywords and Search Tags": meta.get("keywords", ""),
                        "Color Palette": meta.get("color_palette", ""),
                        "Setting / Venue": meta.get("setting_venue", ""),
                        "Lighting / Ambience": meta.get("lighting_ambience", ""),
                        "Original Pinterest URL": source_url_note.strip() if source_url_note.strip() else "Manual Upload",
                        "Local Image Path": f"images/{filename}",
                        "Image Hash (MD5)": file_hash,
                        "Analyzed At": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    save_res = excel_mgr.append_record(rec_to_save)
                    if save_res["success"]:
                        rec_to_save["S.No"] = save_res["sno"]
                        rec_to_save["Image ID"] = save_res["image_id"]
                        st.session_state.last_processed = rec_to_save
                        st.success(f"🎉 **{save_res['message']}**", icon="✅")
                        st.rerun()


# -------------------------------------------------------------
# TAB 4: MASTER EXCEL CATALOG & VIEWER
# -------------------------------------------------------------
with tab_catalog:
    st.markdown("### 📊 **EventDhara Master Catalog Explorer**")
    st.caption(f"Synchronized with `{EXCEL_FILE_PATH}`")

    df_catalog = excel_mgr.get_as_dataframe()

    if df_catalog.empty:
        st.info("The catalog is currently empty. Process your first Pinterest URL in the 'AI Pin Chatbot' tab to generate records!")
    else:
        # High-level Metrics
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val">{len(df_catalog)}</div>
                <div class="metric-lbl">Total Images Logged</div>
            </div>
            """, unsafe_allow_html=True)
        with m2:
            unique_cats = df_catalog["Event Category"].nunique() if "Event Category" in df_catalog else 0
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val">{unique_cats}</div>
                <div class="metric-lbl">Event Categories</div>
            </div>
            """, unsafe_allow_html=True)
        with m3:
            unique_themes = df_catalog["Event Theme"].nunique() if "Event Theme" in df_catalog else 0
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val">{unique_themes}</div>
                <div class="metric-lbl">Decor Themes</div>
            </div>
            """, unsafe_allow_html=True)
        with m4:
            excel_size = EXCEL_FILE_PATH.stat().st_size if EXCEL_FILE_PATH.exists() else 0
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val">{format_file_size(excel_size)}</div>
                <div class="metric-lbl">Excel File Size</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Filters
        f_col1, f_col2, f_col3 = st.columns([2, 2, 3])
        with f_col1:
            cats = ["All Categories"] + sorted([str(c) for c in df_catalog["Event Category"].dropna().unique()])
            sel_cat = st.selectbox("Filter Category", options=cats)
        with f_col2:
            themes = ["All Themes"] + sorted([str(t) for t in df_catalog["Event Theme"].dropna().unique()])
            sel_theme = st.selectbox("Filter Theme", options=themes)
        with f_col3:
            search_query = st.text_input("Search Title, Inclusions, or Keywords", placeholder="e.g. Mandap, Floral, Fairy lights...")

        filtered_df = df_catalog.copy()
        if sel_cat != "All Categories":
            filtered_df = filtered_df[filtered_df["Event Category"] == sel_cat]
        if sel_theme != "All Themes":
            filtered_df = filtered_df[filtered_df["Event Theme"] == sel_theme]
        if search_query:
            query = search_query.lower()
            mask = (
                filtered_df["Title"].astype(str).str.lower().str.contains(query) |
                filtered_df["Image Inclusions"].astype(str).str.lower().str.contains(query) |
                filtered_df["Keywords and Search Tags"].astype(str).str.lower().str.contains(query) |
                filtered_df["Short Description"].astype(str).str.lower().str.contains(query)
            )
            filtered_df = filtered_df[mask]

        st.dataframe(filtered_df, use_container_width=True, height=380)

        # Download & Action Row
        c_down, c_refresh = st.columns([3, 1])
        with c_down:
            if EXCEL_FILE_PATH.exists():
                with open(EXCEL_FILE_PATH, "rb") as f:
                    xl_data = f.read()
                st.download_button(
                    label="📥 Download Updated EventDhara_Metadata.xlsx",
                    data=xl_data,
                    file_name="EventDhara_Metadata.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    use_container_width=True
                )
        with c_refresh:
            if st.button("🔄 Refresh Catalog", use_container_width=True):
                st.rerun()

st.markdown("<br><hr>", unsafe_allow_html=True)
st.caption("EventDhara AI Image Metadata Studio • Built with Python, Streamlit, Groq Vision API & OpenPyXL")
