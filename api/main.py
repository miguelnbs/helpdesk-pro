from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import supabase
from routers.auth import router as auth_router
from middlewares.auth import get_current_profile
from fastapi import FastAPI, Depends
from routers.tickets import router as tickets_router
from routers.admin import router as admin_router



app = FastAPI(
    title="HelpDesk Pro API",
    description="API do sistema de chamados técnicos",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# routers
app.include_router(auth_router)
app.include_router(tickets_router)
app.include_router(admin_router)

@app.get("/health")
def health_check():
    return {
        "status": "online",
        "service": "HelpDesk Pro API"
    }
    
@app.get("/me")
def get_me(profile=Depends(get_current_profile)):
    return profile


