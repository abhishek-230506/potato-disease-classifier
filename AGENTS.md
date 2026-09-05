# Project Rules

- Do not retrain the model.
- Do not modify files inside `saved_model/`.
- Use the existing TensorFlow SavedModel in `saved_model/1/`.
- Keep backend code in `api/`.
- Keep frontend code in `frontend/`.
- Keep the project simple and clean.
- Follow the training notebook exactly for preprocessing and labels.
- If anything is unclear, inspect the training notebook first.
- Do not invent class names or preprocessing steps.
- Prefer readable, minimal code.
- Add helpful error handling.
- Use FastAPI for the backend.
- Use Streamlit for the frontend.
- Create a fresh implementation from scratch if old code is broken.