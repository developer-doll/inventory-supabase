from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models import User
from app.schemas import LoginIn, TokenOut, UserOut
from app.security import verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).options(joinedload(User.role)).filter(User.username == data.username).first()
    if not user or not user.is_active or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    return {"access_token": create_access_token(user), "user": {
        "id": user.id, "username": user.username, "full_name": user.full_name,
        "role": user.role.name, "is_active": user.is_active
    }}

@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "username": user.username, "full_name": user.full_name,
            "role": user.role.name, "is_active": user.is_active}
