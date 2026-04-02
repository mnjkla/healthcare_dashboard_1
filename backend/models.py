from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    age = Column(Integer, default=30)
    health_score = Column(Integer, default=80)
    points = Column(Integer, default=0)
    badges = Column(String, default="[]") # JSON string
    
    activities = relationship("Activity", back_populates="owner")

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String)
    duration_minutes = Column(Integer)
    calories_burned = Column(Integer)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    notes = Column(String, nullable=True)
    
    owner = relationship("User", back_populates="activities")

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    age = Column(Integer)
    gender = Column(String)
    blood_type = Column(String)
    medical_condition = Column(String)
    billing_amount = Column(Float)
