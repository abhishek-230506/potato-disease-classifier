import os
import streamlit as st
import requests
from PIL import Image
import io


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

# Language selection
language = st.sidebar.selectbox(
    "Language / भाषा",
    ["English", "हिंदी"],
    key="language"
)

translations = {
    "English": {
        "title": "🥔 Potato Leaf Disease Classifier",
        "description": "Upload a picture of a potato leaf to detect whether it is Healthy, Early Blight, or Late Blight.",
        "upload": "Choose a potato leaf image...",
        "classify": "Classify Leaf",
        "result": "Classification Result",
        "symptoms": "Symptoms",
        "advisory": "Advisory",
        "confidence": "Confidence Breakdown",
        "uploaded": "Uploaded Potato Leaf",
        "invalid": "Invalid image file"
    },
    "हिंदी": {
        "title": "🥔 आलू की पत्ती रोग पहचानकर्ता",
        "description": "आलू की पत्ती की तस्वीर अपलोड करके रोग की पहचान करें।",
        "upload": "आलू की पत्ती की तस्वीर चुनें...",
        "classify": "पत्ती की जांच करें",
        "result": "जांच का परिणाम",
        "symptoms": "लक्षण",
        "advisory": "सलाह",
        "confidence": "विश्वास स्तर",
        "uploaded": "अपलोड की गई आलू की पत्ती",
        "invalid": "गलत छवि फ़ाइल"
    }
}

t = translations[language]

# App Title & Description
st.title(t["title"])
st.markdown(
    """
    Upload a picture of a potato leaf to detect whether it is **Healthy**, 
    or affected by **Early Blight** or **Late Blight**.
    """
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
    t["upload"],
    type=["jpg", "jpeg", "png"]
)


if uploaded_file is not None:
    try:
        image = Image.open(uploaded_file)
        st.image(image, caption=t["uploaded"], use_container_width=True)


        # Trigger prediction
        if st.button(t["classify"], type="primary"):
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


                        st.subheader(t["result"])
                        if pred_class == "Potato___healthy":
                            st.success(f"### Result: **{display_name}** ({confidence}%)")
                        else:
                            st.warning(f"### Result: **{display_name}** ({confidence}%)")


                        if symptoms:
                            st.markdown(f"#### {t['symptoms']}")
                            for s in symptoms:
                                st.write(f"- {s}")


                        if advisory:
                            st.markdown(f"#### {t['advisory']}")
                            for a in advisory:
                                st.write(f"- {a}")


                        st.markdown(f"#### {t['confidence']}")
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