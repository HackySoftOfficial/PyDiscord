from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import chat, guilds, users, roles
from app.database import engine, Base

# Create tables in the database
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router)
app.include_router(guilds.router)
app.include_router(users.router)
app.include_router(roles.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the PyDiscord API"}

# Swagger UI is available by default at /docs
