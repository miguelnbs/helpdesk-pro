from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client
from database import supabase, client_for_token

security = HTTPBearer()


def get_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    return credentials.credentials


# Valida o token JWT e retorna o usuário autenticado
def get_current_user(token: str = Depends(get_token)):
    try:
        response = supabase.auth.get_user(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado"
        )

    if response is None or response.user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado"
        )

    return response.user


# Cliente do banco exclusivo desta requisição, autenticado com o token do usuário
def get_db(token: str = Depends(get_token)) -> Client:
    return client_for_token(token)


# Busca o perfil completo do usuário autenticado
def get_current_profile(current_user=Depends(get_current_user), db: Client = Depends(get_db)):
    try:
        response = db.table("profiles") \
            .select("*") \
            .eq("id", str(current_user.id)) \
            .execute()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao consultar o perfil"
        )

    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil não encontrado"
        )

    return response.data[0]


# Bloqueia o acesso se o usuário não for administrador
def require_admin(profile=Depends(get_current_profile)):
    if profile["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores"
        )
    return profile
