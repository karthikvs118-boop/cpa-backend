from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import engine, Base
from backend.routes import auth, wallet, postback, admin

app = FastAPI()

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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