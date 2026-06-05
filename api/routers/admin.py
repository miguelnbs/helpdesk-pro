from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from database import supabase
from middlewares.auth import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])

class AssignTicketRequest(BaseModel):
    assigned_to: str

class UpdateUserRoleRequest(BaseModel):
    role: str

# --- Listar todos os usuários ---

@router.get("/users")
def list_users(profile=Depends(require_admin)):
    try:
        result = supabase.table("profiles") \
            .select("*") \
            .order("created_at", desc=True) \
            .execute()
        return {"users": result.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Atualizar role do usuário ---

@router.patch("/users/{user_id}/role")
def update_user_role(user_id: str, data: UpdateUserRoleRequest, profile=Depends(require_admin)):
    valid_roles = ["user", "admin"]
    if data.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Role inválida. Use: {valid_roles}")
    try:
        result = supabase.table("profiles") \
            .update({"role": data.role}) \
            .eq("id", user_id) \
            .execute()
        return {"message": "Role atualizada com sucesso", "user": result.data[0]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Atribuir chamado a um técnico ---

@router.patch("/tickets/{ticket_id}/assign")
def assign_ticket(ticket_id: str, data: AssignTicketRequest, profile=Depends(require_admin)):
    try:
        result = supabase.table("tickets") \
            .update({"assigned_to": data.assigned_to}) \
            .eq("id", ticket_id) \
            .execute()
        return {"message": "Chamado atribuído com sucesso", "ticket": result.data[0]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Estatísticas gerais ---

@router.get("/stats")
def get_stats(profile=Depends(require_admin)):
    try:
        tickets = supabase.table("tickets").select("status, priority, created_at, resolved_at").execute()
        data = tickets.data

        stats = {
            "total": len(data),
            "by_status": {},
            "by_priority": {}
        }

        for ticket in data:
            s = ticket["status"]
            p = ticket["priority"]
            stats["by_status"][s] = stats["by_status"].get(s, 0) + 1
            stats["by_priority"][p] = stats["by_priority"].get(p, 0) + 1

        return stats

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))