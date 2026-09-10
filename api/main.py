import os
import io
import json
from pathlib import Path
import numpy as np
from PIL import Image
import tensorflow as tf
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn


ADVISORIES_FILE = Path(__file__).parent.parent / "advisories.json"

with ADVISORIES_FILE.open("r", encoding="utf-8") as f:
    ADVISORIES = json.load(f)


# Define classes in the exact order verified from training/training.ipynb
CLASS_NAMES = [
    "Potato___Early_blight",
    "Potato___Late_blight",
    "Potato___healthy"
]


# Path to the SavedModel
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, "saved_model", "1")


# Load model using tf.saved_model.load
try:
    imported_model = tf.saved_model.load(MODEL_DIR)
    infer = imported_model.signatures["serving_default"]
except Exception as e:
    raise RuntimeError(f"Failed to load TensorFlow SavedModel from {MODEL_DIR}: {e}")


app = FastAPI(title="Potato Disease Classification API")


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/ping")
async def ping():
    """Health check endpoint."""
    return {"status": "alive"}



@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    """
    Predict the potato leaf condition from an uploaded image.
    Follows preprocessing from the training notebook:
    - Converts image to RGB
    - Resizes to (256, 256)
    - The model handles internal Rescaling(1./255)
    """
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")


    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Could not decode the image file.")


    # Resize to 256x256 matching input dimensions
    image = image.resize((256, 256))
    img_array = np.array(image, dtype=np.float32)
    img_batch = np.expand_dims(img_array, axis=0)


    try:
        # Run inference via the SavedModel serving_default signature
        output = infer(tf.constant(img_batch))
        predictions = output["output_0"].numpy()[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {str(e)}")


    predicted_index = int(np.argmax(predictions))
    predicted_class = CLASS_NAMES[predicted_index]
    confidence = float(predictions[predicted_index])


    info = ADVISORIES.get(predicted_class, {})

    return {
        "class": predicted_class,
        "confidence": round(confidence * 100, 2),
        "name": info.get("name_en", predicted_class),
        "symptoms": info.get("symptoms_en", []),
        "advisory": info.get("advisory_en", []),
        "all_predictions": {
            CLASS_NAMES[i]: round(float(predictions[i]) * 100, 2)
            for i in range(len(CLASS_NAMES))
        }
    }



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)