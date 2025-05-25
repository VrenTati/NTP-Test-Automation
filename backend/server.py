import openai
import google.generativeai as genai
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import base64
import uuid
import json
import asyncio
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pymongo import MongoClient
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Currency Recognition API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Database
client = MongoClient(os.getenv("MONGO_URL"))
db = client.currency_recognition
users_collection = db.users
analysis_collection = db.analysis

# Models
class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    username: str
    password: str

class User(BaseModel):
    username: str

class CurrencyDetection(BaseModel):
    currency_type: str
    denomination: str
    quantity: int
    confidence: str

class AnalysisResult(BaseModel):
    id: str
    openai_result: dict
    gemini_result: dict
    timestamp: datetime
    user_id: str
    combined_analysis: dict

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = users_collection.find_one({"username": username})
    if user is None:
        raise credentials_exception
    return user

def convert_image_to_base64(image_bytes):
    return base64.b64encode(image_bytes).decode('utf-8')

# AI Integration functions
async def analyze_with_openai(image_base64: str):
    try:
        chat = LlmChat(
            api_key=os.getenv("OPENAI_API_KEY"),
            session_id=f"openai-currency-{uuid.uuid4()}",
            system_message="You are a currency recognition expert. Analyze images of banknotes and coins to identify currency type, denomination, and quantity. Focus on UAH (Ukrainian Hryvnia), USD (US Dollar), and EUR (Euro). Return structured JSON responses."
        ).with_model("openai", "gpt-4o-mini")

        image_content = ImageContent(image_base64=image_base64)
        
        user_message = UserMessage(
            text="""Analyze this image of currency (banknotes/coins) and return a JSON response with:
            {
                "currencies_detected": [
                    {
                        "currency_type": "UAH/USD/EUR/etc",
                        "denomination": "value as string",
                        "quantity": number,
                        "confidence": "high/medium/low"
                    }
                ],
                "total_value": "calculated total if same currency type",
                "notes": "any additional observations",
                "provider": "OpenAI GPT-4o-mini"
            }""",
            file_contents=[image_content]
        )
        
        response = await chat.send_message(user_message)
        
        # Try to parse JSON, if fails return raw response
        try:
            return json.loads(response)
        except:
            return {"raw_response": response, "provider": "OpenAI GPT-4o-mini"}
            
    except Exception as e:
        return {"error": str(e), "provider": "OpenAI GPT-4o-mini"}

async def analyze_with_gemini(image_base64: str):
    try:
        chat = LlmChat(
            api_key=os.getenv("GEMINI_API_KEY"),
            session_id=f"gemini-currency-{uuid.uuid4()}",
            system_message="You are a currency recognition expert. Analyze images of banknotes and coins to identify currency type, denomination, and quantity. Focus on UAH (Ukrainian Hryvnia), USD (US Dollar), and EUR (Euro). Return structured JSON responses."
        ).with_model("gemini", "gemini-2.0-flash")

        image_content = ImageContent(image_base64=image_base64)
        
        user_message = UserMessage(
            text="""Analyze this image of currency (banknotes/coins) and return a JSON response with:
            {
                "currencies_detected": [
                    {
                        "currency_type": "UAH/USD/EUR/etc",
                        "denomination": "value as string",
                        "quantity": number,
                        "confidence": "high/medium/low"
                    }
                ],
                "total_value": "calculated total if same currency type",
                "notes": "any additional observations",
                "provider": "Google Gemini 2.0 Flash"
            }""",
            file_contents=[image_content]
        )
        
        response = await chat.send_message(user_message)
        
        # Try to parse JSON, if fails return raw response
        try:
            return json.loads(response)
        except:
            return {"raw_response": response, "provider": "Google Gemini 2.0 Flash"}
            
    except Exception as e:
        return {"error": str(e), "provider": "Google Gemini 2.0 Flash"}

def combine_ai_results(openai_result: dict, gemini_result: dict):
    """Combine and compare results from both AI providers"""
    combined = {
        "comparison": "dual_ai_analysis",
        "openai_summary": openai_result,
        "gemini_summary": gemini_result,
        "consensus": {},
        "discrepancies": []
    }
    
    # Try to find consensus between the two results
    openai_currencies = openai_result.get('currencies_detected', [])
    gemini_currencies = gemini_result.get('currencies_detected', [])
    
    if openai_currencies and gemini_currencies:
        # Basic consensus logic
        if len(openai_currencies) == len(gemini_currencies):
            combined["consensus"]["currency_count_match"] = True
        else:
            combined["discrepancies"].append("Different number of currencies detected")
    
    return combined

# API Routes
@app.post("/api/register", response_model=Token)
async def register(user: UserCreate):
    # Check if user already exists
    if users_collection.find_one({"username": user.username}):
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Create new user
    hashed_password = get_password_hash(user.password)
    user_doc = {
        "username": user.username,
        "hashed_password": hashed_password,
        "created_at": datetime.utcnow()
    }
    users_collection.insert_one(user_doc)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/login", response_model=Token)
async def login(user: UserCreate):
    # Authenticate user
    db_user = users_collection.find_one({"username": user.username})
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/analyze-currency")
async def analyze_currency(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read and convert image
        image_bytes = await file.read()
        image_base64 = convert_image_to_base64(image_bytes)
        
        # Analyze with both AI providers in parallel
        openai_task = analyze_with_openai(image_base64)
        gemini_task = analyze_with_gemini(image_base64)
        
        openai_result, gemini_result = await asyncio.gather(openai_task, gemini_task)
        
        # Combine results
        combined_analysis = combine_ai_results(openai_result, gemini_result)
        
        # Store in database
        analysis_doc = {
            "id": str(uuid.uuid4()),
            "user_id": current_user["username"],
            "openai_result": openai_result,
            "gemini_result": gemini_result,
            "combined_analysis": combined_analysis,
            "timestamp": datetime.utcnow(),
            "filename": file.filename
        }
        
        analysis_collection.insert_one(analysis_doc)
        
        return {
            "analysis_id": analysis_doc["id"],
            "openai_result": openai_result,
            "gemini_result": gemini_result,
            "combined_analysis": combined_analysis,
            "timestamp": analysis_doc["timestamp"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analysis/{analysis_id}")
async def get_analysis(
    analysis_id: str,
    current_user: dict = Depends(get_current_user)
):
    analysis = analysis_collection.find_one({
        "id": analysis_id,
        "user_id": current_user["username"]
    })
    
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Remove MongoDB _id field
    analysis.pop('_id', None)
    return analysis

@app.get("/api/analysis")
async def get_user_analyses(
    current_user: dict = Depends(get_current_user)
):
    analyses = list(analysis_collection.find(
        {"user_id": current_user["username"]},
        {"_id": 0}  # Exclude MongoDB _id field
    ).sort("timestamp", -1).limit(10))
    
    return {"analyses": analyses}

@app.post("/api/webhook/{analysis_id}")
async def webhook_analysis_result(analysis_id: str):
    """Webhook endpoint for real-time updates (placeholder for future implementation)"""
    analysis = analysis_collection.find_one({"id": analysis_id})
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # In a real implementation, this would trigger a webhook to the frontend
    return {"message": "Webhook triggered", "analysis_id": analysis_id}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "Currency Recognition API"}

@app.get("/")
async def root():
    return {"message": "Currency Recognition API", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
