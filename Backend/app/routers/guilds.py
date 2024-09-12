from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Guild

router = APIRouter()

@router.get("/guilds/{guild_id}")
def get_guild(guild_id: int, db: Session = Depends(get_db)):
    guild = db.query(Guild).filter(Guild.id == guild_id).first()
    if guild is None:
        raise HTTPException(status_code=404, detail="Guild not found")
    return guild

@router.post("/guilds/")
def create_guild(name: str, db: Session = Depends(get_db)):
    db_guild = Guild(name=name)
    db.add(db_guild)
    db.commit()
    db.refresh(db_guild)
    return db_guild
