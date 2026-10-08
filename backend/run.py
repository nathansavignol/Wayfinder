import os
import sys
import uvicorn

# Ensure the backend directory is in Python module search path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    print("Starting Wayfinder API on http://127.0.0.1:8000 ...")
    print("Interactive Swagger Documentation available at http://127.0.0.1:8000/docs")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
