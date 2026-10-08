from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
try:
    from .database import Base
except ImportError:
    from database import Base

class Trip(Base):
    __tablename__ = "trips"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, nullable=False)
    destination = Column(String, nullable=True)
    start_date = Column(String, nullable=True)
    end_date = Column(String, nullable=True)
    budget = Column(Float, default=0.0)
    status = Column(String, default="planned")
    image = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
