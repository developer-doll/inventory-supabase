from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.core.config import BOOTSTRAP_ADMIN_USERNAME, BOOTSTRAP_ADMIN_PASSWORD
from app.database import Base, engine, SessionLocal
from app.models import Role, User
from app.security import hash_password
from app.routers import auth, users, products, inventory, orders

app = FastAPI(title="Inventory & Billing API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        for role_name in ("superadmin", "inventory_manager", "sales_person"):
            if not db.query(Role).filter(Role.name == role_name).first():
                db.add(Role(name=role_name))
        db.commit()
        admin = db.query(User).filter(User.username == BOOTSTRAP_ADMIN_USERNAME).first()
        if not admin:
            role = db.query(Role).filter(Role.name == "superadmin").first()
            db.add(User(username=BOOTSTRAP_ADMIN_USERNAME, full_name="System Administrator",
                        password_hash=hash_password(BOOTSTRAP_ADMIN_PASSWORD), role_id=role.id))
            db.commit()
    finally:
        db.close()

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(products.router)
app.include_router(inventory.router)
app.include_router(orders.router)
