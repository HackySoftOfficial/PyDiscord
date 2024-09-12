from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    display_name = Column(String)
    avatar_url = Column(String)
    role_id = Column(Integer, ForeignKey('roles.id'))
    role = relationship("Role", back_populates="users")

class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    color = Column(String)  # Hex color code for the role
    users = relationship("User", back_populates="role")

class Guild(Base):
    __tablename__ = 'guilds'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    channels = relationship("Channel", back_populates="guild")

class Channel(Base):
    __tablename__ = 'channels'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    guild = relationship("Guild", back_populates="channels")
    messages = relationship("Message", back_populates="channel")

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    user_id = Column(Integer, ForeignKey('users.id'))
    channel_id = Column(Integer, ForeignKey('channels.id'))
    user = relationship("User")
    channel = relationship("Channel")
