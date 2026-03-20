from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from routes import auth, wallet, postback, admin

app = FastAPI()

# ✅ CORS (place here — top)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all (for development)
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
app.include_router(auth.router, prefix="/auth")
app.include_router(wallet.router, prefix="/wallet")
app.include_router(postback.router, prefix="/api")
app.include_router(admin.router, prefix="/admin", tags=["Admin"])

# ✅ Home
@app.get("/")
def home():
    return {"message": "CPA Backend Running 🚀"}