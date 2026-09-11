import os
import base64
import streamlit as st
import requests
from PIL import Image
import io

# Background image path: potato/farmer3.avif
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG_IMAGE_PATH = os.path.join(BASE_DIR, "farmer3.avif")

# Load image as data URL
with open(BG_IMAGE_PATH, "rb") as f:
    bg_bytes = f.read()
bg_base64 = base64.b64encode(bg_bytes).decode()
bg_data_url = f"url('data:image/avif;base64,{bg_base64}')"

# Custom CSS for full-page background and text colors
st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: {bg_data_url};
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
        min-height: 100vh;
        color: #ffffff;
    }}

    .stApp h1 {{
        color: #0b2f1a !important;
    }}

    .desc-box {{
        background: rgba(255, 255, 255, 0.75);
        color: #0b2f1a;
        padding: 10px 14px;
        border-radius: 10px;
        display: inline-block;
        max-width: 100%;
        margin-bottom: 10px;
    }}

    .stApp label {{
        color: #0b2f1a !important;
    }}

    .stApp p,
    .stApp .stMarkdown,
    .stApp .stTooltipIcon,
    .stApp .st-ae,
    .stApp .st-af,
    .stApp .stButton,
    .stApp .stSelectbox,
    .stApp .stNumberInput,
    .stApp .stTextInput,
    .stApp .stFileUploader {{
        color: #ffffff !important;
    }}

    .stApp a {{
        color: #ffffff !important;
    }}

    .stApp::before {{
        content: "";
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.25);
        z-index: -1;
    }}

    .stCard, .st-ae, .st-af {{
        background-color: rgba(0, 0, 0, 0.55) !important;
    }}

    /* Hide top bar and GitHub button completely */
    header {{
        display: none !important;
    }}
    .stApp [data-testid="stToolbar"] {{
        display: none !important;
    }}
    .stApp [data-testid="stTopBar"] {{
        display: none !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# Read backend URL from environment variable, falling back to localhost:8000 when running locally
raw_backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
BACKEND_URL = raw_backend_url.strip().rstrip("/")

PING_URL = f"{BACKEND_URL}/ping"
PREDICT_URL = f"{BACKEND_URL}/predict"

# Set page configuration
st.set_page_config(
    page_title="Potato Disease Classification",
    page_icon="🥔",
    layout="centered"
)

# App Title & Description
st.title("🥔 Potato Leaf Disease Classifier")

st.markdown(
    """
    <div class="desc-box">
    Upload a picture of a potato leaf to detect whether it is Healthy, 
    or affected by Early Blight or Late Blight.
    </div>
    """,
    unsafe_allow_html=True
)

# Friendly label mapping for display
CLASS_DISPLAY_NAMES = {
    "Potato___Early_blight": "Early Blight",
    "Potato___Late_blight": "Late Blight",
    "Potato___healthy": "Healthy"
}

# Sidebar Info
with st.sidebar:
    st.header("About the Model")
    st.markdown(
        """
        - **Model Type**: Deep CNN (TensorFlow SavedModel)
        - **Target Classes**:
          - 🌿 Healthy
          - 🍂 Early Blight
          - 🥀 Late Blight
        - **Backend**: FastAPI
        - **Frontend**: Streamlit
        """
    )
    st.markdown("---")
    backend_status_placeholder = st.empty()
    try:
        ping_res = requests.get(PING_URL, timeout=2)
        if ping_res.status_code == 200:
            backend_status_placeholder.success(f"Backend: Connected ({BACKEND_URL})")
        else:
            backend_status_placeholder.warning("Backend: Unhealthy")
    except Exception:
        backend_status_placeholder.error("Backend: Not reachable")

# File Uploader
uploaded_file = st.file_uploader(
    "Choose a potato leaf image...",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
    try:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Potato Leaf", use_container_width=True)

        # Trigger prediction
        if st.button("Classify Leaf", type="primary"):
            with st.spinner("Analyzing image..."):
                try:
                    # Prepare file payload
                    file_bytes = uploaded_file.getvalue()
                    mime_type = uploaded_file.type or "image/jpeg"
                    files = {"file": (uploaded_file.name, file_bytes, mime_type)}

                    response = requests.post(PREDICT_URL, files=files, timeout=15)

                    if response.status_code == 200:
                        data = response.json()
                        pred_class = data.get("class", "Unknown")
                        confidence = data.get("confidence", 0.0)
                        name = data.get("name", CLASS_DISPLAY_NAMES.get(pred_class, pred_class))
                        symptoms = data.get("symptoms", [])
                        advisory = data.get("advisory", [])
                        all_preds = data.get("all_predictions", {})

                        display_name = name if name else CLASS_DISPLAY_NAMES.get(pred_class, pred_class)

                        st.subheader("Classification Result")
                        if pred_class == "Potato___healthy":
                            st.success(f"### Result: **{display_name}** ({confidence}%)")
                        else:
                            st.warning(f"### Result: **{display_name}** ({confidence}%)")

                        if symptoms:
                            st.markdown("#### Symptoms")
                            for s in symptoms:
                                st.write(f"- {s}")

                        if advisory:
                            st.markdown("#### Advisory")
                            for a in advisory:
                                st.write(f"- {a}")

                        st.markdown("#### Confidence Breakdown")
                        for cls_key, prob in all_preds.items():
                            c_name = CLASS_DISPLAY_NAMES.get(cls_key, cls_key)
                            st.write(f"**{c_name}**: {prob}%")
                            st.progress(min(max(prob / 100.0, 0.0), 1.0))

                    else:
                        st.error(f"Error from API ({response.status_code}): {response.text}")

                except requests.exceptions.ConnectionError:
                    st.error(
                        "Unable to connect to the FastAPI backend. "
                        f"Please verify that the backend is running at `{BACKEND_URL}`."
                    )
                except Exception as ex:
                    st.error(f"An unexpected error occurred: {ex}")

    except Exception as e:
        st.error(f"Invalid image file: {e}")
else:
    st.info("Please upload an image of a potato leaf to begin.")