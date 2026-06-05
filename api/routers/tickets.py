from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from database import supabase
from middlewares.auth import get_current_profile, require_admin

router = APIRouter(prefix="/tickets", tags=["tickets"])

# --- Modelos ---

class TicketRequest(BaseModel):
    title: str
    description: str
    category: str
    priority: Optional[str] = "low"

class TicketUpdateRequest(BaseModel):
    message: str

class TicketStatusRequest(BaseModel):
    status: str

# --- Rotas ---

@router.post("")
def create_ticket(data: TicketRequest, profile=Depends(get_current_profile)):
    try:
        result = supabase.table("tickets").insert({
            "title": data.title,
            "description": data.description,
            "category": data.category,
            "priority": data.priority,
            "status": "open",
            "created_by": profile["id"]
        }).execute()

        return {"message": "Chamado aberto com sucesso", "ticket": result.data[0]}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("")
def list_my_tickets(profile=Depends(get_current_profile)):
    try:
        result = supabase.table("tickets") \
            .select("*") \
            .eq("created_by", profile["id"]) \
            .order("created_at", desc=True) \
            .execute()

        return {"tickets": result.data}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/all")
def list_all_tickets(profile=Depends(require_admin)):
    try:
        result = supabase.table("tickets") \
            .select("*, profiles!tickets_created_by_fkey(full_name, sector)") \
            .order("created_at", desc=True) \
            .execute()

        return {"tickets": result.data}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{ticket_id}")
def get_ticket(ticket_id: str, profile=Depends(get_current_profile)):
    try:
        result = supabase.table("tickets") \
            .select("*, ticket_updates(*)") \
            .eq("id", ticket_id) \
            .single() \
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Chamado não encontrado")

        ticket = result.data

        # usuário comum só pode ver seus próprios chamados
        if profile["role"] != "admin" and ticket["created_by"] != profile["id"]:
            raise HTTPException(status_code=403, detail="Acesso negado")

        return ticket

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{ticket_id}/status")
def update_status(ticket_id: str, data: TicketStatusRequest, profile=Depends(require_admin)):
    valid_statuses = ["open", "in_progress", "waiting", "resolved", "cancelled"]

    if data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status inválido. Use: {valid_statuses}")

    try:
        update_data = {"status": data.status}

        if data.status == "resolved":
            from datetime import datetime, timezone
            update_data["resolved_at"] = datetime.now(timezone.utc).isoformat()

        result = supabase.table("tickets") \
            .update(update_data) \
            .eq("id", ticket_id) \
            .execute()

        return {"message": "Status atualizado com sucesso", "ticket": result.data[0]}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{ticket_id}/updates")
def add_update(ticket_id: str, data: TicketUpdateRequest, profile=Depends(get_current_profile)):
    try:
        result = supabase.table("ticket_updates").insert({
            "ticket_id": ticket_id,
            "author_id": profile["id"],
            "message": data.message
        }).execute()

        return {"message": "Resposta adicionada com sucesso", "update": result.data[0]}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))