from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Role

router = APIRouter()

@router.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/users/")
def create_user(username: str, hashed_password: str, display_name: str, role_id: int, db: Session = Depends(get_db)):
    db_role = db.query(Role).filter(Role.id == role_id).first()
    if db_role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    db_user = User(username=username, hashed_password=hashed_password, display_name=display_name, role_id=role_id)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
