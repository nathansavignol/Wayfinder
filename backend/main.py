from fastapi import FastAPI, Depends, HTTPException, status, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List

try:
    from .database import engine, Base, get_db
    from .models import Trip
    from .schemas import TripCreate, TripUpdate, TripResponse
except ImportError:
    from database import engine, Base, get_db
    from models import Trip
    from schemas import TripCreate, TripUpdate, TripResponse

# Initialize database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Wayfinder API",
    description="Backend REST API with SQLite database for Wayfinder travel itineraries",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler to return 400 Bad Request on schema/field validation errors (matches US5 Test 4 & US6 Test 2)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Bad Request: mandatory fields missing or invalid format", "errors": exc.errors()}
    )

# Exception handler to return 500/503 when database operation fails (matches US6 Test 4)
@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Database connection error"}
    )

@app.get("/", tags=["Health"])
def root():
    return {"message": "Wayfinder API is running", "docs": "/docs"}

# ----------------------------------------------------
# TRIPS CRUD ENDPOINTS (US5 & US6)
# ----------------------------------------------------

@app.get("/trips", response_model=List[TripResponse], tags=["Trips"])
def get_trips(db: Session = Depends(get_db)):
    """Retrieve all trips ordered by newest first."""
    return db.query(Trip).order_by(Trip.id.desc()).all()

@app.post("/trips", response_model=TripResponse, status_code=status.HTTP_201_CREATED, tags=["Trips"])
def create_trip(trip_data: TripCreate, db: Session = Depends(get_db)):
    """Create a new trip in the database (US5 Test 1)."""
    new_trip = Trip(
        title=trip_data.title,
        destination=trip_data.destination,
        start_date=trip_data.start_date,
        end_date=trip_data.end_date,
        budget=trip_data.budget or 0.0,
        status=trip_data.status or "planned",
        image=trip_data.image,
        notes=trip_data.notes
    )
    db.add(new_trip)
    db.commit()
    db.refresh(new_trip)
    return new_trip

@app.get("/trips/{id}", response_model=TripResponse, tags=["Trips"])
def get_trip_by_id(id: int, db: Session = Depends(get_db)):
    """Get single trip by ID (US5 Test 6 / US6 Test 1)."""
    trip = db.query(Trip).filter(Trip.id == id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip with id {id} not found"
        )
    return trip

@app.put("/trips/{id}", response_model=TripResponse, tags=["Trips"])
def update_trip(id: int, trip_data: TripUpdate, db: Session = Depends(get_db)):
    """Update an existing trip (US5 Test 2 / Test 5)."""
    trip = db.query(Trip).filter(Trip.id == id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip with id {id} not found"
        )

    update_dict = trip_data.model_dump(exclude_unset=True) if hasattr(trip_data, "model_dump") else trip_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(trip, field, value)

    db.commit()
    db.refresh(trip)
    return trip

@app.delete("/trips/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Trips"])
def delete_trip(id: int, db: Session = Depends(get_db)):
    """Delete a trip from the database (US5 Test 3)."""
    trip = db.query(Trip).filter(Trip.id == id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip with id {id} not found"
        )
    db.delete(trip)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
