import random
from faker import Faker
from app.db.session import SessionLocal, init_db
from app.db.models import SourceCustomer

fake = Faker('en_IN')

SAMPLE_EXPLICIT_RECORDS = [
    {
        "customer_id": "C001",
        "name": "John Smith",
        "email": "john@example.com",
        "mobile": "9876543210",
        "city": "Chennai",
        "segment": "Premium"
    },
    {
        "customer_id": "C002",
        "name": "Mary Thomas",
        "email": "mary@example.com",
        "mobile": "9123456780",
        "city": "Bengaluru",
        "segment": "Standard"
    },
    {
        "customer_id": "C003",
        "name": "Arun Kumar",
        "email": "arun.kumar@domain.in",
        "mobile": "9840123456",
        "city": "Hyderabad",
        "segment": "Enterprise"
    },
    {
        "customer_id": "C004",
        "name": "Priya Sharma",
        "email": "priya.s@techcorp.com",
        "mobile": "9712345678",
        "city": "Mumbai",
        "segment": "Premium"
    },
    {
        "customer_id": "C005",
        "name": "David Wilson",
        "email": "david.w@globalnet.org",
        "mobile": "9988776655",
        "city": "Delhi",
        "segment": "Standard"
    }
]

def seed_source_database(count: int = 50):
    init_db()
    db = SessionLocal()
    
    print(f"Seeding database with {count} customer records...")
    
    # 1. Insert fixed sample records first
    for rec in SAMPLE_EXPLICIT_RECORDS:
        existing = db.query(SourceCustomer).filter(SourceCustomer.customer_id == rec["customer_id"]).first()
        if not existing:
            c = SourceCustomer(
                customer_id=rec["customer_id"],
                name=rec["name"],
                email=rec["email"],
                mobile=rec["mobile"],
                city=rec["city"],
                segment=rec["segment"]
            )
            db.add(c)
            
    # 2. Generate random Faker records
    cities = ["Chennai", "Bengaluru", "Hyderabad", "Mumbai", "Delhi", "Pune", "Kolkata"]
    segments = ["Standard", "Premium", "Enterprise", "VIP"]
    
    for i in range(6, count + 1):
        cid = f"C{i:03d}"
        existing = db.query(SourceCustomer).filter(SourceCustomer.customer_id == cid).first()
        if not existing:
            # 10 digit Indian mobile starting with 9, 8, 7, 6
            prefix = random.choice(["9", "8", "7", "6"])
            phone = prefix + "".join([str(random.randint(0, 9)) for _ in range(9)])
            first_name = fake.first_name()
            last_name = fake.last_name()
            full_name = f"{first_name} {last_name}"
            email = f"{first_name.lower()}.{last_name.lower()}{random.randint(10,99)}@{fake.free_email_domain()}"
            
            c = SourceCustomer(
                customer_id=cid,
                name=full_name,
                email=email,
                mobile=phone,
                city=random.choice(cities),
                segment=random.choice(segments)
            )
            db.add(c)
            
    db.commit()
    total = db.query(SourceCustomer).count()
    db.close()
    print(f"Seeding completed successfully! Total records in source_customers: {total}")

if __name__ == "__main__":
    seed_source_database(50)
