from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.auth import router as auth_router
from routers.profile import router as profile_router
from routers.tickets import router as tickets_router
from routers.admin import router as admin_router

app = FastAPI(
    title="HelpDesk Pro API",
    description="API do sistema de chamados técnicos",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(tickets_router)
app.include_router(admin_router)


@app.get("/health")
def health_check():
    return {"status": "online", "service": "HelpDesk Pro API"}
