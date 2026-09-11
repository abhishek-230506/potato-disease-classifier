import os
import base64
import textwrap
import streamlit as st
import requests
from PIL import Image


# This must be the first Streamlit command
st.set_page_config(
    page_title="Potato Disease Classification",
    page_icon=None,
    layout="centered",
    initial_sidebar_state="expanded"
)


# Background image path: potato/farmer3.avif
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG_IMAGE_PATH = os.path.join(BASE_DIR, "farmer3.avif")


# Load background image (gracefully handle a missing file instead of crashing)
bg_data_url = None
try:
    with open(BG_IMAGE_PATH, "rb") as f:
        bg_bytes = f.read()
    bg_base64 = base64.b64encode(bg_bytes).decode()
    bg_data_url = f"url('data:image/avif;base64,{bg_base64}')"
except (FileNotFoundError, OSError):
    bg_data_url = None


# Friendly label mapping
CLASS_DISPLAY_NAMES = {
    "Potato___Early_blight": "Early Blight",
    "Potato___Late_blight": "Late Blight",
    "Potato___healthy": "Healthy"
}


# Translations
TRANSLATIONS = {
    "English": {
        "language": "Language",
        "about_model": "About the Model",
        "description": (
            "Upload a picture of a potato leaf to detect whether it is "
            "Healthy, or affected by Early Blight or Late Blight."
        ),
        "choose_image": "Choose a potato leaf image...",
        "uploaded_image": "Uploaded Potato Leaf",
        "classify": "Classify Leaf",
        "analyzing": "Analyzing image...",
        "classification_result": "Classification Result",
        "symptoms": "Symptoms",
        "advisory": "Advisory",
        "confidence": "Confidence",
        "confidence_breakdown": "Confidence Breakdown",
        "upload_message": "Please upload an image of a potato leaf to begin."
    },
    "हिंदी": {
        "language": "भाषा",
        "about_model": "मॉडल के बारे में",
        "description": (
            "आलू के पत्ते की तस्वीर अपलोड करके जांचें कि पत्ता स्वस्थ है "
            "या अर्ली ब्लाइट या लेट ब्लाइट से प्रभावित है।"
        ),
        "choose_image": "आलू के पत्ते की तस्वीर चुनें...",
        "uploaded_image": "अपलोड किया गया आलू का पत्ता",
        "classify": "पत्ती की जांच करें",
        "analyzing": "तस्वीर का विश्लेषण हो रहा है...",
        "classification_result": "जांच का परिणाम",
        "symptoms": "लक्षण",
        "advisory": "सलाह",
        "confidence": "विश्वास",
        "confidence_breakdown": "विश्वास प्रतिशत",
        "upload_message": "शुरू करने के लिए आलू के पत्ते की तस्वीर अपलोड करें।"
    }
}


# Backend URL
raw_backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
BACKEND_URL = raw_backend_url.strip().rstrip("/")

PING_URL = f"{BACKEND_URL}/ping"
PREDICT_URL = f"{BACKEND_URL}/predict"


# Sidebar (built once)
with st.sidebar:
    selected_language = st.selectbox(
        "Language / भाषा",
        options=["English", "हिंदी"],
        index=0,
        key="language_selector"
    )

    texts = TRANSLATIONS[selected_language]

    st.header(texts["about_model"])

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
            backend_status_placeholder.success(
                f"Backend: Connected ({BACKEND_URL})"
            )
        else:
            backend_status_placeholder.warning(
                "Backend: Unhealthy"
            )

    except Exception:
        backend_status_placeholder.error(
            "Backend: Not reachable"
        )


# Custom CSS
background_css = f"""
    .stApp {{
        background-image: {bg_data_url};
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        background-repeat: no-repeat;
        min-height: 100vh;
    }}

    .stApp::before {{
        content: "";
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.25);
        z-index: -1;
    }}
""" if bg_data_url else """
    .stApp {
        min-height: 100vh;
    }
"""

st.markdown(
    f"""
    <style>
    {background_css}

    .main-title {{
        color: #0f2b1d !important;
        text-align: center !important;
        width: 100%;
        margin: 0 0 16px 0;
        font-size: 2.2rem;
        font-weight: 700;
    }}

    .desc-box {{
        display: block;
        width: 100%;
        box-sizing: border-box;
        padding: 12px 16px;
        margin-bottom: 14px;
        border-radius: 10px;
        background: rgba(255, 255, 255, 0.78);
        color: #111111 !important;
        font-size: 16px;
        line-height: 1.5;
    }}

    .desc-box p {{
        color: #111111 !important;
    }}

    .stApp,
    .stApp p,
    .stApp label,
    .stApp .stMarkdown {{
        color: #111111 !important;
    }}

    .stApp [data-testid="stFileUploader"] {{
        background: rgba(255, 255, 255, 0.78) !important;
        padding: 12px;
        border-radius: 12px;
        color: #111111 !important;
    }}

    .stApp [data-testid="stFileUploader"] label,
    .stApp [data-testid="stFileUploader"] span,
    .stApp [data-testid="stFileUploader"] small {{
        color: #111111 !important;
    }}

    .stApp [data-testid="stFileUploaderDropzone"] {{
        background: rgba(255, 255, 255, 0.65) !important;
        border: 1px solid rgba(0, 0, 0, 0.35) !important;
    }}

    .stApp [data-testid="stFileUploader"] button {{
        color: #111111 !important;
        background: rgba(255, 255, 255, 0.9) !important;
        border: 1px solid #555555 !important;
    }}

    .result-info-box {{
        width: 100%;
        box-sizing: border-box;
        padding: 18px;
        margin-top: 16px;
        border-radius: 14px;
        background: rgba(255, 255, 255, 0.84);
        color: #111111 !important;
        border: 1px solid rgba(0, 0, 0, 0.22);
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.18);
    }}

    .result-info-box h2,
    .result-info-box h3,
    .result-info-box h4,
    .result-info-box p,
    .result-info-box li,
    .result-info-box strong {{
        color: #111111 !important;
    }}

    .result-info-box ul {{
        margin-top: 4px;
        padding-left: 24px;
    }}

    .result-info-box li {{
        margin-bottom: 6px;
    }}

    .detected-result {{
        padding: 12px 14px;
        border-radius: 10px;
        background: rgba(255, 255, 255, 0.65);
        border-left: 5px solid #2e7d32;
    }}

    .confidence-row {{
        margin-top: 10px;
    }}

    .confidence-label {{
        display: flex;
        justify-content: space-between;
        color: #111111 !important;
        font-weight: 600;
        margin-bottom: 4px;
    }}

    .confidence-bar {{
        width: 100%;
        height: 8px;
        background: rgba(0, 0, 0, 0.18);
        border-radius: 5px;
        overflow: hidden;
    }}

    .confidence-fill {{
        height: 100%;
        background: #2e7d32;
        border-radius: 5px;
    }}

    .stApp h2,
    .stApp h3,
    .stApp h4,
    .stApp h5,
    .stApp h6 {{
        color: #111111 !important;
    }}

    .stApp button {{
        color: #111111 !important;
    }}

    footer,
    .stApp footer,
    .stApp [data-testid="stFooter"] {{
        display: none !important;
    }}

    /* Sidebar text: force white only in dark mode, only inside the sidebar */
    @media (prefers-color-scheme: dark) {{
        [data-testid="stSidebar"],
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] li,
        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] h4,
        [data-testid="stSidebar"] h5,
        [data-testid="stSidebar"] h6 {{
            color: #ffffff !important;
        }}
    }}
    </style>
    """,
    unsafe_allow_html=True
)


# Main title and description
st.markdown(
    """
    <h1 class="main-title">
        Potato Leaf Disease Classifier
    </h1>
    """,
    unsafe_allow_html=True
)

st.markdown(
    f"""
    <div class="desc-box">
        {texts["description"]}
    </div>
    """,
    unsafe_allow_html=True
)


# File Uploader
uploaded_file = st.file_uploader(
    texts["choose_image"],
    type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
    try:
        image = Image.open(uploaded_file)

        st.image(
            image,
            caption=texts["uploaded_image"],
            use_container_width=True
        )

        if st.button(texts["classify"], type="primary"):
            with st.spinner(texts["analyzing"]):
                try:
                    file_bytes = uploaded_file.getvalue()
                    mime_type = uploaded_file.type or "image/jpeg"
                    files = {
                        "file": (
                            uploaded_file.name,
                            file_bytes,
                            mime_type
                        )
                    }

                    response = requests.post(
                        PREDICT_URL,
                        files=files,
                        timeout=15
                    )

                    if response.status_code == 200:
                        data = response.json()

                        pred_class = data.get("class", "Unknown")
                        confidence = data.get("confidence", 0.0)
                        name = data.get(
                            "name",
                            CLASS_DISPLAY_NAMES.get(
                                pred_class,
                                pred_class
                            )
                        )
                        symptoms = data.get("symptoms", [])
                        advisory = data.get("advisory", [])
                        all_preds = data.get("all_predictions", {})

                        display_name = (
                            name
                            if name
                            else CLASS_DISPLAY_NAMES.get(
                                pred_class,
                                pred_class
                            )
                        )

                        # Build symptoms HTML
                        symptoms_html = ""

                        if symptoms:
                            symptoms_items = "".join(
                                f"<li>{s}</li>" for s in symptoms
                            )
                            symptoms_html = textwrap.dedent(f"""\
                                <h3>{texts["symptoms"]}</h3>
                                <ul>{symptoms_items}</ul>
                            """)

                        # Build advisory HTML
                        advisory_html = ""

                        if advisory:
                            advisory_items = "".join(
                                f"<li>{a}</li>" for a in advisory
                            )
                            advisory_html = textwrap.dedent(f"""\
                                <h3>{texts["advisory"]}</h3>
                                <ul>{advisory_items}</ul>
                            """)

                        # Build confidence HTML
                        confidence_html = ""

                        if all_preds:
                            confidence_rows = ""

                            for cls_key, prob in all_preds.items():
                                class_name = CLASS_DISPLAY_NAMES.get(
                                    cls_key,
                                    cls_key
                                )

                                try:
                                    prob_val = float(prob)
                                except (TypeError, ValueError):
                                    prob_val = 0.0

                                bar_width = min(max(prob_val, 0), 100)
                                confidence_rows += textwrap.dedent(f"""\
                                    <div class="confidence-row">
                                    <div class="confidence-label"><span>{class_name}</span><span>{prob}%</span></div>
                                    <div class="confidence-bar"><div class="confidence-fill" style="width: {bar_width}%;"></div></div>
                                    </div>
                                """)

                            confidence_html = textwrap.dedent(f"""\
                                <h3>{texts["confidence_breakdown"]}</h3>
                            """) + confidence_rows

                        # Display complete result box
                        result_box_html = textwrap.dedent(f"""\
                            <div class="result-info-box">
                            <h2>{texts["classification_result"]}</h2>
                            <div class="detected-result">
                            <h3>{display_name}</h3>
                            <p><strong>{texts["confidence"]}:</strong> {confidence}%</p>
                            </div>
                            {symptoms_html}
                            {advisory_html}
                            {confidence_html}
                            </div>
                        """)

                        st.markdown(result_box_html, unsafe_allow_html=True)

                    else:
                        st.error(
                            f"Error from API "
                            f"({response.status_code}): "
                            f"{response.text}"
                        )

                except requests.exceptions.ConnectionError:
                    st.error(
                        "Unable to connect to the FastAPI backend. "
                        f"Please verify that the backend is running at "
                        f"`{BACKEND_URL}`."
                    )

                except requests.exceptions.Timeout:
                    st.error(
                        "The backend took too long to respond. "
                        "Please try again."
                    )

                except Exception as ex:
                    st.error(f"An unexpected error occurred: {ex}")

    except Exception as e:
        st.error(f"Invalid image file: {e}")

else:
    st.info(texts["upload_message"])