"""
Add test data to the database for demo purposes
"""
from datetime import datetime, timedelta
from database import SessionLocal
from models import User, Patient, Scan
from auth_utils import hash_password
import random

def add_test_data():
    db = SessionLocal()
    
    try:
        # Check if we already have data
        existing_patients = db.query(Patient).count()
        if existing_patients > 0:
            print(f"✅ Database already has {existing_patients} patients")
            return
        
        print("📝 Adding test data...")
        
        # Create test doctor if doesn't exist
        doctor = db.query(User).filter(User.email == "doctor@test.com").first()
        if not doctor:
            doctor = User(
                email="doctor@test.com",
                username="doctor001",
                full_name="Dr. Sarah Johnson",
                role="doctor",
                hashed_password=hash_password("doctor123"),
                is_active=1,
                license_number="MD12345"
            )
            db.add(doctor)
            db.commit()
            db.refresh(doctor)
            print("✅ Created test doctor: doctor@test.com / doctor123")
        
        # Create test patients
        patients_data = [
            {
                "medical_record_number": "MRN001",
                "first_name": "Emily",
                "last_name": "Williams",
                "date_of_birth": datetime(1985, 3, 15),
                "gender": "Female",
                "contact_phone": "+1-555-0101",
                "contact_email": "emily.williams@email.com",
                "address": "123 Oak Street, Springfield"
            },
            {
                "medical_record_number": "MRN002",
                "first_name": "Jennifer",
                "last_name": "Davis",
                "date_of_birth": datetime(1978, 7, 22),
                "gender": "Female",
                "contact_phone": "+1-555-0102",
                "contact_email": "jennifer.davis@email.com",
                "address": "456 Pine Avenue, Riverside"
            },
            {
                "medical_record_number": "MRN003",
                "first_name": "Maria",
                "last_name": "Garcia",
                "date_of_birth": datetime(1990, 11, 8),
                "gender": "Female",
                "contact_phone": "+1-555-0103",
                "contact_email": "maria.garcia@email.com",
                "address": "789 Maple Drive, Lakeside"
            },
            {
                "medical_record_number": "MRN004",
                "first_name": "Lisa",
                "last_name": "Anderson",
                "date_of_birth": datetime(1982, 5, 30),
                "gender": "Female",
                "contact_phone": "+1-555-0104",
                "contact_email": "lisa.anderson@email.com",
                "address": "321 Elm Street, Hilltown"
            }
        ]
        
        created_patients = []
        for patient_data in patients_data:
            patient = Patient(**patient_data)
            db.add(patient)
            db.commit()
            db.refresh(patient)
            created_patients.append(patient)
            print(f"✅ Created patient: {patient.full_name} (MRN: {patient.medical_record_number})")
        
        # Create test scans for some patients
        scan_results = [
            ("Benign (Non-cancerous)", "Low Risk", 0.92, 8.5, 91.5),
            ("Benign (Non-cancerous)", "Very Low Risk", 0.95, 5.2, 94.8),
            ("Malignant (Cancerous)", "High Risk", 0.88, 87.3, 12.7),
            ("Benign (Non-cancerous)", "Low Risk", 0.90, 15.4, 84.6),
        ]
        
        for i, patient in enumerate(created_patients):
            # Add 1-3 scans per patient
            num_scans = random.randint(1, 3)
            for scan_num in range(num_scans):
                result_idx = random.randint(0, len(scan_results) - 1)
                result, risk, confidence, malignant_prob, benign_prob = scan_results[result_idx]
                
                days_ago = random.randint(1, 90)
                scan_date = datetime.utcnow() - timedelta(days=days_ago)
                
                scan = Scan(
                    patient_id=patient.id,
                    user_id=doctor.id,
                    image_path=f"uploads/patient_{patient.id}/test_scan_{scan_num}.jpg",
                    original_filename=f"mammogram_{scan_num}.jpg",
                    prediction_result=result,
                    confidence_score=confidence,
                    malignant_probability=malignant_prob,
                    benign_probability=benign_prob,
                    risk_level=risk,
                    mean_intensity=125.5,
                    std_intensity=42.3,
                    brightness=0.65,
                    contrast=0.42,
                    image_width=224,
                    image_height=224,
                    file_format="JPEG",
                    doctor_notes=f"Routine screening scan. Patient shows {result.lower()}." if scan_num == 0 else None,
                    report_generated=1 if scan_num == 0 else 0,
                    created_at=scan_date
                )
                db.add(scan)
            
            db.commit()
            print(f"✅ Created {num_scans} scan(s) for {patient.full_name}")
        
        print("\n" + "="*60)
        print("✅ Test data added successfully!")
        print("="*60)
        print("\n📊 Summary:")
        print(f"   - Patients: {len(created_patients)}")
        print(f"   - Doctor: Dr. Sarah Johnson")
        print(f"   - Login: doctor@test.com / doctor123")
        print("\n🌐 Access the app at: http://localhost:3000")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"❌ Error adding test data: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_test_data()

