from app.database import SessionLocal, engine, Base
from app.models import Employee
from app.utils import generate_salt, hash_pin

SEED_EMPLOYEES = [
    {"matricule": "ADMIN001", "first_name": "Admin", "last_name": " ", "role": "admin", "pin": "1234"},
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    existing = db.query(Employee).count()
    if existing > 0:
        print(f"Database already has {existing} employees. Skipping seed.")
        db.close()
        return

    for data in SEED_EMPLOYEES:
        salt = generate_salt()
        emp = Employee(
            matricule=data["matricule"],
            first_name=data["first_name"],
            last_name=data["last_name"],
            role=data["role"],
            pin_hash=hash_pin(data["pin"], salt),
            salt=salt,
            is_active=True,
        )
        db.add(emp)
        print(f"  Created: {data['matricule']} ({data['first_name']} {data['last_name']}) — PIN: {data['pin']}")

    db.commit()
    db.close()
    print(f"Seeded {len(SEED_EMPLOYEES)} employees.")


if __name__ == "__main__":
    seed()
