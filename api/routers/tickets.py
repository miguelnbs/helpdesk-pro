from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from supabase import Client
from middlewares.auth import get_current_profile, require_admin, get_db

router = APIRouter(prefix="/tickets", tags=["tickets"])

VALID_STATUSES = ["open", "in_progress", "waiting", "resolved", "cancelled"]
VALID_PRIORITIES = ["low", "medium", "high", "critical"]


# --- Modelos ---

class TicketRequest(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    description: str = Field(min_length=3)
    category: str = Field(min_length=2, max_length=50)
    priority: Optional[str] = "low"

class TicketUpdateRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)

class TicketStatusRequest(BaseModel):
    status: str


# --- Criar chamado (Create) ---

@router.post("")
def create_ticket(data: TicketRequest, profile=Depends(get_current_profile), db: Client = Depends(get_db)):
    if data.priority not in VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail=f"Prioridade inválida. Use: {VALID_PRIORITIES}")

    try:
        result = db.table("tickets").insert({
            "title": data.title.strip(),
            "description": data.description.strip(),
            "category": data.category.strip(),
            "priority": data.priority,
            "status": "open",
            "created_by": profile["id"]
        }).execute()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": "Chamado aberto com sucesso", "ticket": result.data[0]}


# --- Listar chamados (Read) ---

@router.get("")
def list_my_tickets(profile=Depends(get_current_profile), db: Client = Depends(get_db)):
    try:
        result = db.table("tickets") \
            .select("*") \
            .eq("created_by", profile["id"]) \
            .order("created_at", desc=True) \
            .execute()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"tickets": result.data}


@router.get("/all")
def list_all_tickets(profile=Depends(require_admin), db: Client = Depends(get_db)):
    try:
        result = db.table("tickets") \
            .select("*, profiles!tickets_created_by_fkey(full_name, sector)") \
            .order("created_at", desc=True) \
            .execute()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"tickets": result.data}


@router.get("/{ticket_id}")
def get_ticket(ticket_id: str, profile=Depends(get_current_profile), db: Client = Depends(get_db)):
    try:
        result = db.table("tickets") \
            .select("*, ticket_updates(*)") \
            .eq("id", ticket_id) \
            .execute()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not result.data:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")

    ticket = result.data[0]

    # usuário comum só pode ver os próprios chamados
    if profile["role"] != "admin" and ticket["created_by"] != profile["id"]:
        raise HTTPException(status_code=403, detail="Acesso negado")

    ticket["ticket_updates"] = sorted(
        ticket.get("ticket_updates") or [],
        key=lambda u: u["created_at"]
    )
    return ticket


# --- Atualizar chamado (Update) ---

@router.patch("/{ticket_id}/status")
def update_status(ticket_id: str, data: TicketStatusRequest, profile=Depends(require_admin), db: Client = Depends(get_db)):
    if data.status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail=f"Status inválido. Use: {VALID_STATUSES}")

    now = datetime.now(timezone.utc).isoformat()
    update_data = {"status": data.status, "updated_at": now}
    if data.status == "resolved":
        update_data["resolved_at"] = now

    try:
        result = db.table("tickets").update(update_data).eq("id", ticket_id).execute()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not result.data:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")

    return {"message": "Status atualizado com sucesso", "ticket": result.data[0]}


@router.post("/{ticket_id}/updates")
def add_update(ticket_id: str, data: TicketUpdateRequest, profile=Depends(get_current_profile), db: Client = Depends(get_db)):
    try:
        # o RLS só deixa enxergar chamados do próprio usuário (ou todos, se admin)
        exists = db.table("tickets").select("id").eq("id", ticket_id).execute()
        if not exists.data:
            raise HTTPException(status_code=404, detail="Chamado não encontrado")

        result = db.table("ticket_updates").insert({
            "ticket_id": ticket_id,
            "author_id": profile["id"],
            "message": data.message.strip()
        }).execute()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"message": "Resposta adicionada com sucesso", "update": result.data[0]}


# --- Excluir chamado (Delete) ---

@router.delete("/{ticket_id}")
def delete_ticket(ticket_id: str, profile=Depends(require_admin), db: Client = Depends(get_db)):
    try:
        result = db.table("tickets").delete().eq("id", ticket_id).execute()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not result.data:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")

    # o histórico (ticket_updates) é removido junto, por ON DELETE CASCADE
    return {"message": "Chamado excluído com sucesso"}
