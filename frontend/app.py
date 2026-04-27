import streamlit as st
import requests
import json
import os
from pathlib import Path

# ── Page config ──────────────────────────────────────────
st.set_page_config(
    page_title="RxScan AI",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ───────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        text-align: center;
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .medicine-card {
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 1rem;
        border-radius: 0 10px 10px 0;
        margin: 0.5rem 0;
    }
    .warning-box {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 0 10px 10px 0;
        margin: 0.5rem 0;
    }
    .success-box {
        background: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 0 10px 10px 0;
    }
    .fda-box {
        background: #e8f4f8;
        border-left: 4px solid #17a2b8;
        padding: 1rem;
        border-radius: 0 10px 10px 0;
        margin: 0.5rem 0;
    }
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem;
        border-radius: 10px;
        font-size: 1.1rem;
        font-weight: 600;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

# ── Backend URL ──────────────────────────────────────────
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")


def call_extract_api(uploaded_file) -> dict:
    """Sends file to FastAPI backend and returns response"""
    try:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        response = requests.post(f"{BACKEND_URL}/extract", files=files, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Cannot connect to backend. Make sure FastAPI server is running."}
    except requests.exceptions.Timeout:
        return {"error": "Request timed out. Please try again."}
    except Exception as e:
        return {"error": f"Something went wrong: {str(e)}"}


def display_prescription_info(prescription: dict):
    """Renders patient and doctor info section"""
    st.subheader("📋 Prescription Details")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**👨‍⚕️ Doctor Information**")
        st.write(f"Name: {prescription.get('doctor_name') or 'N/A'}")
        st.write(f"Qualification: {prescription.get('doctor_qualification') or 'N/A'}")

    with col2:
        st.markdown("**🧑 Patient Information**")
        st.write(f"Name: {prescription.get('patient_name') or 'N/A'}")
        st.write(f"Age: {prescription.get('patient_age') or 'N/A'}")
        st.write(f"Gender: {prescription.get('patient_gender') or 'N/A'}")
        st.write(f"Date: {prescription.get('date') or 'N/A'}")

    if prescription.get("additional_notes"):
        st.markdown("**📝 Additional Notes**")
        st.info(prescription["additional_notes"])


def display_medicine_card(index: int, item: dict):
    """Renders one medicine card with prescription + FDA info"""
    rx = item.get("prescription_info", {})
    fda = item.get("fda_info", {})

    medicine_name = rx.get("name", "Unknown").title()

    with st.expander(f"💊 {index}. {medicine_name}", expanded=True):

        # Prescription info
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Dosage", rx.get("dosage") or "N/A")
        col2.metric("Frequency", rx.get("frequency") or "N/A")
        col3.metric("Duration", rx.get("duration") or "N/A")
        col4.metric("Instructions", rx.get("instructions") or "N/A")

        st.divider()

        # FDA info
        if fda.get("found"):
            st.markdown("**🏛️ FDA Drug Information**")

            fda_col1, fda_col2 = st.columns(2)

            with fda_col1:
                if fda.get("brand_names"):
                    st.markdown(f"**Brand Names:** {', '.join(fda['brand_names'])}")
                if fda.get("generic_names"):
                    st.markdown(f"**Generic Name:** {', '.join(fda['generic_names'])}")
                if fda.get("manufacturer"):
                    st.markdown(f"**Manufacturer:** {fda['manufacturer']}")
                if fda.get("purpose"):
                    st.markdown(f"**Purpose:** {fda['purpose']}")

            with fda_col2:
                if fda.get("storage"):
                    st.markdown(f"**Storage:** {fda['storage']}")
                if fda.get("dosage_info"):
                    st.markdown(f"**Dosage Info:** {fda['dosage_info'][:200]}...")

            # Warnings — highlighted
            if fda.get("warnings"):
                st.markdown("**⚠️ Warnings**")
                st.warning(fda["warnings"][:400] + "...")

            # Side effects
            if fda.get("side_effects"):
                st.markdown("**🔴 Side Effects**")
                st.error(fda["side_effects"][:400] + "...")

            # Drug interactions
            if fda.get("interactions"):
                st.markdown("**⚡ Drug Interactions**")
                st.warning(fda["interactions"][:400] + "...")

            # Contraindications
            if fda.get("contraindications"):
                st.markdown("**🚫 Contraindications**")
                st.error(fda["contraindications"][:400] + "...")

        else:
            st.info(f"ℹ️ {fda.get('message', 'Drug information not available')}")


def display_raw_text(raw_text: str):
    """Shows extracted OCR text"""
    with st.expander("🔍 View Extracted Raw Text (OCR Output)"):
        st.code(raw_text, language="text")


def display_json_output(data: dict):
    """Shows full JSON response"""
    with st.expander("📦 View Full JSON Response"):
        st.json(data)


def generate_download_json(data: dict) -> str:
    """Prepares JSON string for download"""
    return json.dumps(data, indent=2)


# ── Main App ─────────────────────────────────────────────
def main():

    # Header
    st.markdown('<div class="main-header">💊 RxScan AI</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Upload a prescription → Extract medicines → Get FDA drug info instantly</div>',
        unsafe_allow_html=True
    )

    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/medical-doctor.png", width=80)
        st.title("RxScan AI")
        st.markdown("---")
        st.markdown("### How it works")
        st.markdown("1. 📸 Upload prescription image or PDF")
        st.markdown("2. 🔍 OCR extracts the text")
        st.markdown("3. 🧠 AI parses medicines")
        st.markdown("4. 🏛️ FDA database lookup")
        st.markdown("5. 📊 Get structured results")
        st.markdown("---")
        st.markdown("### Supported Formats")
        st.markdown("JPG, JPEG, PNG, BMP, TIFF, PDF")
        st.markdown("Max size: 10MB")
    # Upload section
    st.markdown("### 📤 Upload Prescription")

    uploaded_file = st.file_uploader(
        "Choose a prescription image or PDF",
        type=["jpg", "jpeg", "png", "bmp", "tiff", "pdf"],
        help="Upload a clear photo or scan of the prescription"
    )

    if uploaded_file:
        col1, col2 = st.columns([1, 1])

        with col1:
            st.markdown("**Preview:**")
            if uploaded_file.type.startswith("image"):
                st.image(uploaded_file, use_column_width=True)
            else:
                st.info("PDF uploaded — preview not available")

        with col2:
            st.markdown("**File Info:**")
            file_size = len(uploaded_file.getvalue()) / 1024
            st.write(f"📄 Name: {uploaded_file.name}")
            st.write(f"📦 Size: {file_size:.1f} KB")
            st.write(f"🗂️ Type: {uploaded_file.type}")
            st.markdown("---")
            extract_button = st.button("🔬 Extract Prescription Data")

        if extract_button:
            with st.spinner("Processing prescription... This may take 15-20 seconds..."):

                # Progress steps
                progress = st.progress(0)
                status = st.empty()

                status.text("🖼️ Running OCR on image...")
                progress.progress(25)

                result = call_extract_api(uploaded_file)

                progress.progress(75)
                status.text("🧠 Parsing with AI...")
                progress.progress(90)
                status.text("🏛️ Looking up FDA database...")
                progress.progress(100)
                status.empty()
                progress.empty()

            # Handle errors
            if "error" in result:
                st.error(f"❌ {result['error']}")
                return

            # Success
            st.success(f"✅ Successfully extracted {result.get('total_medicines', 0)} medicines!")
            st.markdown("---")

            # Metrics row
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Medicines", result.get("total_medicines", 0))
            col2.metric("Patient", result.get("prescription", {}).get("patient_name") or "N/A")
            col3.metric("Doctor", result.get("prescription", {}).get("doctor_name") or "N/A")
            col4.metric("Date", result.get("prescription", {}).get("date") or "N/A")

            st.markdown("---")

            # Prescription details
            display_prescription_info(result.get("prescription", {}))
            st.markdown("---")

            # Medicines
            st.subheader("💊 Medicines Found")
            for i, medicine in enumerate(result.get("medicines", []), 1):
                display_medicine_card(i, medicine)

            st.markdown("---")

            # Raw text + JSON
            display_raw_text(result.get("raw_text", ""))
            display_json_output(result)

            # Download button
            st.download_button(
                label="⬇️ Download Full Report (JSON)",
                data=generate_download_json(result),
                file_name=f"rxscan_{uploaded_file.name}.json",
                mime="application/json"
            )


if __name__ == "__main__":
    main()