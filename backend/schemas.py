from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime

# ----------------------------------------------------
# AUTH SCHEMAS (US8 & US9)
# ----------------------------------------------------
class UserRegister(BaseModel):
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=6, description="Password with minimum 6 characters")

class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    created_at: Optional[datetime] = None

# ----------------------------------------------------
# TRIP SCHEMAS (US5 & US6)
# ----------------------------------------------------
class TripBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    title: str = Field(..., min_length=1, description="Title of the trip (mandatory)")
    destination: Optional[str] = None
    start_date: Optional[str] = Field(None, alias="startDate")
    end_date: Optional[str] = Field(None, alias="endDate")
    budget: Optional[float] = 0.0
    status: Optional[str] = "planned"
    image: Optional[str] = None
    notes: Optional[str] = None

class TripCreate(TripBase):
    pass

class TripUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    title: Optional[str] = None
    destination: Optional[str] = None
    start_date: Optional[str] = Field(None, alias="startDate")
    end_date: Optional[str] = Field(None, alias="endDate")
    budget: Optional[float] = None
    status: Optional[str] = None
    image: Optional[str] = None
    notes: Optional[str] = None

class TripResponse(TripBase):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: int
    created_at: Optional[datetime] = None
    user_id: Optional[int] = None

# ----------------------------------------------------
# ACTIVITY SCHEMAS (US10 - US15)
# ----------------------------------------------------
class ActivityCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str = Field(..., min_length=1, description="Activity title")
    price: Optional[float] = Field(0.0, ge=0.0, description="Price must be non-negative (US11)")
    type: Optional[str] = Field(None, description="Category or type of activity (US12)")
    duration: Optional[float] = Field(None, gt=0, description="Duration must be positive (US13)")
    location: Optional[str] = Field(None, description="Location of activity (US14)")
    notes: Optional[str] = Field(None, max_length=1000, description="Notes up to 1000 characters (US15)")

class ActivityPatch(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: Optional[str] = Field(None, min_length=1)
    price: Optional[float] = Field(None, ge=0.0)
    type: Optional[str] = None
    duration: Optional[float] = Field(None, gt=0)
    location: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)

class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trip_id: int
    title: str
    price: float
    type: Optional[str] = None
    duration: Optional[float] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

# ----------------------------------------------------
# BUDGET COMPARISON SCHEMA (US16)
# ----------------------------------------------------
class TripBudgetResponse(BaseModel):
    trip_id: int
    initial_budget: float
    total_cost: float
    remaining_balance: float
    variance: float
    is_over_budget: bool
