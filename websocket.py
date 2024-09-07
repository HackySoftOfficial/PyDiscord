from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref
from datetime import datetime, timedelta
import jwt
from jwt import PyJWTError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional, Dict
from fastapi.middleware.cors import CORSMiddleware
import bcrypt
from fastapi import Request
from sqlalchemy import Boolean
import uuid
from sqlalchemy import UniqueConstraint

# Function to hash a password
def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

# Function to verify a password against a stored hash
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# Setup
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Secret key and algorithm for JWT
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Database Models
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True, unique=True)
    email = Column(String, index=True, unique=True)
    hashed_password = Column(String)
    display_name = Column(String, default="")
    avatar_url = Column(String, default="")
    about_me = Column(String, default="")
    pronouns = Column(String, default="")
    guilds = relationship("GuildMember", back_populates="user")

class Guild(Base):
    __tablename__ = 'guilds'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    owner_id = Column(Integer)
    invite_code = Column(String, nullable=True)  # Adding invite_code column
    members = relationship("GuildMember", back_populates="guild")

class GuildMember(Base):
    __tablename__ = 'guild_members'
    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    guild = relationship("Guild", back_populates="members")
    user = relationship("User", back_populates="guilds")

    __table_args__ = (UniqueConstraint('guild_id', 'user_id', name='uix_guild_user'),)

class Channel(Base):
    __tablename__ = 'channels'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    guild = relationship("Guild")
    messages = relationship("Message", back_populates="channel")
    permissions = relationship("ChannelPermission", back_populates="channel")

class ChannelPermission(Base):
    __tablename__ = 'channel_permissions'
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey('channels.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    can_view = Column(Boolean, default=False)
    can_manage = Column(Boolean, default=False)
    channel = relationship("Channel", back_populates="permissions")
    user = relationship("User")

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    channel_id = Column(Integer, ForeignKey('channels.id'))
    channel = relationship("Channel", back_populates="messages")
    reactions = relationship("Reaction", back_populates="message")

class Reaction(Base):
    __tablename__ = 'reactions'
    id = Column(Integer, primary_key=True, index=True)
    emoji = Column(String)
    message_id = Column(Integer, ForeignKey('messages.id'))
    message = relationship("Message", back_populates="reactions")

Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this according to your security needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket Manager
class WebSocketManager:
    def __init__(self):
        self.connections: Dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.connections[user_id] = websocket
        self.user_status[user_id] = "online"

    def disconnect(self, user_id: int):
        if user_id in self.connections:
            del self.connections[user_id]
            self.user_status[user_id] = "offline"  # Set status to offline

    async def send_message(self, user_id: int, message: str):
        if user_id in self.connections:
            websocket = self.connections[user_id]
            await websocket.send_text(message)

websocket_manager = WebSocketManager()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# JWT Helper Functions
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

def user_to_dict(user):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "display_name": user.display_name,
        "avatar_url": user.avatar_url,
        "about_me": user.about_me,
        "pronouns": user.pronouns
    }

def has_permission(db, user: User, guild_id: Optional[int] = None, operation: str = None) -> bool:
    if operation in ["delete_guild", "create_channel", "delete_channel"]:
        if not guild_id:
            return False
        guild = db.query(Guild).filter(Guild.id == guild_id).first()
        if not guild:
            return False
        if guild.owner_id != user.id:
            return False
    return True

def extract_token_from_headers(websocket: WebSocket) -> Optional[str]:
    """Extract the token from WebSocket headers."""
    headers = websocket.headers
    authorization_header = headers.get("Authorization")
    if authorization_header:
        prefix, token = authorization_header.split(" ", 1)
        if prefix.lower() == "bearer":
            return token
    return None

def get_current_user_from_token(token: str) -> User:
    """Extract the current user from the token."""
    username = verify_token(token)
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user")
    return user

def guild_to_dict(guild: Guild) -> dict:
    """Convert Guild object to dictionary."""
    return {
        "id": guild.id,
        "name": guild.name,
        "owner_id": guild.owner_id
    }

def channel_to_dict(channel: Channel) -> dict:
    """Convert Channel object to dictionary."""
    return {
        "id": channel.id,
        "name": channel.name,
        "guild_id": channel.guild_id
    }

# WebSocket Endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Accept the WebSocket connection
    await websocket.accept()

    # Extract and verify token
    token = extract_token_from_headers(websocket)
    
    if token:
        try:
            current_user = get_current_user_from_token(token)
        except HTTPException as e:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            print(f"Connection closed due to invalid token: {e.detail}")
            return
    else:
        current_user = None

    print("Token verified or no token provided, connection is open")
    
    try:
        while True:
            data = await websocket.receive_json()
            print(f"Received data: {data}")
            command = data.get("command")
            payload = data.get("payload")

            if command == "register" or command == "login":
                if command == "register":
                    user_data = payload
                    db = SessionLocal()
                    # Check if the email is already in use
                    existing_user = db.query(User).filter(User.email == user_data['email']).first()
                    if existing_user:
                        await websocket.send_json({"status": "error", "detail": "Email is already in use"})
                    else:
                        # Proceed with registration
                        hashed_password = get_password_hash(user_data['password'])
                        db_user = User(username=user_data['username'], email=user_data['email'], hashed_password=hashed_password)
                        db.add(db_user)
                        db.commit()
                        db.refresh(db_user)
                        await websocket.send_json({"status": "success", "user": user_to_dict(db_user)})
                    db.close()
                elif command == "login":
                    form_data = payload
                    db = SessionLocal()
                    user = db.query(User).filter(User.username == form_data['username']).first()
                    if not user or not verify_password(form_data['password'], user.hashed_password):
                        await websocket.send_json({"status": "error", "detail": "Invalid credentials"})
                    else:
                        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
                        access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
                        await websocket.send_json({"access_token": access_token, "token_type": "bearer"})

            elif current_user:
                if command == "get_user":
                    user_id = payload['user_id']
                    db = SessionLocal()
                    user = db.query(User).filter(User.id == user_id).first()
                    if user is None:
                        await websocket.send_json({"status": "error", "detail": "User not found"})
                    else:
                        await websocket.send_json({"status": "success", "user": user_to_dict(user)})

                elif command == "update_user":
                    db = SessionLocal()
                    db_user = db.query(User).filter(User.id == current_user.id).first()
                    if db_user is None:
                        await websocket.send_json({"status": "error", "detail": "User not found"})
                    else:
                        # Update only provided fields
                        if 'display_name' in payload:
                            db_user.display_name = payload['display_name']
                        if 'avatar_url' in payload:
                            db_user.avatar_url = payload['avatar_url']
                        if 'about_me' in payload:
                            db_user.about_me = payload['about_me']
                        if 'pronouns' in payload:
                            db_user.pronouns = payload['pronouns']
                        db.commit()
                        db.refresh(db_user)
                        await websocket.send_json({"status": "success", "user": user_to_dict(db_user)})

                elif command == "create_guild":
                    db = SessionLocal()
                    invite_code = str(uuid.uuid4())
                    db_guild = Guild(name=payload['name'], owner_id=current_user.id, invite_code=invite_code)
                    db.add(db_guild)
                    db.commit()
                    db.refresh(db_guild)
                    # Add current user to the guild members
                    db.add(GuildMember(guild_id=db_guild.id, user_id=current_user.id))
                    db.commit()
                    await websocket.send_json({"status": "success", "guild": guild_to_dict(db_guild)})

                elif command == "get_guild":
                    db = SessionLocal()
                    guild = db.query(Guild).filter(Guild.id == payload['guild_id']).first()
                    if guild is None:
                        await websocket.send_json({"status": "error", "detail": "Guild not found"})
                    else:
                        # Check if the user is a member
                        if not db.query(GuildMember).filter(GuildMember.user_id == current_user.id, GuildMember.guild_id == guild.id).first():
                            await websocket.send_json({"status": "error", "detail": "User is not a member of this guild"})
                        else:
                            await websocket.send_json({"status": "success", "guild": guild_to_dict(guild)})

                elif command == "delete_guild":
                    db = SessionLocal()
                    guild_id = payload.get('guild_id')
                    
                    if not has_permission(db, current_user, guild_id, command):
                        await websocket.send_json({"status": "error", "detail": "Permission denied"})
                    else:
                        guild = db.query(Guild).filter(Guild.id == guild_id).first()
                        if guild is None:
                            await websocket.send_json({"status": "error", "detail": "Guild not found"})
                        else:
                            db.delete(guild)
                            db.commit()
                            await websocket.send_json({"status": "success", "detail": "Guild deleted"})
                    db.close()

                elif command == "create_channel":
                    channel_data = payload
                    db = SessionLocal()
                    if not has_permission(db, current_user, channel_data['guild_id'], command):
                        await websocket.send_json({"status": "error", "detail": "Permission denied"})
                        continue
                    db_channel = Channel(name=channel_data['name'], guild_id=channel_data['guild_id'])
                    db.add(db_channel)
                    db.commit()
                    db.refresh(db_channel)
                    await websocket.send_json({"status": "success", "channel": channel_to_dict(db_channel)})

                elif command == "get_channel":
                    channel_id = payload['channel_id']
                    db = SessionLocal()
                    channel = db.query(Channel).filter(Channel.id == channel_id).first()
                    if channel is None:
                        await websocket.send_json({"status": "error", "detail": "Channel not found"})
                    else:
                        # Check if the user has permission to view this channel
                        permission = db.query(ChannelPermission).filter(ChannelPermission.user_id == current_user.id, ChannelPermission.channel_id == channel_id, ChannelPermission.can_view.is_(True)).first()
                        if not permission:
                            await websocket.send_json({"status": "error", "detail": "No permission to view this channel"})
                        else:
                            await websocket.send_json({"status": "success", "channel": channel_to_dict(channel)})

                elif command == "update_channel":
                    channel_id = payload['channel_id']
                    channel_update = payload['channel_update']
                    db = SessionLocal()
                    channel = db.query(Channel).filter(Channel.id == channel_id).first()
                    if channel is None:
                        await websocket.send_json({"status": "error", "detail": "Channel not found"})
                    else:
                        # Update only provided fields
                        if 'name' in channel_update:
                            channel.name = channel_update['name']
                        db.commit()
                        db.refresh(channel)
                        await websocket.send_json({"status": "success", "channel": channel_to_dict(channel)})

                elif command == "delete_channel":
                    channel_id = payload['channel_id']
                    db = SessionLocal()
                    if not has_permission(db, current_user, db.query(Channel).filter(Channel.id == channel_id).first().guild_id, command):
                        await websocket.send_json({"status": "error", "detail": "Permission denied"})
                        continue
                    channel = db.query(Channel).filter(Channel.id == channel_id).first()
                    if channel is None:
                        await websocket.send_json({"status": "error", "detail": "Channel not found"})
                    else:
                        db.delete(channel)
                        db.commit()
                        await websocket.send_json({"status": "success", "detail": "Channel deleted"})

                elif command == "request_invite":
                    guild_id = payload['guild_id']
                    db = SessionLocal()
                    guild = db.query(Guild).filter(Guild.id == guild_id).first()
                    if guild is None:
                        await websocket.send_json({"status": "error", "detail": "Guild not found"})
                    elif not db.query(GuildMember).filter(GuildMember.user_id == current_user.id, GuildMember.guild_id == guild.id).first():
                        await websocket.send_json({"status": "error", "detail": "User is not a member of this guild"})
                    else:
                        # Generate an invite code if it does not exist
                        if guild.invite_code is None:
                            guild.invite_code = str(uuid.uuid4())
                            db.commit()
                        await websocket.send_json({"status": "success", "invite_code": guild.invite_code})

                elif command == "join_guild":
                    invite_code = payload['invite_code']
                    db = SessionLocal()
                    guild = db.query(Guild).filter(Guild.invite_code == invite_code).first()
                    if guild is None:
                        await websocket.send_json({"status": "error", "detail": "Invalid invite code"})
                    else:
                        # Check if the user is already a member of the guild
                        existing_membership = db.query(GuildMember).filter(GuildMember.user_id == current_user.id, GuildMember.guild_id == guild.id).first()
                        if existing_membership:
                            await websocket.send_json({"status": "error", "detail": "User is already a member of this guild"})
                        else:
                            db.add(GuildMember(user_id=current_user.id, guild_id=guild.id))
                            # Add user to the guild's channels
                            channels = db.query(Channel).filter(Channel.guild_id == guild.id).all()
                            for channel in channels:
                                permission = ChannelPermission(user_id=current_user.id, channel_id=channel.id, can_view=True, can_manage=False)
                                db.add(permission)
                            guild.invite_code = None  # Remove the invite code after use
                            db.commit()
                        await websocket.send_json({"status": "success", "detail": "Joined guild"})

                elif command == "list_user_guilds":
                    db = SessionLocal()
                    memberships = db.query(GuildMember).filter(GuildMember.user_id == current_user.id).all()
                    guild_ids = {membership.guild_id for membership in memberships}
                    guilds = db.query(Guild).filter(Guild.id.in_(guild_ids)).all()
                    await websocket.send_json({"status": "success", "guilds": [guild_to_dict(guild) for guild in guilds]})
                elif command == "set_status":
                    status = payload['status']
                    if status not in ["online", "dnd", "idle", "invisible"]:
                        await websocket.send_json({"status": "error", "detail": "Invalid status"})
                    else:
                        websocket_manager.set_status(current_user.id, status)
                        await websocket.send_json({"status": "success", "status": status})

                elif command == "get_user_status":
                    user_id = payload['user_id']
                    status = websocket_manager.user_status.get(user_id, "offline")
                    await websocket.send_json({"status": "success", "user_id": user_id, "status": status})
                elif command == "get_channel_users":
                    channel_id = payload['channel_id']
                    page = payload.get('page', 1)
                    per_page = 100
                    db = SessionLocal()
                    channel = db.query(Channel).filter(Channel.id == channel_id).first()
                    if channel is None:
                        await websocket.send_json({"status": "error", "detail": "Channel not found"})
                    else:
                        permissions_query = db.query(ChannelPermission).filter(ChannelPermission.channel_id == channel_id).order_by(ChannelPermission.user_id)
                        total_users = permissions_query.count()
                        permissions = permissions_query.offset((page - 1) * per_page).limit(per_page).all()
                        user_ids = [perm.user_id for perm in permissions]
                        users = db.query(User).filter(User.id.in_(user_ids)).all()
                        db.close()
                        await websocket.send_json({
                            "status": "success",
                            "page": page,
                            "total_pages": (total_users // per_page) + 1,
                            "users": [user_to_dict(user) for user in users]
                        })
                # Add to the WebSocket command handling
                elif command == "get_messages":
                    channel_id = payload['channel_id']
                    page = payload.get('page', 1)
                    per_page = 100
                    db = SessionLocal()
                    messages_query = db.query(Message).filter(Message.channel_id == channel_id).order_by(Message.id.desc())
                    total_messages = messages_query.count()
                    messages = messages_query.offset((page - 1) * per_page).limit(per_page).all()
                    db.close()
                    await websocket.send_json({
                        "status": "success",
                        "page": page,
                        "total_pages": (total_messages // per_page) + 1,
                        "messages": [{"id": msg.id, "content": msg.content} for msg in messages]
                    })
                # Add to the WebSocket command handling
                elif command == "send_message":
                    channel_id = payload['channel_id']
                    content = payload['content']
                    db = SessionLocal()
                    channel = db.query(Channel).filter(Channel.id == channel_id).first()
                    if channel is None:
                        await websocket.send_json({"status": "error", "detail": "Channel not found"})
                    else:
                        # Save the message in the database
                        db_message = Message(content=content, channel_id=channel_id)
                        db.add(db_message)
                        db.commit()
                        db.refresh(db_message)
                        await websocket.send_json({"status": "success", "message_id": db_message.id, "content": content})
                    db.close()



            else:
                await websocket.send_json({"status": "error", "detail": "Unauthorized"})
                print("Unauthorized command received")
    
    except WebSocketDisconnect:
        print("WebSocket disconnected")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("websocket:app", host="0.0.0.0", port=8000, reload=True)
