# HelpDesk Pro

Sistema interno de abertura e gestão de chamados técnicos, com painel administrativo, controle de SLA, histórico de interações e dashboard operacional.

> 🚧 **Projeto em desenvolvimento ativo.** As etapas concluídas estão documentadas abaixo. As etapas em andamento serão adicionadas conforme forem finalizadas.

---

## Status do projeto

| Etapa | Descrição | Status |
|---|---|---|
| 1 | Setup, banco e conexão | ✅ Concluída |
| 2 | Autenticação e middlewares | ✅ Concluída |
| 3 | Rotas de chamados (tickets) | ✅ Concluída |
| 4 | Rotas administrativas | ✅ Concluída |
| 5 | Dashboard Streamlit | ✅ Concluída |
| 6 | Frontend React | 🚧 Em desenvolvimento |
| 7 | Deploy completo | 🚧 Em desenvolvimento |

---

## Visão geral

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
│   ├── venv/
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── tickets.py
│   │   └── admin.py
│   ├── middlewares/
│   │   ├── __init__.py
│   │   └── auth.py
│   ├── .env
│   ├── .env.example
│   ├── main.py
│   ├── database.py
│   └── requirements.txt
├── dashboard/
│   ├── venv/
│   ├── .env
│   ├── requirements.txt
│   └── app.py
└── frontend/              ← em desenvolvimento
```

---

## .gitignore

```
venv/
.env
__pycache__/
*.pyc
*.pyo
.DS_Store
node_modules/
dist/
```

---

# ✅ Etapa 1 — Setup, Banco e Conexão

## Pré-requisitos

- Python instalado (3.10+)
- Node.js instalado
- Conta no [Supabase](https://supabase.com)

## Passo 1 — Criar a estrutura de pastas

```bash
mkdir helpdesk-pro
cd helpdesk-pro
mkdir api frontend dashboard
```

## Passo 2 — Criar e ativar o ambiente virtual Python

```bash
cd api
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

## Passo 3 — Instalar dependências

```bash
pip install fastapi uvicorn python-dotenv supabase "pydantic[email]"
pip freeze > requirements.txt
```

## Passo 4 — Criar o arquivo `database.py`

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

## Passo 5 — Criar o arquivo `.env`

```
SUPABASE_URL=https://xxxxxxxxxxx.supabase.co
SUPABASE_KEY=sua_anon_key_aqui
```

> O `.env` deve ficar dentro de `api/`, nunca dentro de `venv/`.

## Passo 6 — Criar o arquivo `main.py`

```python
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from routers.auth import router as auth_router
from routers.tickets import router as tickets_router
from routers.admin import router as admin_router
from middlewares.auth import get_current_profile

app = FastAPI(
    title="HelpDesk Pro API",
    description="API do sistema de chamados técnicos",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(tickets_router)
app.include_router(admin_router)

@app.get("/health")
def health_check():
    return {"status": "online", "service": "HelpDesk Pro API"}

@app.get("/me")
def get_me(profile=Depends(get_current_profile)):
    return profile
```

## Passo 7 — Criar as tabelas no Supabase

```sql
CREATE TABLE profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  full_name TEXT NOT NULL,
  role TEXT NOT NULL DEFAULT 'user',
  sector TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE tickets (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  category TEXT NOT NULL,
  priority TEXT NOT NULL DEFAULT 'low',
  status TEXT NOT NULL DEFAULT 'open',
  created_by UUID REFERENCES profiles(id) NOT NULL,
  assigned_to UUID REFERENCES profiles(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  resolved_at TIMESTAMPTZ
);

CREATE TABLE ticket_updates (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  ticket_id UUID REFERENCES tickets(id) ON DELETE CASCADE NOT NULL,
  author_id UUID REFERENCES profiles(id) NOT NULL,
  message TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Passo 8 — Trigger de perfil automático

```sql
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

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
```

## Passo 9 — Configurar RLS

```sql
-- profiles
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuários autenticados podem ler perfis"
ON public.profiles FOR SELECT TO authenticated USING (true);

CREATE POLICY "Usuário pode atualizar próprio perfil"
ON public.profiles FOR UPDATE TO authenticated USING (auth.uid() = id);

CREATE POLICY "Service pode ler todos os profiles"
ON public.profiles FOR SELECT TO anon USING (true);

-- tickets
CREATE POLICY "Usuário pode criar chamado"
ON public.tickets FOR INSERT TO authenticated
WITH CHECK (auth.uid() = created_by);

CREATE POLICY "Usuário pode ver seus chamados"
ON public.tickets FOR SELECT TO authenticated
USING (auth.uid() = created_by);

CREATE POLICY "Admin pode ver todos os chamados"
ON public.tickets FOR SELECT TO authenticated
USING (EXISTS (
  SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin'
));

CREATE POLICY "Admin pode atualizar chamados"
ON public.tickets FOR UPDATE TO authenticated
USING (EXISTS (
  SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin'
));

CREATE POLICY "Service pode ler todos os tickets"
ON public.tickets FOR SELECT TO anon USING (true);

-- ticket_updates
CREATE POLICY "Usuário pode criar atualização"
ON public.ticket_updates FOR INSERT TO authenticated
WITH CHECK (auth.uid() = author_id);

CREATE POLICY "Usuário pode ver atualizações dos seus chamados"
ON public.ticket_updates FOR SELECT TO authenticated
USING (EXISTS (
  SELECT 1 FROM public.tickets WHERE id = ticket_id AND created_by = auth.uid()
));

CREATE POLICY "Admin pode ver todas as atualizações"
ON public.ticket_updates FOR SELECT TO authenticated
USING (EXISTS (
  SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role = 'admin'
));

CREATE POLICY "Service pode ler todos os updates"
ON public.ticket_updates FOR SELECT TO anon USING (true);
```

## Resultado da Etapa 1

```
✅ Projeto estruturado em camadas
✅ FastAPI rodando com documentação automática em /docs
✅ Supabase conectado via supabase-py
✅ Banco modelado com 3 tabelas
✅ Trigger de criação automática de perfil
✅ RLS configurado com policies nas 3 tabelas
```

---

# ✅ Etapa 2 — Autenticação

## Estrutura

```bash
mkdir routers middlewares
type nul > routers\__init__.py
type nul > middlewares\__init__.py
```

## `routers/auth.py`

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from database import supabase

router = APIRouter(prefix="/auth", tags=["auth"])

class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
def register(data: RegisterRequest):
    try:
        response = supabase.auth.sign_up({
            "email": data.email,
            "password": data.password,
            "options": {"data": {"full_name": data.full_name}}
        })
        if response.user is None:
            raise HTTPException(status_code=400, detail="Erro ao criar usuário")
        return {"message": "Usuário criado com sucesso", "user_id": str(response.user.id), "email": response.user.email}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
def login(data: LoginRequest):
    try:
        response = supabase.auth.sign_in_with_password({"email": data.email, "password": data.password})
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

## `middlewares/auth.py`

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
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado")
        return response.user
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado")

def get_current_profile(current_user=Depends(get_current_user)):
    try:
        response = supabase.table("profiles").select("*").eq("id", str(current_user.id)).single().execute()
        if not response.data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil não encontrado")
        return response.data
    except Exception:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil não encontrado")

def require_admin(profile=Depends(get_current_profile)):
    if profile["role"] != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito a administradores")
    return profile
```

## Resultado da Etapa 2

```
✅ POST /auth/register
✅ POST /auth/login com retorno de JWT
✅ Middleware get_current_user
✅ Middleware get_current_profile
✅ Middleware require_admin
✅ GET /me funcionando end to end
```

---

# ✅ Etapa 3 — Rotas de Chamados

## `routers/tickets.py`

```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from database import supabase
from middlewares.auth import get_current_profile, require_admin

router = APIRouter(prefix="/tickets", tags=["tickets"])

class TicketRequest(BaseModel):
    title: str
    description: str
    category: str
    priority: Optional[str] = "low"

class TicketUpdateRequest(BaseModel):
    message: str

class TicketStatusRequest(BaseModel):
    status: str

@router.post("")
def create_ticket(data: TicketRequest, profile=Depends(get_current_profile)):
    try:
        result = supabase.table("tickets").insert({
            "title": data.title, "description": data.description,
            "category": data.category, "priority": data.priority,
            "status": "open", "created_by": profile["id"]
        }).execute()
        return {"message": "Chamado aberto com sucesso", "ticket": result.data[0]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/all")
def list_all_tickets(profile=Depends(require_admin)):
    try:
        result = supabase.table("tickets") \
            .select("*, profiles!tickets_created_by_fkey(full_name, sector)") \
            .order("created_at", desc=True).execute()
        return {"tickets": result.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def list_my_tickets(profile=Depends(get_current_profile)):
    try:
        result = supabase.table("tickets").select("*") \
            .eq("created_by", profile["id"]).order("created_at", desc=True).execute()
        return {"tickets": result.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{ticket_id}")
def get_ticket(ticket_id: str, profile=Depends(get_current_profile)):
    try:
        result = supabase.table("tickets").select("*, ticket_updates(*)") \
            .eq("id", ticket_id).single().execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Chamado não encontrado")
        ticket = result.data
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
        result = supabase.table("tickets").update(update_data).eq("id", ticket_id).execute()
        return {"message": "Status atualizado com sucesso", "ticket": result.data[0]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{ticket_id}/updates")
def add_update(ticket_id: str, data: TicketUpdateRequest, profile=Depends(get_current_profile)):
    try:
        result = supabase.table("ticket_updates").insert({
            "ticket_id": ticket_id, "author_id": profile["id"], "message": data.message
        }).execute()
        return {"message": "Resposta adicionada com sucesso", "update": result.data[0]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

## Resultado da Etapa 3

```
✅ POST /tickets
✅ GET /tickets
✅ GET /tickets/all (admin)
✅ GET /tickets/{id}
✅ POST /tickets/{id}/updates
✅ PATCH /tickets/{id}/status (admin)
```

---

# ✅ Etapa 4 — Rotas Administrativas

## `routers/admin.py`

```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from database import supabase
from middlewares.auth import require_admin

router = APIRouter(prefix="/admin", tags=["admin"])

class AssignTicketRequest(BaseModel):
    assigned_to: str

class UpdateUserRoleRequest(BaseModel):
    role: str

@router.get("/users")
def list_users(profile=Depends(require_admin)):
    try:
        result = supabase.table("profiles").select("*").order("created_at", desc=True).execute()
        return {"users": result.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/users/{user_id}/role")
def update_user_role(user_id: str, data: UpdateUserRoleRequest, profile=Depends(require_admin)):
    valid_roles = ["user", "admin"]
    if data.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Role inválida. Use: {valid_roles}")
    try:
        result = supabase.table("profiles").update({"role": data.role}).eq("id", user_id).execute()
        return {"message": "Role atualizada com sucesso", "user": result.data[0]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/tickets/{ticket_id}/assign")
def assign_ticket(ticket_id: str, data: AssignTicketRequest, profile=Depends(require_admin)):
    try:
        result = supabase.table("tickets").update({"assigned_to": data.assigned_to}).eq("id", ticket_id).execute()
        return {"message": "Chamado atribuído com sucesso", "ticket": result.data[0]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/stats")
def get_stats(profile=Depends(require_admin)):
    try:
        tickets = supabase.table("tickets").select("status, priority, created_at, resolved_at").execute()
        data = tickets.data
        stats = {"total": len(data), "by_status": {}, "by_priority": {}}
        for ticket in data:
            s = ticket["status"]
            p = ticket["priority"]
            stats["by_status"][s] = stats["by_status"].get(s, 0) + 1
            stats["by_priority"][p] = stats["by_priority"].get(p, 0) + 1
        return stats
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

## Resultado da Etapa 4

```
✅ GET /admin/users
✅ PATCH /admin/users/{id}/role
✅ PATCH /admin/tickets/{id}/assign
✅ GET /admin/stats
```

---

# ✅ Etapa 5 — Dashboard Streamlit

## Setup

```bash
cd dashboard
python -m venv venv
venv\Scripts\activate
pip install streamlit supabase python-dotenv pandas plotly
pip freeze > requirements.txt
```

## `.env`

```
SUPABASE_URL=https://xxxxxxxxxxx.supabase.co
SUPABASE_KEY=sua_anon_key_aqui
```

## Rodar

```bash
streamlit run app.py
```

Abre em `http://localhost:8501`

## Funcionalidades

- KPIs: total de chamados, abertos, em atendimento, resolvidos, tempo médio de resolução
- Gráfico de barras por status
- Gráfico de pizza por prioridade
- Gráfico de barras por categoria
- Timeline de chamados ao longo do tempo
- Tabela completa com filtro por status

## Resultado da Etapa 5

```
✅ Dashboard conectado ao Supabase
✅ KPIs operacionais
✅ 4 gráficos interativos com Plotly
✅ Tabela filtrável
✅ Cache de 30s para performance
```

---

# 🚧 Etapa 6 — Frontend React

> Em desenvolvimento. Será documentada ao final da etapa.

---

# 🚧 Etapa 7 — Deploy completo

> Em desenvolvimento. Será documentada ao final da etapa.