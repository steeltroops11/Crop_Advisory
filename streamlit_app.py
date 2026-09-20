import streamlit as st
import os
import sys
from pathlib import Path

# Add the project root to sys.path so we can import src modules
ROOT_DIR = Path(__file__).resolve().parent
sys.path.append(str(ROOT_DIR))

from src.rag_chain import CropAdvisoryRAGChain
from src.config import GEMINI_API_KEY

# Page configuration
st.set_page_config(
    page_title="Kisan Mitra - AI Crop Advisory",
    page_icon="🌾",
    layout="centered"
)

st.title("🌾 Kisan Mitra")
st.caption("AI Crop Advisory for Small Farmers in Punjab")

# Initialize the RAG chain once and cache it
@st.cache_resource
def get_rag_chain():
    """Initialize and return the RAG chain, handling missing API key."""
    if not GEMINI_API_KEY:
        st.error("⚠️ GEMINI_API_KEY is not set. Please configure it in Streamlit Cloud secrets.")
        st.stop()
    try:
        return CropAdvisoryRAGChain()
    except Exception as e:
        st.error(f"⚠️ Failed to initialize the advisory chain: {e}")
        st.stop()

# Input form
with st.form("advisory_form"):
    query = st.text_input(
        "Enter your question (Hindi/English/Punjabi):",
        placeholder="PR 126 lagayi hai 25 din ho gaye, urea kab aur kitna daalu?"
    )

    col1, col2 = st.columns(2)
    with col1:
        crop = st.selectbox(
            "Crop (optional):",
            ["auto", "paddy", "wheat"],
            format_func=lambda x: {"auto": "Auto-detect", "paddy": "Paddy (धान)", "wheat": "Wheat (गेहूं)"}[x],
            index=0
        )
    with col2:
        language = st.selectbox(
            "Response language:",
            ["auto", "hindi", "english", "punjabi"],
            format_func=lambda x: {
                "auto": "Auto-detect",
                "hindi": "Hindi (हिन्दी)",
                "english": "English",
                "punjabi": "Punjabi (ਪੰਜਾਬੀ)"
            }[x],
            index=0
        )

    district = st.text_input(
        "District (optional):",
        placeholder="Ludhiana",
        help="Leave blank for auto-detection from query"
    )

    use_weather = st.checkbox("Use real-time weather gates", value=True)

    submitted = st.form_submit_button("Get Advisory", type="primary")

# Process form submission
if submitted and query.strip():
    # Get the RAG chain (cached)
    chain = get_rag_chain()
    if chain is None:
        # Error already shown in get_rag_chain
        st.stop()

    # Prepare parameters
    crop_param = None if crop == "auto" else crop
    language_param = None if language == "auto" else language
    district_param = None if not district.strip() else district.strip()

    # Show loading spinner
    with st.spinner("Fetching advisory from Kisan Mitra..."):
        try:
            # Query the RAG chain
            response = chain.query(
                farmer_query=query.strip(),
                crop_hint=crop_param,
                language=language_param,
                district=district_param,
                use_weather=use_weather
            )

            if response:
                st.success("✅ Advisory received")

                # Display answer
                st.markdown("### 📋 Advisory")
                st.write(response.answer)

                # Show metadata in expandable section
                with st.expander("📊 Details"):
                    st.json({
                        "detected_crop": response.detected_crop,
                        "language_used": response.language_used,
                        "confidence": response.confidence,
                        "sources": response.sources
                    })
            else:
                st.error("❌ Failed to generate advisory")

        except Exception as e:
            st.error(f"❌ Error while generating advisory: {e}")
            st.info("Make sure the required API keys and services are accessible.")
