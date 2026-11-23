from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from supabase import Client
from middlewares.auth import require_admin, get_db

router = APIRouter(prefix="/admin", tags=["admin"])

VALID_ROLES = ["user", "admin"]


class AssignTicketRequest(BaseModel):
    assigned_to: str

class UpdateUserRoleRequest(BaseModel):
    role: str


# --- Listar todos os usuários ---

@router.get("/users")
def list_users(profile=Depends(require_admin), db: Client = Depends(get_db)):
    try:
        result = db.table("profiles") \
            .select("*") \
            .order("created_at", desc=True) \
            .execute()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"users": result.data}


# --- Atualizar role do usuário ---

@router.patch("/users/{user_id}/role")
def update_user_role(user_id: str, data: UpdateUserRoleRequest, profile=Depends(require_admin), db: Client = Depends(get_db)):
    if data.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail=f"Role inválida. Use: {VALID_ROLES}")

    if user_id == profile["id"]:
        raise HTTPException(status_code=400, detail="Você não pode alterar a sua própria role")

    try:
        result = db.table("profiles").update({"role": data.role}).eq("id", user_id).execute()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not result.data:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return {"message": "Role atualizada com sucesso", "user": result.data[0]}


# --- Atribuir chamado a um técnico ---

@router.patch("/tickets/{ticket_id}/assign")
def assign_ticket(ticket_id: str, data: AssignTicketRequest, profile=Depends(require_admin), db: Client = Depends(get_db)):
    try:
        target = db.table("profiles").select("id").eq("id", data.assigned_to).execute()
        if not target.data:
            raise HTTPException(status_code=404, detail="Técnico não encontrado")

        result = db.table("tickets").update({"assigned_to": data.assigned_to}).eq("id", ticket_id).execute()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not result.data:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")

    return {"message": "Chamado atribuído com sucesso", "ticket": result.data[0]}


# --- Estatísticas gerais ---

@router.get("/stats")
def get_stats(profile=Depends(require_admin), db: Client = Depends(get_db)):
    try:
        tickets = db.table("tickets").select("status, priority, created_at, resolved_at").execute()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    data = tickets.data
    stats = {"total": len(data), "by_status": {}, "by_priority": {}}

    for ticket in data:
        s = ticket["status"]
        p = ticket["priority"]
        stats["by_status"][s] = stats["by_status"].get(s, 0) + 1
        stats["by_priority"][p] = stats["by_priority"].get(p, 0) + 1

    return stats
