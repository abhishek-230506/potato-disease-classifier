import os
import html
import base64
import textwrap
import streamlit as st
import requests
from PIL import Image


# This must be the first Streamlit command
st.set_page_config(
    page_title="Potato Disease Classification",
    page_icon="🥔",
    layout="centered",
    initial_sidebar_state="expanded"
)


# ---------------------------------------------------------------------------
# Background image
# ---------------------------------------------------------------------------
# FIX: the original code assumed a fixed folder depth
# (dirname(dirname(__file__))). If the script ever lives one level shallower
# or deeper than expected, the image silently fails to load with no warning.
# We now try a few sensible candidate locations and use the first one that
# actually exists.
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_CANDIDATE_BG_PATHS = [
    os.path.join(_SCRIPT_DIR, "farmer3.avif"),
    os.path.join(os.path.dirname(_SCRIPT_DIR), "farmer3.avif"),
    os.path.join(os.path.dirname(os.path.dirname(_SCRIPT_DIR)), "farmer3.avif"),
]

bg_data_url = None
for _path in _CANDIDATE_BG_PATHS:
    try:
        with open(_path, "rb") as f:
            bg_bytes = f.read()
        bg_base64 = base64.b64encode(bg_bytes).decode()
        bg_data_url = f"url('data:image/avif;base64,{bg_base64}')"
        break
    except (FileNotFoundError, OSError):
        continue


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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def to_percent(value):
    """
    FIX: the original template assumed `confidence` / values inside
    `all_predictions` were always already on a 0-100 scale. Many models
    return probabilities on a 0-1 scale instead, which used to render as
    e.g. "0.95%" and draw an invisible confidence bar. This normalizes
    either convention to a clean 0-100 percentage, and never crashes on
    bad/missing data.
    """
    try:
        val = float(value)
    except (TypeError, ValueError):
        return 0.0
    if 0 <= val <= 1:
        val *= 100
    return max(0.0, min(val, 100.0))


def esc(value):
    """
    FIX: the original code interpolated backend-supplied strings (class
    name, symptoms, advisory text) directly into an HTML block rendered
    with unsafe_allow_html=True. If the backend ever returns text
    containing '<', '>' or '&' (e.g. an error message, or unexpected
    model output) it would break the layout or inject stray markup.
    Escaping keeps this safe no matter what the backend sends.
    """
    return html.escape(str(value))


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

    /* Main content area text (over the background image) stays dark,
       since it always sits on a light translucent card regardless of
       the active Streamlit theme. This is intentionally scoped to
       .main so it can no longer bleed into the sidebar (see below). */
    .stApp .main,
    .stApp .main p,
    .stApp .main label,
    .stApp .main .stMarkdown {{
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

    .result-info-box h3 {{
        margin-top: 20px;
        margin-bottom: 8px;
    }}

    .result-info-box h2 {{
        margin-top: 0;
        margin-bottom: 12px;
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

    .confidence-section {{
        margin-top: 18px;
    }}

    .confidence-row {{
        margin-top: 12px;
    }}

    .confidence-row:first-of-type {{
        margin-top: 8px;
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

    .stApp .main h2,
    .stApp .main h3,
    .stApp .main h4,
    .stApp .main h5,
    .stApp .main h6 {{
        color: #111111 !important;
    }}

    .stApp .main button {{
        color: #111111 !important;
    }}

    footer,
    .stApp footer,
    .stApp [data-testid="stFooter"] {{
        display: none !important;
    }}

    /* --------------------------------------------------------------
       Sidebar text color: follow the active Streamlit theme.
       FIX: previously the sidebar rules had the SAME CSS specificity
       as the blanket ".stApp p / .stApp label / .stApp .stMarkdown"
       rule above (which forced everything, including the sidebar,
       to a hardcoded dark color). Whichever rule happened to be
       declared last in the stylesheet silently won, so this was one
       accidental reorder away from breaking again, and elements like
       <span>/<li>/<h1-h6> in the sidebar were never covered at all.

       Two changes fix this for good:
       1. The blanket dark-text rule above is now scoped to `.main`
          only, so it can never touch the sidebar again.
       2. The sidebar rule below is prefixed with `.stApp` and lists
          every relevant tag explicitly, giving it strictly higher
          specificity than any other rule in this file - so it always
          wins regardless of source order, and correctly tracks
          Streamlit's `--text-color` theme variable: white text in
          dark mode, dark text in light mode. --------------------- */
    .stApp [data-testid="stSidebar"],
    .stApp [data-testid="stSidebar"] p,
    .stApp [data-testid="stSidebar"] span,
    .stApp [data-testid="stSidebar"] li,
    .stApp [data-testid="stSidebar"] label,
    .stApp [data-testid="stSidebar"] strong,
    .stApp [data-testid="stSidebar"] .stMarkdown,
    .stApp [data-testid="stSidebar"] [data-baseweb="select"] *,
    .stApp [data-testid="stSidebar"] h1,
    .stApp [data-testid="stSidebar"] h2,
    .stApp [data-testid="stSidebar"] h3,
    .stApp [data-testid="stSidebar"] h4,
    .stApp [data-testid="stSidebar"] h5,
    .stApp [data-testid="stSidebar"] h6 {{
        color: var(--text-color) !important;
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
                        # FIX: a non-JSON 200 response (e.g. a proxy
                        # returning an HTML page) used to raise an
                        # unguarded exception with a confusing message.
                        try:
                            data = response.json()
                        except ValueError:
                            st.error(
                                "The backend returned a response that "
                                "wasn't valid JSON. Please check the "
                                "/predict endpoint."
                            )
                            data = None

                        if data is not None:
                            pred_class = data.get("class", "Unknown")
                            confidence = to_percent(data.get("confidence", 0.0))
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

                            # Build symptoms HTML (escaped)
                            symptoms_html = ""

                            if symptoms:
                                symptoms_items = "".join(
                                    f"<li>{esc(s)}</li>" for s in symptoms
                                )
                                symptoms_html = textwrap.dedent(f"""\
                                    <h3>{esc(texts["symptoms"])}</h3>
                                    <ul>{symptoms_items}</ul>
                                """)

                            # Build advisory HTML (escaped)
                            advisory_html = ""

                            if advisory:
                                advisory_items = "".join(
                                    f"<li>{esc(a)}</li>" for a in advisory
                                )
                                advisory_html = textwrap.dedent(f"""\
                                    <h3>{esc(texts["advisory"])}</h3>
                                    <ul>{advisory_items}</ul>
                                """)

                            # Build confidence HTML (escaped, normalized to %)
                            confidence_html = ""

                            if all_preds:
                                confidence_rows = ""

                                for cls_key, prob in all_preds.items():
                                    class_name = CLASS_DISPLAY_NAMES.get(
                                        cls_key,
                                        cls_key
                                    )
                                    prob_pct = to_percent(prob)

                                    confidence_rows += textwrap.dedent(f"""\
                                        <div class="confidence-row">
                                        <div class="confidence-label"><span>{esc(class_name)}</span><span>{prob_pct:.1f}%</span></div>
                                        <div class="confidence-bar"><div class="confidence-fill" style="width: {prob_pct:.1f}%;"></div></div>
                                        </div>
                                    """)

                                confidence_html = textwrap.dedent(f"""\
                                    <h3>{esc(texts["confidence_breakdown"])}</h3>
                                """) + confidence_rows

                            # Display complete result box
                            result_box_html = textwrap.dedent(f"""\
                                <div class="result-info-box">
                                <h2>{esc(texts["classification_result"])}</h2>
                                <div class="detected-result">
                                <h3>{esc(display_name)}</h3>
                                <p><strong>{esc(texts["confidence"])}:</strong> {confidence:.1f}%</p>
                                </div>
                                {symptoms_html}
                                {advisory_html}
                                {confidence_html}
                                </div>
                            """)

                            st.markdown(result_box_html, unsafe_allow_html=True)

                    else:
                        # FIX: raw response.text could be a huge HTML
                        # error page (e.g. a 502 from a proxy) dumped
                        # straight into the UI. Truncate for safety.
                        error_detail = response.text[:500]
                        st.error(
                            f"Error from API "
                            f"({response.status_code}): "
                            f"{error_detail}"
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