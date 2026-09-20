import streamlit as st
import requests
import json

# ⚠️ UPDATE THIS AFTER DEPLOYING TO RENDER.COM
BACKEND_URL = "https://kisan-mitra-api.onrender.com"  # <-- REPLACE WITH YOUR RENDER URL

st.set_page_config(
    page_title="Kisan Mitra - AI Crop Advisory",
    page_icon="🌾",
    layout="centered"
)

st.title("🌾 Kisan Mitra")
st.caption("AI Crop Advisory for Small Farmers in Punjab")

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
            format_func=lambda x: {"auto": "Auto-detect", "paddy": "Paddy (धान)", "wheat": "Wheat (गेहूं)}"[x],
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

if submitted and query.strip():
    # Prepare request
    payload = {
        "query": query.strip(),
        "crop": None if crop == "auto" else crop,
        "language": None if language == "auto" else language,
        "district": None if not district.strip() else district.strip(),
        "use_weather": use_weather
    }

    # Show loading spinner
    with st.spinner("Fetching advisory from Kisan Mitra..."):
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/v1/advisory",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    st.success("✅ Advisory received")

                    # Display answer
                    st.markdown("### 📋 Advisory")
                    st.write(data["answer"])

                    # Show metadata in expandable section
                    with st.expander("📊 Details"):
                        st.json({
                            "detected_crop": data.get("detected_crop"),
                            "language_used": data.get("language_used"),
                            "confidence": data.get("confidence"),
                            "sources": data.get("sources")
                        })
                else:
                    st.error("❌ Service returned an error")
            else:
                st.error(f"❌ Request failed: {response.status_code} - {response.text}")

        except requests.exceptions.RequestException as e:
            st.error(f"❌ Connection error: {str(e)}")
            st.info("Make sure the backend service is running and accessible.")
