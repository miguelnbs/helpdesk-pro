# HelpDesk Pro — Etapas 1 e 2: Setup, Banco e Autenticação

## Visão geral do projeto

Sistema interno de abertura e gestão de chamados técnicos, com painel administrativo, controle de SLA, histórico de interações e dashboard operacional.

**Stack completa do projeto:**

| Camada | Tecnologia |
|---|---|
| Frontend | React + TypeScript + Vite + Tailwind + shadcn/ui |
| API | Python + FastAPI |
| Banco de dados | Supabase (PostgreSQL) |
| Autenticação | Supabase Auth |
| Dashboard | Python + Streamlit |
| Deploy | Vercel (front) + Railway (API) + Streamlit Cloud (dashboard) |

---

## Arquitetura

```
┌─────────────────┐        ┌─────────────────┐
│   React (front) │◄──────►│  FastAPI (back) │
│   Vercel        │  REST  │  Railway        │
└─────────────────┘        └────────┬────────┘
                                    │
                           ┌────────▼────────┐
                           │    Supabase     │
                           │  PostgreSQL     │
                           └────────┬────────┘
                                    │
                           ┌────────▼────────┐
                           │   Streamlit     │
                           │   Dashboard     │
                           │ Streamlit Cloud │
                           └─────────────────┘
```

---

## Estrutura de pastas

```
helpdesk-pro/
├── api/
│   ├── venv/                  ← ambiente virtual (não subir no git)
│   ├── routers/
│   │   ├── __init__.py
│   │   └── auth.py            ← rotas de cadastro e login
│   ├── middlewares/
│   │   ├── __init__.py
│   │   └── auth.py            ← validação JWT e controle de perfil
│   ├── .env                   ← variáveis de ambiente (não subir no git)
│   ├── main.py                ← entrypoint da API
│   ├── database.py            ← conexão com Supabase
│   └── requirements.txt       ← dependências Python
└── frontend/                  ← React (próximas etapas)
```

---

## .gitignore recomendado

```
venv/
.env
__pycache__/
*.pyc
.DS_Store
node_modules/
dist/
```

---

# Etapa 1 — Setup, Banco e Conexão

## Pré-requisitos

- Python instalado (3.10+)
- Node.js instalado
- Conta no [Supabase](https://supabase.com)

---

## Passo 1 — Criar a estrutura de pastas

```bash
mkdir helpdesk-pro
cd helpdesk-pro
mkdir api frontend
```

---

## Passo 2 — Criar e ativar o ambiente virtual Python

```bash
cd api

# Criar
python -m venv venv

# Ativar — Windows
venv\Scripts\activate

# Ativar — Mac/Linux
source venv/bin/activate
```

O `(venv)` no início do terminal confirma que está ativo.

---

## Passo 3 — Instalar dependências

```bash
pip install fastapi uvicorn python-dotenv supabase
pip freeze > requirements.txt
```

---

## Passo 4 — Criar o arquivo `main.py`

```python
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from database import supabase
from routers.auth import router as auth_router
from middlewares.auth import get_current_profile

app = FastAPI(
    title="HelpDesk Pro API",
    description="API do sistema de chamados técnicos",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restringir ao domínio do front em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# routers
app.include_router(auth_router)

@app.get("/health")
def health_check():
    return {
        "status": "online",
        "service": "HelpDesk Pro API"
    }

@app.get("/me")
def get_me(profile=Depends(get_current_profile)):
    return profile
```

---

## Passo 5 — Criar o arquivo `.env`

Na pasta `api`, no mesmo nível do `main.py` e **fora da pasta `venv`**:

```
SUPABASE_URL=https://xxxxxxxxxxx.supabase.co
SUPABASE_KEY=sua_anon_key_aqui
```

> **Onde encontrar:** Painel do Supabase → Settings → API → Project URL e anon/public key.

> **Atenção:** o `.env` deve ficar dentro de `api/`, nunca dentro de `venv/`.

---

## Passo 6 — Criar o arquivo `database.py`

```python
import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
```

> O `Path(__file__).parent` garante que o `.env` seja encontrado independentemente de onde o uvicorn é iniciado.

---

## Passo 7 — Subir o servidor

```bash
uvicorn main:app --reload
```

Rotas disponíveis:
- `http://localhost:8000/health` → status da API
- `http://localhost:8000/docs` → documentação automática (Swagger UI)

---

## Passo 8 — Criar as tabelas no Supabase

No painel do Supabase → **SQL Editor**, execute:

```sql
-- Tabela de perfis de usuário
CREATE TABLE profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  full_name TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user', -- 'user' ou 'admin'
  sector TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de chamados
CREATE TABLE tickets (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  category TEXT NOT NULL,
  priority TEXT NOT NULL DEFAULT 'low', -- low, medium, high, critical
  status TEXT NOT NULL DEFAULT 'open', -- open, in_progress, waiting, resolved, cancelled
  created_by UUID REFERENCES profiles(id) NOT NULL,
  assigned_to UUID REFERENCES profiles(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  resolved_at TIMESTAMPTZ
);

-- Tabela de atualizações/histórico dos chamados
CREATE TABLE ticket_updates (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  ticket_id UUID REFERENCES tickets(id) ON DELETE CASCADE NOT NULL,
  author_id UUID REFERENCES profiles(id) NOT NULL,
  message TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Passo 9 — Criar o trigger de perfil automático

Ainda no **SQL Editor**, execute:

```sql
-- Função que cria o perfil automaticamente após cadastro
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, full_name, role)
  VALUES (
    NEW.id,
    COALESCE(NEW.raw_user_meta_data->>'full_name', 'Usuário'),
    'user'
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger que dispara a função após novo usuário
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
```

> A partir daqui, todo usuário criado via Supabase Auth terá um perfil criado automaticamente na tabela `profiles`.

---

## Resultado da Etapa 1

```
✅ Projeto estruturado em camadas (api / frontend)
✅ Ambiente virtual Python configurado
✅ FastAPI rodando com documentação automática em /docs
✅ Supabase conectado via supabase-py
✅ Variáveis de ambiente carregadas corretamente com python-dotenv
✅ Banco modelado com 3 tabelas: profiles, tickets, ticket_updates
✅ Trigger de criação automática de perfil configurado
```

---

# Etapa 2 — Autenticação

## Fluxo de autenticação

```
Cadastro → Supabase Auth cria user → trigger cria perfil em profiles
Login    → Supabase Auth valida    → retorna JWT
Rotas protegidas → FastAPI valida JWT → libera ou bloqueia
```

---

## Passo 1 — Criar as pastas de routers e middlewares

```bash
# Windows
mkdir routers
mkdir middlewares
type nul > routers\__init__.py
type nul > middlewares\__init__.py
```

---

## Passo 2 — Instalar dependência de validação de email

```bash
pip install "pydantic[email]"
pip freeze > requirements.txt
```

---

## Passo 3 — Criar o arquivo `routers/auth.py`

```python
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
```

---

## Passo 4 — Criar o arquivo `middlewares/auth.py`

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import supabase

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    try:
        response = supabase.auth.get_user(token)

        if response.user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido ou expirado"
            )

        return response.user

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado"
        )


def get_current_profile(current_user=Depends(get_current_user)):
    try:
        response = supabase.table("profiles") \
            .select("*") \
            .eq("id", str(current_user.id)) \
            .single() \
            .execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil não encontrado"
            )

        return response.data

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil não encontrado"
        )


def require_admin(profile=Depends(get_current_profile)):
    if profile["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores"
        )
    return profile
```

**O que cada função faz:**

- `get_current_user` — valida o JWT e retorna o usuário autenticado
- `get_current_profile` — busca o perfil completo na tabela `profiles`
- `require_admin` — bloqueia a rota se o usuário não for admin

---

## Resultado da Etapa 2

```
✅ Rota POST /auth/register — cadastro com Supabase Auth
✅ Rota POST /auth/login — login com retorno de JWT
✅ Trigger criando perfil automaticamente no cadastro
✅ Middleware get_current_user — valida JWT em rotas protegidas
✅ Middleware get_current_profile — retorna perfil completo
✅ Middleware require_admin — bloqueia rotas para não admins
✅ Rota GET /me — autenticação funcionando end to end
```

---

# Próxima etapa

**Etapa 3 — Rotas de chamados (tickets)**

| Rota | Método | Descrição |
|---|---|---|
| `/tickets` | POST | Abrir novo chamado |
| `/tickets` | GET | Listar chamados do usuário |
| `/tickets/{id}` | GET | Ver detalhes de um chamado |
| `/tickets/{id}/status` | PATCH | Atualizar status (admin) |
| `/tickets/{id}/updates` | POST | Adicionar resposta ao chamado |
| `/tickets/all` | GET | Listar todos os chamados (admin) |
