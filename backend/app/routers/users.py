from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models import User, Role
from app.schemas import UserCreate, UserOut
from app.security import require_roles, hash_password

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/", response_model=UserOut)
def create_user(data: UserCreate, db: Session = Depends(get_db),
                admin: User = Depends(require_roles("superadmin"))):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=409, detail="Username already exists")
    role = db.query(Role).filter(Role.name == data.role).first()
    user = User(username=data.username, full_name=data.full_name,
                password_hash=hash_password(data.password), role_id=role.id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "username": user.username, "full_name": user.full_name,
            "role": role.name, "is_active": user.is_active}

@router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db),
               admin: User = Depends(require_roles("superadmin"))):
    users = db.query(User).options(joinedload(User.role)).order_by(User.id.desc()).all()
    return [{"id": u.id, "username": u.username, "full_name": u.full_name,
             "role": u.role.name, "is_active": u.is_active} for u in users]
