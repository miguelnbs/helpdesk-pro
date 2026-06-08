# HelpDesk Pro

Sistema interno de abertura e gestão de chamados técnicos, com painel administrativo, controle de SLA, histórico de interações e dashboard operacional.

> 🚧 **Projeto em desenvolvimento ativo.** Deploy em andamento.

---

## Status do projeto

| Etapa | Descrição | Status |
|---|---|---|
| 1 | Setup, banco e conexão | ✅ Concluída |
| 2 | Autenticação e middlewares | ✅ Concluída |
| 3 | Rotas de chamados (tickets) | ✅ Concluída |
| 4 | Rotas administrativas | ✅ Concluída |
| 5 | Dashboard Streamlit | ✅ Concluída |
| 6 | Frontend React | ✅ Concluída |
| 7 | Deploy completo | 🚧 Em desenvolvimento |

---

## Visão geral

**Stack completa do projeto:**

| Camada | Tecnologia |
|---|---|
| Frontend | React + TypeScript + Vite + Tailwind CSS |
| API | Python + FastAPI |
| Banco de dados | Supabase (PostgreSQL) |
| Autenticação | Supabase Auth + JWT |
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
└── frontend/
    ├── src/
    │   ├── components/
    │   │   └── PrivateRoute.tsx
    │   ├── context/
    │   │   └── AuthContext.tsx
    │   ├── pages/
    │   │   ├── Login.tsx
    │   │   ├── Register.tsx
    │   │   ├── Dashboard.tsx
    │   │   ├── NewTicket.tsx
    │   │   └── TicketDetail.tsx
    │   ├── services/
    │   │   └── api.ts
    │   ├── types/
    │   │   └── index.ts
    │   ├── App.tsx
    │   └── main.tsx
    ├── .env
    ├── tailwind.config.js
    ├── postcss.config.js
    └── package.json
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

- Python 3.10+
- Node.js instalado
- Conta no [Supabase](https://supabase.com)

## Setup da API

```bash
cd api
python -m venv venv
venv\Scripts\activate
pip install fastapi uvicorn python-dotenv supabase "pydantic[email]"
pip freeze > requirements.txt
```

## `.env`

```
SUPABASE_URL=https://xxxxxxxxxxx.supabase.co
SUPABASE_KEY=sua_anon_key_aqui
```

## `database.py`

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

## Tabelas no Supabase

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

## Trigger de perfil automático

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

## RLS — Row Level Security

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

## Rotas disponíveis

| Rota | Método | Descrição |
|---|---|---|
| `/tickets` | POST | Abrir novo chamado |
| `/tickets` | GET | Listar chamados do usuário |
| `/tickets/all` | GET | Listar todos os chamados (admin) |
| `/tickets/{id}` | GET | Detalhes com histórico |
| `/tickets/{id}/status` | PATCH | Atualizar status (admin) |
| `/tickets/{id}/updates` | POST | Adicionar resposta |

## Resultado da Etapa 3

```
✅ CRUD completo de chamados
✅ Controle de acesso por perfil
✅ Histórico de atualizações por chamado
✅ Atualização de status com registro de resolved_at
```

---

# ✅ Etapa 4 — Rotas Administrativas

## Rotas disponíveis

| Rota | Método | Descrição |
|---|---|---|
| `/admin/users` | GET | Listar todos os usuários |
| `/admin/users/{id}/role` | PATCH | Atualizar role do usuário |
| `/admin/tickets/{id}/assign` | PATCH | Atribuir chamado a técnico |
| `/admin/stats` | GET | Estatísticas por status e prioridade |

## Resultado da Etapa 4

```
✅ Gestão de usuários e roles
✅ Atribuição de chamados
✅ Estatísticas operacionais
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

## Rodar

```bash
streamlit run app.py
```

Abre em `http://localhost:8501`

## Funcionalidades

- KPIs: total, abertos, em atendimento, resolvidos, tempo médio de resolução
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

# ✅ Etapa 6 — Frontend React

## Setup

```bash
cd frontend
npx create-vite@5 . --template react-ts
npm install
npm install axios react-router-dom
npm install -D tailwindcss postcss autoprefixer @tailwindcss/postcss
```

## `.env`

```
VITE_API_URL=http://localhost:8000
```

## `src/index.css`

```css
@import "tailwindcss";
```

## `postcss.config.js`

```js
export default {
  plugins: {
    '@tailwindcss/postcss': {},
    autoprefixer: {},
  },
}
```

## Rodar

```bash
npm run dev
```

Abre em `http://localhost:5173`

## Páginas

| Página | Rota | Descrição |
|---|---|---|
| Login | `/login` | Autenticação com email e senha |
| Cadastro | `/register` | Criação de conta |
| Dashboard | `/dashboard` | Listagem de chamados |
| Novo Chamado | `/tickets/new` | Formulário de abertura |
| Detalhes | `/tickets/:id` | Histórico e atualização de status |

## Resultado da Etapa 6

```
✅ Login e cadastro funcionando
✅ Dashboard listando chamados com status e prioridade
✅ Formulário de novo chamado
✅ Detalhes com histórico de atualizações
✅ Atualização de status para admin
✅ Rotas protegidas com PrivateRoute
✅ Contexto de autenticação com JWT
✅ Integração completa com a API FastAPI
```

---

# 🚧 Etapa 7 — Deploy completo

> Em desenvolvimento. Será documentada ao final da etapa.

**Plano de deploy:**

| Serviço | Plataforma | Status |
|---|---|---|
| API FastAPI | Railway | 🚧 Pendente |
| Frontend React | Vercel | 🚧 Pendente |
| Dashboard Streamlit | Streamlit Cloud | 🚧 Pendente |