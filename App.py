from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pymongo import MongoClient

# Replace these with your PostgreSQL and MongoDB connection details
POSTGRES_DATABASE_URL = "postgresql://username:password@localhost/dbname"
MONGO_DATABASE_URL = "mongodb://username:password@localhost:27017/"

# Create the FastAPI app
app = FastAPI()

# SQLAlchemy database setup
engine = create_engine(POSTGRES_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define SQLAlchemy model for User
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    phone = Column(String)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)

# Pydantic models for request and response
class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str
    phone: str

class UserResponse(BaseModel):
    user_id: int
    full_name: str
    email: str
    phone: str

# MongoDB setup
mongo_client = MongoClient(MONGO_DATABASE_URL)
mongo_db = mongo_client["user_profiles"]
profile_collection = mongo_db["profiles"]

# User registration route
@app.post("/register/", response_model=UserResponse)
async def register_user(user: UserCreate):
    db = SessionLocal()
    
    # Check if email already exists
    existing_user_email = db.query(User).filter(User.email == user.email).first()
    
    if existing_user_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create a profile document in MongoDB
    profile_data = {
        "user_id": db_user.id,
        "profile_picture": ""  # You can set this to the profile picture URL later
    }
    profile_collection.insert_one(profile_data)
    
    db.close()
    
    return {"user_id": db_user.id, **user.dict()}

# Get user details route
@app.get("/user/{user_id}/", response_model=UserResponse)
async def get_user(user_id: int):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    db.close()
    
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Retrieve profile picture from MongoDB
    profile_data = profile_collection.find_one({"user_id": user_id})
    if profile_data:
        user_data = user.__dict__
        user_data.pop("_sa_instance_state")
        user_data["user_id"] = user.id
        user_data["profile_picture"] = profile_data.get("profile_picture", "")
        return user_data
    
    return user.__dict__

# Run the FastAPI application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
