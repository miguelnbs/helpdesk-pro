from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from database import supabase

router = APIRouter(prefix="/auth", tags=["auth"])

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
    try:
        response = supabase.auth.sign_up({
            "email": data.email,
            "password": data.password,
            "options": {
                "data": {
                    "full_name": data.full_name
                }
            }
        })

        if response.user is None:
            raise HTTPException(status_code=400, detail="Erro ao criar usuário")

        return {
            "message": "Usuário criado com sucesso",
            "user_id": str(response.user.id),
            "email": response.user.email
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
def login(data: LoginRequest):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password
        })

        if response.user is None:
            raise HTTPException(status_code=401, detail="Credenciais inválidas")

        return {
            "access_token": response.session.access_token,
            "token_type": "bearer",
            "user_id": str(response.user.id),
            "email": response.user.email
        }

    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
    
@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest):
    try:
        supabase.auth.reset_password_email(
            data.email,
            options={"redirect_to": "https://helpdesk-pro-rosy.vercel.app/reset-password"}
        )
        return {"message": "Email de recuperação enviado"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest):
    try:
        supabase.auth.set_session(data.access_token, data.access_token)
        supabase.auth.update_user({"password": data.new_password})
        return {"message": "Senha redefinida com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))    