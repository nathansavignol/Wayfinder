# Wayfinder Travel Itinerary Manager

A clean, minimalist application to create, edit, view, and delete travel itineraries, powered by a Python (FastAPI) REST backend and persistent SQLite database.

---

## Running the Application

### 1. Start the Backend API
From the project root:
```powershell
python backend\run.py
```
* **API Server:** http://127.0.0.1:8000
* **Interactive Swagger UI Documentation:** http://127.0.0.1:8000/docs

### 2. Open the Frontend
Double-click **`index.html`** or open it in your browser.
The interface will automatically communicate with the backend API at `http://127.0.0.1:8000/trips`.

---

## Running Automated Acceptance Tests (US5 & US6)

To execute the automated validation tests for API endpoints and database persistence:
```powershell
python backend\test_api.py
```
