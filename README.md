# Potato Leaf Disease Classifier

A web application that predicts potato leaf disease from an uploaded image.

## Classes

The TensorFlow model predicts:

- Potato___Early_blight
- Potato___Late_blight
- Potato___healthy

## Technologies

- TensorFlow
- FastAPI
- Uvicorn
- Streamlit
- Python 3.12

## Project Structure

```text
potato/
├── api/
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── app.py
│   └── requirements.txt
├── saved_model/
│   └── 1/
├── README.md
└── .gitignore
```

## Run Locally

Create and activate the Python environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install backend dependencies:

```powershell
python -m pip install -r api\requirements.txt
```

Install frontend dependencies:

```powershell
python -m pip install -r frontend\requirements.txt
```

Start the FastAPI backend:

```powershell
python -m uvicorn api.main:app --reload --port 8000
```

Start the Streamlit frontend in a second PowerShell window:

```powershell
python -m streamlit run frontend\app.py --server.port 8501
```

Open:

```text
http://localhost:8501
```

## API

- `GET /ping` checks whether the backend is running.
- `POST /predict` accepts an image and returns the predicted class and confidence.

## Deployment

### Render backend

Build command:

```text
pip install -r api/requirements.txt
```

Start command:

```text
uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

### Streamlit frontend

Deploy `frontend/app.py` through Streamlit Community Cloud.

Set this Streamlit secret or environment variable:

```toml
BACKEND_URL = "https://your-render-service.onrender.com"
```

Replace the URL with the Render backend URL after deployment.

## Notes

- Do not modify anything inside `saved_model/`.
- The model already contains resizing and rescaling layers.
- Locally, the frontend uses `http://localhost:8000`.
- In the cloud, the frontend uses the `BACKEND_URL` setting.