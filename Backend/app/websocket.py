from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, inspect, Boolean, DateTime, UniqueConstraint, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, backref
from datetime import datetime, timedelta
import jwt
from jwt import PyJWTError
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional, Dict, Set
from fastapi.middleware.cors import CORSMiddleware
import bcrypt
from fastapi import Request
import uuid
from loguru import logger
import traceback
from sqlalchemy.pool import QueuePool
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, inspect, Boolean, DateTime
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
import uuid
from sqlalchemy import UniqueConstraint
from loguru import logger
import traceback
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import time

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
engine = create_engine(DATABASE_URL, poolclass=QueuePool, pool_size=20, max_overflow=0, pool_timeout=30, connect_args={"check_same_thread": False})
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
    avatar_url = Column(String, default="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fimages-wixmp-ed30a86b8c4ca887773594c2.wixmp.com%2Ff%2F75bff394-4f86-45a8-a923-e26223aa74cb%2Fde901o7-d61b3bfb-f1b1-453b-8268-9200130bbc65.png%3Ftoken%3DeyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7InBhdGgiOiJcL2ZcLzc1YmZmMzk0LTRmODYtNDVhOC1hOTIzLWUyNjIyM2FhNzRjYlwvZGU5MDFvNy1kNjFiM2JmYi1mMWIxLTQ1M2ItODI2OC05MjAwMTMwYmJjNjUucG5nIn1dXSwiYXVkIjpbInVybjpzZXJ2aWNlOmZpbGUuZG93bmxvYWQiXX0.aEck9OnRf_XJzrEzZNvrGS2XpAlo2ixuxoAX5fgpNnw&f=1&nofb=1&ipt=5b65b8c2a2a8d93e2e05d2f9893d068b631030ea239ab9a29be57785374d72c7&ipo=images")
    about_me = Column(String, default="")
    pronouns = Column(String, default="")
    guilds = relationship("GuildMember", back_populates="user")

class Guild(Base):
    __tablename__ = 'guilds'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    owner_id = Column(Integer)
    invite_code = Column(String, nullable=True)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)  # Make it nullable
    members = relationship("GuildMember", back_populates="guild")
    channels = relationship("Channel", back_populates="guild")

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
    guild = relationship("Guild", back_populates="channels")
    messages = relationship("Message", back_populates="channel")
    permissions = relationship("ChannelPermission", back_populates="channel")

class ChannelPermission(Base):
    __tablename__ = 'channel_permissions'
    id = Column(Integer, primary_key=True, index=True)
    channel_id = Column(Integer, ForeignKey('channels.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    can_view = Column(Boolean, default=True)
    can_send = Column(Boolean, default=True)
    can_manage = Column(Boolean, default=False)
    channel = relationship("Channel", back_populates="permissions")
    user = relationship("User")

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    channel_id = Column(Integer, ForeignKey('channels.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    channel = relationship("Channel", back_populates="messages")
    user = relationship("User")

# Add this function to check and create missing tables/columns
def check_and_create_tables():
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if 'guilds' not in existing_tables:
        Guild.__table__.create(engine)
    else:
        existing_columns = [c['name'] for c in inspector.get_columns('guilds')]
        if 'created_by' not in existing_columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE guilds ADD COLUMN created_by INTEGER"))

    if 'channels' not in existing_tables:
        Channel.__table__.create(engine)
    
    if 'messages' not in existing_tables:
        Message.__table__.create(engine)
    else:
        existing_columns = [c['name'] for c in inspector.get_columns('messages')]
        if 'user_id' not in existing_columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE messages ADD COLUMN user_id INTEGER"))
        if 'timestamp' not in existing_columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE messages ADD COLUMN timestamp DATETIME"))

    if 'channel_permissions' not in existing_tables:
        ChannelPermission.__table__.create(engine)

    # Add checks for other tables and columns as needed

# Call this function before creating the FastAPI app
check_and_create_tables()

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
        self.user_status: Dict[int, str] = {}
        self.user_channels: Dict[int, Set[int]] = {}  # User ID to set of Channel IDs
        self.user_guilds: Dict[int, Set[int]] = {}  # User ID to set of Guild IDs

    async def connect(self, user_id: int, websocket: WebSocket):
        self.connections[user_id] = websocket
        self.user_status[user_id] = "online"
        await self.send_initial_data(user_id)

    async def disconnect(self, user_id: int):
        if user_id in self.connections:
            del self.connections[user_id]
        if user_id in self.user_status:
            del self.user_status[user_id]
        if user_id in self.user_channels:
            del self.user_channels[user_id]
        if user_id in self.user_guilds:
            del self.user_guilds[user_id]

    async def broadcast_to_channel(self, channel_id: int, message: dict):
        for user_id, channels in self.user_channels.items():
            if channel_id in channels:
                websocket = self.connections.get(user_id)
                if websocket:
                    await websocket.send_json(message)

    async def broadcast_to_guild(self, guild_id: int, message: dict):
        for user_id, guilds in self.user_guilds.items():
            if guild_id in guilds:
                websocket = self.connections.get(user_id)
                if websocket:
                    await websocket.send_json(message)

    async def join_channel(self, user_id: int, channel_id: int):
        self.user_channels.setdefault(user_id, set()).add(channel_id)

    async def leave_channel(self, user_id: int, channel_id: int):
        if user_id in self.user_channels:
            self.user_channels[user_id].discard(channel_id)

    async def join_guild(self, user_id: int, guild_id: int):
        self.user_guilds.setdefault(user_id, set()).add(guild_id)

    async def leave_guild(self, user_id: int, guild_id: int):
        if user_id in self.user_guilds:
            self.user_guilds[user_id].discard(guild_id)

    async def send_initial_data(self, user_id: int):
        websocket = self.connections[user_id]
        with get_db() as db:
            # Send user info
            user = db.query(User).filter(User.id == user_id).first()
            await websocket.send_json({"type": "user_info", "data": user_to_dict(user)})

            # Send user's guilds
            guilds = db.query(Guild).join(GuildMember).filter(GuildMember.user_id == user_id).all()
            guild_data = [guild_to_dict(guild) for guild in guilds]
            await websocket.send_json({"type": "guilds_list", "data": guild_data})

            # For each guild, send channels
            for guild in guilds:
                channels = db.query(Channel).filter(Channel.guild_id == guild.id).all()
                channel_data = [channel_to_dict(channel) for channel in channels]
                await websocket.send_json({"type": "guild_channels", "guild_id": guild.id, "data": channel_data})
                # Update our tracking dictionaries
                for channel in channels:
                    await self.join_channel(user_id, channel.id)
                await self.join_guild(user_id, guild.id)

    async def send_message(self, user_id: int, message: str):
        if user_id in self.connections:
            websocket = self.connections[user_id]
            logger.info(f"Sent: {message}")
            await websocket.send_text(message)

    def set_status(self, user_id: int, status: str):
        self.user_status[user_id] = status

    def get_status(self, user_id: int) -> str:
        return self.user_status.get(user_id, "offline")

websocket_manager = WebSocketManager()

# Dependency
@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        db.rollback()
        raise
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

def extract_token_from_query_params(websocket: WebSocket) -> Optional[str]:
    """Extract the token from WebSocket query parameters."""
    token = websocket.query_params.get("token")
    return token

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
        "owner_id": guild.owner_id,
        "invite_code": guild.invite_code
    }

def channel_to_dict(channel: Channel) -> dict:
    """Convert Channel object to dictionary."""
    return {
        "id": channel.id,
        "name": channel.name,
        "guild_id": channel.guild_id
    }

# Add this function to convert GuildMember to a dictionary
def guild_member_to_dict(guild_member: GuildMember) -> dict:
    return {
        "id": guild_member.user.id,
        "username": guild_member.user.username,
        "display_name": guild_member.user.display_name,
        "avatar_url": guild_member.user.avatar_url,
        "status": websocket_manager.get_status(guild_member.user.id)
    }

# Add this near the top of the file, after imports
logger.add("app.log", rotation="500 MB")

# Simple rate limiting
last_request_time = {}
MIN_REQUEST_INTERVAL = 0.1  # 100ms

def rate_limit(user_id):
    current_time = time.time()
    if user_id in last_request_time:
        time_since_last_request = current_time - last_request_time[user_id]
        if time_since_last_request < MIN_REQUEST_INTERVAL:
            time.sleep(MIN_REQUEST_INTERVAL - time_since_last_request)
    last_request_time[user_id] = time.time()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    logger.info("New WebSocket connection attempt")

    token = extract_token_from_query_params(websocket)
    
    current_user = None
    if token:
        try:
            current_user = get_current_user_from_token(token)
            logger.info(f"User authenticated: {current_user.username}")
        except Exception as e:
            logger.error(f"Token validation failed: {str(e)}")
            await websocket.accept()
            await websocket.send_json({"status": "error", "detail": "Invalid token"})
            await websocket.close(code=1008)
            return
    else:
        logger.warning("No token provided")

    try:
        await websocket.accept()
        if current_user:
            await websocket_manager.connect(current_user.id, websocket)
            logger.info(f"WebSocket connection established for user: {current_user.username}")

        while True:
            data = await websocket.receive_json()
            logger.info(f"Received data: {data}")
            command = data.get("command")
            payload = data.get("payload")

            if current_user:
                rate_limit(current_user.id)

            if command in ["register", "login"]:
                if command == "register":
                    user_data = payload
                    # Ensure correct session usage
                    db = SessionLocal()
                    try:
                        existing_user = db.query(User).filter(User.username == user_data['username']).first()
                        if existing_user:
                            await websocket.send_json({"status": "error", "detail": "Username is already in use"})
                        else:
                            hashed_password = get_password_hash(user_data['password'])
                            db_user = User(username=user_data['username'], email=user_data['email'], hashed_password=hashed_password)
                            db.add(db_user)
                            db.commit()
                            db.refresh(db_user)
                            await websocket.send_json({"status": "success", "user": user_to_dict(db_user)})
                    finally:
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
                        logger.info(f"Sent: Token: Bearer {access_token}")
                        await websocket.send_json({"access_token": access_token, "token_type": "bearer"})

            elif current_user:
                with get_db() as db:
                    if command == "get_user":
                        user = payload['user_id']
                        if user == 'me':
                            await websocket.send_json({"status": "success", "user": user_to_dict(current_user)})
                        elif user == int:
                            await websocket.send_json({"status": "success", "user": user_to_dict(user)})
                        else:
                            await websocket.send_json({"status": "error", "detail": "Invalid payload"})

                    elif command == "update_user":
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
                        invite_code = str(uuid.uuid4())
                        db_guild = Guild(name=payload['name'], owner_id=current_user.id, invite_code=invite_code)
                        db.add(db_guild)
                        db.commit()
                        db.refresh(db_guild)
                        # Add current user to the guild members
                        db_guild_member = GuildMember(guild_id=db_guild.id, user_id=current_user.id)
                        db.add(db_guild_member)
                        db.commit()
                        
                        # Create a guild_data dictionary
                        guild_data = guild_to_dict(db_guild)
                        
                        # Send the guild_created message to the user who created the guild
                        await websocket.send_json({
                            "type": "guild_created",
                            "status": "success",
                            "data": guild_data
                        })
                        
                        # Broadcast to all users (including the creator) that a new guild has been created
                        await websocket_manager.broadcast_to_guild(db_guild.id, {
                            "type": "guild_created",
                            "data": guild_data
                        })
                        
                        # Add the user to the guild's WebSocket manager
                        await websocket_manager.join_guild(current_user.id, db_guild.id)

                    elif command == "get_guild":
                        guild = db.query(Guild).filter(Guild.id == payload['guild_id']).first()
                        if guild is None:
                            await websocket.send_json({"status": "error", "detail": "Guild not found"})
                        else:
                            # Check if the user is a member
                            if not db.query(GuildMember).filter(GuildMember.user_id == current_user.id, GuildMember.guild_id == guild.id).first():
                                await websocket.send_json({"status": "error", "detail": "User is not a member of this guild"})
                            else:
                                guild_data = guild_to_dict(guild)
                                
                                # Fetch guild members
                                guild_members = db.query(GuildMember).filter(GuildMember.guild_id == guild.id).all()
                                members_data = [guild_member_to_dict(member) for member in guild_members]
                                
                                # Fetch guild channels
                                channels = db.query(Channel).filter(Channel.guild_id == guild.id).all()
                                channels_data = [channel_to_dict(channel) for channel in channels]
                                
                                await websocket.send_json({
                                    "status": "success",
                                    "type": "guild_data",
                                    "guild": guild_data,
                                    "members": members_data,
                                    "channels": channels_data
                                })

                    elif command == "delete_guild":
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
                                await websocket_manager.broadcast_to_guild(guild_id, {"type": "guild_deleted", "guild_id": guild_id})

                    elif command == "create_channel":
                        guild_id = payload.get('guild_id')
                        channel_name = payload.get('name')
                        guild = db.query(Guild).filter(Guild.id == guild_id).first()
                        if not guild:
                            await websocket.send_json({"status": "error", "detail": "Guild not found"})
                        elif guild.owner_id != current_user.id:
                            await websocket.send_json({"status": "error", "detail": "Only guild owner can create channels"})
                        else:
                            new_channel = Channel(name=channel_name, guild_id=guild_id)
                            db.add(new_channel)
                            db.commit()
                            db.refresh(new_channel)
                            await websocket.send_json({"status": "success", "channel": channel_to_dict(new_channel)})
                            await websocket_manager.broadcast_to_guild(guild_id, {"type": "channel_created", "data": channel_to_dict(new_channel)})

                    elif command == "delete_channel":
                        channel_id = payload.get('channel_id')
                        channel = db.query(Channel).filter(Channel.id == channel_id).first()
                        if not channel:
                            await websocket.send_json({"status": "error", "detail": "Channel not found"})
                        elif channel.guild.owner_id != current_user.id:
                            await websocket.send_json({"status": "error", "detail": "Only guild owner can delete channels"})
                        else:
                            db.delete(channel)
                            db.commit()
                            await websocket.send_json({"status": "success", "detail": f"Channel {channel.name} deleted successfully"})
                            await websocket_manager.broadcast_to_guild(channel.guild_id, {"type": "channel_deleted", "channel_id": channel_id})

                    elif command == "get_channel":
                        channel_id = payload['channel_id']
                        content = payload['content']
                        channel = db.query(Channel).filter(Channel.id == channel_id).first()
                        if channel is None:
                            await websocket.send_json({"status": "error", "detail": "Channel not found"})
                        else:
                            db_message = Message(content=content, channel_id=channel_id, user_id=current_user.id)
                            db.add(db_message)
                            db.commit()
                            db.refresh(db_message)
                            message_data = {
                                "id": db_message.id,
                                "content": content,
                                "author": user_to_dict(current_user),
                                "timestamp": db_message.timestamp.isoformat()
                            }
                            await websocket.send_json({"status": "success", "message": message_data})
                            #await websocket_manager.broadcast_to_channel(channel_id, {"type": "new_message", "data": message_data})

                    elif command == "update_channel":
                        channel_id = payload['channel_id']
                        channel_update = payload['channel_update']
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

                    elif command == "request_invite":
                        guild_id = payload['guild_id']
                        guild = db.query(Guild).filter(Guild.id == guild_id).first()
                        if guild is None:
                            await websocket.send_json({"status": "error", "detail": "Guild not found"})
                        elif not db.query(GuildMember).filter(GuildMember.user_id == current_user.id, GuildMember.guild_id == guild.id).first():
                            await websocket.send_json({"status": "error", "detail": "User is not a member of this guild"})
                        else:
                            # Generate a new invite code and save who created it
                            guild.invite_code = str(uuid.uuid4())
                            guild.created_by = current_user.id
                            db.commit()
                            await websocket.send_json({"status": "success", "invite_code": guild.invite_code})

                    elif command == "join_guild":
                        invite_code = payload['invite_code']
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
                            guild_data = {
                                "id": guild.id,
                                "name": guild.name,
                                "owner_id": guild.owner_id,
                                "created_by": guild.created_by
                            }
                            await websocket.send_json({"status": "success", "detail": "Joined guild", "guild": guild_data})

                    elif command == "list_user_guilds":
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
                        status = websocket_manager.get_status(user_id)
                        await websocket.send_json({"status": "success", "user_id": user_id, "status": status})
                    elif command == "get_channel_users":
                        channel_id = payload['channel_id']
                        page = payload.get('page', 1)
                        per_page = 100
                        channel = db.query(Channel).filter(Channel.id == channel_id).first()
                        if channel is None:
                            await websocket.send_json({"status": "error", "detail": "Channel not found"})
                        else:
                            permissions_query = db.query(ChannelPermission).filter(ChannelPermission.channel_id == channel_id).order_by(ChannelPermission.user_id)
                            total_users = permissions_query.count()
                            permissions = permissions_query.offset((page - 1) * per_page).limit(per_page).all()
                            user_ids = [perm.user_id for perm in permissions]
                            users = db.query(User).filter(User.id.in_(user_ids)).all()
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
                        per_page = 50

                        # Fetch messages in descending order by timestamp
                        messages_query = db.query(Message).filter(Message.channel_id == channel_id).order_by(Message.timestamp.desc())

                        # Get the total number of messages
                        total_messages = messages_query.count()

                        # Calculate total pages
                        total_pages = (total_messages // per_page) + (1 if total_messages % per_page != 0 else 0)

                        # Fetch messages with pagination (no change needed here since order_by is DESC)
                        messages = messages_query.offset((page - 1) * per_page).limit(per_page).all()

                        # Create message list
                        message_list = [{
                            "id": msg.id,
                            "content": msg.content,
                            "author": user_to_dict(msg.user),
                            "timestamp": msg.timestamp.isoformat()
                        } for msg in messages]

                        # Send the result back to the websocket
                        await websocket.send_json({
                            "status": "success",
                            "page": page,
                            "total_pages": total_pages,
                            "messages": message_list
                        })
                    # Add to the WebSocket command handling
                    elif command == "send_message":
                        channel_id = payload['channel_id']
                        guild_id = payload['guild_id']
                        content = payload['content']
                        channel = db.query(Channel).filter(Channel.id == channel_id).first()
                        if channel is None:
                            await websocket.send_json({"status": "error", "detail": "Channel not found"})
                        else:
                            # Save the message in the database
                            db_message = Message(content=content, channel_id=channel_id, user_id=current_user.id)
                            db.add(db_message)
                            db.commit()
                            db.refresh(db_message)
                            await websocket.send_json({"status": "success", "message": "Success!"})
                            broadcast_data = {
                                "id": db_message.id,
                                "content": content,
                                "author": user_to_dict(current_user),
                                "channel_id": channel_id,
                                "guild_id": guild_id,
                                "timestamp": db_message.timestamp.isoformat(),
                            }
                            await websocket_manager.broadcast_to_channel(channel_id, {"type": "new_message", "data": broadcast_data})

                    elif command == "get_guild_channels":
                        guild_id = payload['guild_id']
                        channels = db.query(Channel).filter(Channel.guild_id == guild_id).all()
                        await websocket.send_json({"status": "success", "channels": [channel_to_dict(channel) for channel in channels]})

            else:
                await websocket.send_json({"status": "error", "detail": "Unauthorized"})
                logger.warning("Unauthorized command received")
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected.")
        #websocket_manager.disconnect(current_user.id)
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket: {str(e)}")
        logger.debug(traceback.format_exc())
        await websocket.close(code=1011)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("websocket:app", host="0.0.0.0", port=8000, reload=True)
