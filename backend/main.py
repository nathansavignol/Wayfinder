from fastapi import FastAPI, Depends, HTTPException, status, Response, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional

try:
    from .database import engine, Base, get_db
    from .models import Trip, User, Activity
    from .schemas import (
        TripCreate, TripUpdate, TripResponse,
        UserRegister, UserLogin, TokenResponse, UserResponse,
        ActivityCreate, ActivityPatch, ActivityResponse, TripBudgetResponse
    )
    from .auth import hash_password, verify_password, create_access_token, get_current_user
except ImportError:
    from database import engine, Base, get_db
    from models import Trip, User, Activity
    from schemas import (
        TripCreate, TripUpdate, TripResponse,
        UserRegister, UserLogin, TokenResponse, UserResponse,
        ActivityCreate, ActivityPatch, ActivityResponse, TripBudgetResponse
    )
    from auth import hash_password, verify_password, create_access_token, get_current_user

# Initialize database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Wayfinder API",
    description="Backend REST API with SQLite database, Authentication & Activities for Wayfinder",
    version="1.2.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Return 400 Bad Request on schema/field validation errors (matches US5 Test 4, US6 Test 2, US8 Test 3, US11 Test 2/3, US13 Test 2, US15 Test 2)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Bad Request: mandatory fields missing or invalid format", "errors": exc.errors()}
    )

# Return 503 when database operation fails (matches US6 Test 4)
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
# AUTHENTICATION ENDPOINTS (US8 & US9)
# ----------------------------------------------------

@app.post("/auth/register", status_code=status.HTTP_201_CREATED, tags=["Auth"])
def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    """Create a new user account with hashed password (US8 Test 1, 2, 3)."""
    existing = db.query(User).filter(User.email == user_data.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists"
        )

    hashed = hash_password(user_data.password)
    new_user = User(
        email=user_data.email.lower(),
        hashed_password=hashed
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "id": new_user.id,
        "email": new_user.email,
        "message": "User registered successfully"
    }

@app.post("/auth/login", response_model=TokenResponse, tags=["Auth"])
def login_user(login_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return JWT access token (US9 Test 1, 2)."""
    user = db.query(User).filter(User.email == login_data.email.lower()).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    token = create_access_token(data={"sub": str(user.id), "email": user.email})
    return {"access_token": token, "token_type": "bearer"}

# ----------------------------------------------------
# TRIPS CRUD ENDPOINTS (US5 & US6 - Protected by US9)
# ----------------------------------------------------

@app.get("/trips", response_model=List[TripResponse], tags=["Trips"])
def get_trips(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all trips owned by the authenticated user (US9 Test 3)."""
    return db.query(Trip).filter(
        (Trip.user_id == current_user.id) | (Trip.user_id == None)
    ).order_by(Trip.id.desc()).all()

@app.post("/trips", response_model=TripResponse, status_code=status.HTTP_201_CREATED, tags=["Trips"])
def create_trip(
    trip_data: TripCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new trip linked to authenticated user (US5 Test 1)."""
    new_trip = Trip(
        title=trip_data.title,
        destination=trip_data.destination,
        start_date=trip_data.start_date,
        end_date=trip_data.end_date,
        budget=trip_data.budget or 0.0,
        status=trip_data.status or "planned",
        image=trip_data.image,
        notes=trip_data.notes,
        user_id=current_user.id
    )
    db.add(new_trip)
    db.commit()
    db.refresh(new_trip)
    return new_trip

@app.get("/trips/{id}", response_model=TripResponse, tags=["Trips"])
def get_trip_by_id(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get single trip by ID (US5 Test 6 / US6 Test 1)."""
    trip = db.query(Trip).filter(Trip.id == id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip with id {id} not found"
        )
    return trip

@app.put("/trips/{id}", response_model=TripResponse, tags=["Trips"])
def update_trip(
    id: int,
    trip_data: TripUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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
def delete_trip(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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

# ----------------------------------------------------
# ACTIVITIES ENDPOINTS (US10 - US15)
# ----------------------------------------------------

def verify_trip_access(trip_id: int, current_user: User, db: Session) -> Trip:
    """Helper to verify trip exists and check ownership (US10 Test 2 & 3)."""
    trip = db.query(Trip).filter(Trip.id == trip_id).first()
    if not trip:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Trip with id {trip_id} not found"
        )
    if trip.user_id is not None and trip.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not own this trip"
        )
    return trip

@app.post("/trips/{trip_id}/activities", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED, tags=["Activities"])
def create_activity(
    trip_id: int,
    activity_data: ActivityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create an activity linked to a trip (US10, US11, US12, US13, US14, US15)."""
    verify_trip_access(trip_id, current_user, db)

    new_activity = Activity(
        trip_id=trip_id,
        title=activity_data.title,
        price=activity_data.price if activity_data.price is not None else 0.0,
        type=activity_data.type,
        duration=activity_data.duration,
        location=activity_data.location,
        notes=activity_data.notes
    )
    db.add(new_activity)
    db.commit()
    db.refresh(new_activity)
    return new_activity

@app.get("/trips/{trip_id}/activities", response_model=List[ActivityResponse], tags=["Activities"])
def get_trip_activities(
    trip_id: int,
    type: Optional[str] = Query(None, description="Filter activities by type (US12)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all activities for a trip, with optional category filter (US12 Test 1, 2)."""
    verify_trip_access(trip_id, current_user, db)

    query = db.query(Activity).filter(Activity.trip_id == trip_id)
    if type is not None:
        query = query.filter(Activity.type == type)

    return query.order_by(Activity.id.asc()).all()

@app.get("/trips/{trip_id}/activities/{id}", response_model=ActivityResponse, tags=["Activities"])
def get_activity_by_id(
    trip_id: int,
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve a single activity by ID (US11 Test 1, US13 Test 1, US14 Test 1, US15 Test 1)."""
    verify_trip_access(trip_id, current_user, db)

    activity = db.query(Activity).filter(Activity.id == id, Activity.trip_id == trip_id).first()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activity with id {id} not found in this trip"
        )
    return activity

@app.patch("/trips/{trip_id}/activities/{id}", response_model=ActivityResponse, tags=["Activities"])
def patch_activity(
    trip_id: int,
    id: int,
    activity_data: ActivityPatch,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update fields of an activity (US12 Test 3, US13 Test 3, US15 Test 1, 2, 3)."""
    verify_trip_access(trip_id, current_user, db)

    activity = db.query(Activity).filter(Activity.id == id, Activity.trip_id == trip_id).first()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activity with id {id} not found in this trip"
        )

    update_dict = activity_data.model_dump(exclude_unset=True) if hasattr(activity_data, "model_dump") else activity_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(activity, field, value)

    db.commit()
    db.refresh(activity)
    return activity

@app.delete("/trips/{trip_id}/activities/{id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Activities"])
def delete_activity(
    trip_id: int,
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an activity from a trip."""
    verify_trip_access(trip_id, current_user, db)

    activity = db.query(Activity).filter(Activity.id == id, Activity.trip_id == trip_id).first()
    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Activity with id {id} not found in this trip"
        )
    db.delete(activity)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# ----------------------------------------------------
# BUDGET COMPARISON ENDPOINT (US16)
# ----------------------------------------------------

@app.get("/trips/{trip_id}/budget", response_model=TripBudgetResponse, tags=["Budget"])
def get_trip_budget_comparison(
    trip_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calculate total cost from activities and compare against budget (US16 Test 1, 2, 3)."""
    trip = verify_trip_access(trip_id, current_user, db)

    activities = db.query(Activity).filter(Activity.trip_id == trip_id).all()
    total_cost = sum(act.price for act in activities if act.price is not None)
    initial_budget = trip.budget or 0.0
    remaining_balance = initial_budget - total_cost
    variance = initial_budget - total_cost
    is_over_budget = total_cost > initial_budget

    return {
        "trip_id": trip_id,
        "initial_budget": initial_budget,
        "total_cost": total_cost,
        "remaining_balance": remaining_balance,
        "variance": variance,
        "is_over_budget": is_over_budget
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
