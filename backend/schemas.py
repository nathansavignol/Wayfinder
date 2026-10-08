from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

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
