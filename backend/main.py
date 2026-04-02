from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import models, database
from database import engine, get_db
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import datetime

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS for Flutter web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Schemas ---
class UserBase(BaseModel):
    email: str
    full_name: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    age: int
    health_score: int
    points: int
    badges: str
    class Config:
        from_attributes = True

class ActivityBase(BaseModel):
    type: str
    duration_minutes: int
    calories_burned: int
    notes: str = None

class ActivityCreate(ActivityBase):
    pass

class Activity(ActivityBase):
    id: int
    user_id: int
    date: datetime.datetime
    class Config:
        from_attributes = True

class PatientOut(BaseModel):
    total_patients: int
    avg_age: float
    total_billing: float
    medical_conditions: dict
    gender_dist: dict
    blood_types: dict

# --- API Endpoints ---

@app.post("/users/", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    # In real app, hash password
    new_user = models.User(email=user.email, full_name=user.full_name, hashed_password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/patients/stats/", response_model=PatientOut)
def get_patient_stats(db: Session = Depends(get_db)):
    patients = db.query(models.Patient).all()
    if not patients:
        return PatientOut(total_patients=0, avg_age=0, total_billing=0, medical_conditions={}, gender_dist={}, blood_types={})
    
    total = len(patients)
    avg_age = sum(p.age for p in patients) / total
    total_billing = sum(p.billing_amount for p in patients)
    
    conditions = {}
    genders = {}
    blood_types = {}
    
    for p in patients:
        conditions[p.medical_condition] = conditions.get(p.medical_condition, 0) + 1
        genders[p.gender] = genders.get(p.gender, 0) + 1
        blood_types[p.blood_type] = blood_types.get(p.blood_type, 0) + 1
        
    return PatientOut(
        total_patients=total,
        avg_age=avg_age,
        total_billing=total_billing,
        medical_conditions=conditions,
        gender_dist=genders,
        blood_types=blood_types
    )

@app.get("/leaderboard/", response_model=List[User])
def get_leaderboard(db: Session = Depends(get_db)):
    return db.query(models.User).order_by(models.User.points.desc()).limit(10).all()

@app.get("/activities/{user_id}", response_model=List[Activity])
def get_activities(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.Activity).filter(models.Activity.user_id == user_id).all()

@app.post("/activities/{user_id}", response_model=Activity)
def create_activity(user_id: int, activity: ActivityCreate, db: Session = Depends(get_db)):
    # Add activity
    new_activity = models.Activity(**activity.dict(), user_id=user_id)
    db.add(new_activity)
    
    # Reward points (10 per activity)
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        user.points += 10
        
    db.commit()
    db.refresh(new_activity)
    return new_activity

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
