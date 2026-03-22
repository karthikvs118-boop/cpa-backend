

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from backend.database import engine, Base
from backend.routes import auth, wallet, postback, admin

# 🔥 NEW (rate limiting)
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware

# 🔐 Load environment variables
load_dotenv()

app = FastAPI(
    title="CPA Backend",
    description="Secure CPA Tracking System",
    version="1.0.0"
)

# 🔥 ADD THIS (IMPORTANT)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


# ✅ CORS (⚠️ restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://easyearningapp.netlify.app"],  # change later to frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Create tables
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# ✅ Routes
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(wallet.router, prefix="/wallet", tags=["Wallet"])
app.include_router(postback.router, prefix="/api", tags=["Postback"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])

# ✅ Home
@app.get("/")
def home():
    return {"message": "CPA Backend Running 🚀"}

# ✅ Health check
@app.get("/health")
def health():
    return {"status": "ok"}