from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from database import new_client

router = APIRouter(prefix="/auth", tags=["auth"])

FRONTEND_RESET_URL = "https://helpdesk-pro-rosy.vercel.app/reset-password"


# --- Modelos ---

class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    access_token: str
    new_password: str


# --- Rotas ---

@router.post("/register")
def register(data: RegisterRequest):
    if len(data.full_name.strip()) < 2:
        raise HTTPException(status_code=400, detail="Informe o nome completo")
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="A senha deve ter pelo menos 6 caracteres")

    try:
        client = new_client()
        response = client.auth.sign_up({
            "email": data.email,
            "password": data.password,
            "options": {"data": {"full_name": data.full_name.strip()}}
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    if response.user is None:
        raise HTTPException(status_code=400, detail="Erro ao criar usuário")

    return {
        "message": "Usuário criado com sucesso",
        "user_id": str(response.user.id),
        "email": response.user.email
    }


@router.post("/login")
def login(data: LoginRequest):
    try:
        client = new_client()
        response = client.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password
        })
    except Exception:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    if response.user is None or response.session is None:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    return {
        "access_token": response.session.access_token,
        "token_type": "bearer",
        "user_id": str(response.user.id),
        "email": response.user.email
    }


@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest):
    try:
        client = new_client()
        client.auth.reset_password_email(
            data.email,
            options={"redirect_to": FRONTEND_RESET_URL}
        )
        return {"message": "Email de recuperação enviado"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest):
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="A senha deve ter pelo menos 6 caracteres")

    try:
        client = new_client()
        client.auth.set_session(data.access_token, data.access_token)
        client.auth.update_user({"password": data.new_password})
        return {"message": "Senha redefinida com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
