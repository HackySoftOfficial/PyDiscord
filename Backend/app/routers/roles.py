from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Role

router = APIRouter()

@router.get("/roles/{role_id}")
def get_role(role_id: int, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.id == role_id).first()
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return role

@router.post("/roles/")
def create_role(name: str, color: str, db: Session = Depends(get_db)):
    db_role = Role(name=name, color=color)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role
