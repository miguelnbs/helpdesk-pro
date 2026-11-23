from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from supabase import Client
from middlewares.auth import get_current_user, get_current_profile, get_db

router = APIRouter(tags=["profile"])


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=100)
    sector: Optional[str] = Field(default=None, max_length=60)


# Perfil do usuário autenticado (inclui o e-mail, que vem do Supabase Auth)
@router.get("/me")
def get_me(current_user=Depends(get_current_user), profile=Depends(get_current_profile)):
    return {**profile, "email": current_user.email}


# Atualização do próprio perfil — só nome e setor; a role nunca é alterada por aqui
@router.patch("/me")
def update_me(
    data: ProfileUpdateRequest,
    current_user=Depends(get_current_user),
    profile=Depends(get_current_profile),
    db: Client = Depends(get_db),
):
    changes = data.model_dump(exclude_unset=True)

    if "full_name" in changes:
        name = (changes["full_name"] or "").strip()
        if len(name) < 2:
            raise HTTPException(status_code=400, detail="O nome deve ter pelo menos 2 caracteres")
        changes["full_name"] = name

    if "sector" in changes:
        changes["sector"] = (changes["sector"] or "").strip() or None

    if not changes:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    try:
        result = db.table("profiles").update(changes).eq("id", profile["id"]).execute()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not result.data:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")

    return {**result.data[0], "email": current_user.email}
