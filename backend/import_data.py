import pandas as pd
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
import os

# Create tables
models.Base.metadata.create_all(bind=engine)

def import_csv():
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'healthcare_dataset.csv')
    if not os.path.exists(csv_path):
        print("CSV file not found!")
        return

    df = pd.read_csv(csv_path)
    db = SessionLocal()
    
    # Simple check to avoid duplicates
    if db.query(models.Patient).count() > 0:
        print("Data already imported.")
        return

    print(f"Importing {len(df)} rows from CSV...")
    
    patients = []
    for _, row in df.iterrows():
        patient = models.Patient(
            name=row['Name'],
            age=row['Age'],
            gender=row['Gender'],
            blood_type=row['Blood Type'],
            medical_condition=row['Medical Condition'],
            billing_amount=row['Billing Amount']
        )
        patients.append(patient)
        
        # Batch commit every 1000 rows
        if len(patients) >= 1000:
            db.bulk_save_objects(patients)
            db.commit()
            patients = []
            print(".", end="", flush=True)

    if patients:
        db.bulk_save_objects(patients)
        db.commit()
    
    # Create a default user for testing
    if db.query(models.User).filter(models.User.email == 'user@example.com').count() == 0:
        test_user = models.User(
            email='user@example.com',
            full_name='Nguyễn Văn A',
            hashed_password='password123' # Mock password
        )
        db.add(test_user)
        db.commit()
        print("\nCreated test user: user@example.com")

    print("\nImport complete.")
    db.close()

if __name__ == "__main__":
    import_csv()
