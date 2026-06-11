# HelpDesk Pro

Sistema interno de abertura e gestão de chamados técnicos, com painel administrativo, controle de SLA, histórico de interações e dashboard operacional.

---

## Links de produção

| Serviço | URL |
|---|---|
| Frontend | https://helpdesk-pro-rosy.vercel.app |
| API | https://helpdesk-pro-production-06b5.up.railway.app |
| Dashboard | https://appdesk-pro-hf2cgtvatyycth8udqclw6.streamlit.app |
| Documentação da API | https://helpdesk-pro-production-06b5.up.railway.app/docs |

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
| 7 | Deploy completo | ✅ Concluída |

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
│   ├── Procfile
│   ├── runtime.txt
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
    │   │   ├── ForgotPassword.tsx
    │   │   ├── ResetPassword.tsx
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
    ├── vercel.json
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

## Como rodar localmente

### API

```bash
cd api
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

API disponível em `http://localhost:8000`
Documentação em `http://localhost:8000/docs`

### Dashboard

```bash
cd dashboard
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Dashboard disponível em `http://localhost:8501`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend disponível em `http://localhost:5173`

---

# ✅ Etapa 1 — Setup, Banco e Conexão

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

## Rotas

| Rota | Método | Descrição |
|---|---|---|
| `/auth/register` | POST | Cadastro de usuário |
| `/auth/login` | POST | Login com retorno de JWT |
| `/auth/forgot-password` | POST | Envio de email de recuperação |
| `/auth/reset-password` | POST | Redefinição de senha |
| `/me` | GET | Perfil do usuário autenticado |

## Resultado da Etapa 2

```
✅ Cadastro e login com JWT
✅ Recuperação e redefinição de senha
✅ Middleware de autenticação reutilizável
✅ Controle de acesso por perfil (user/admin)
```

---

# ✅ Etapa 3 — Rotas de Chamados

## Rotas

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

## Rotas

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

## Páginas

| Página | Rota | Descrição |
|---|---|---|
| Login | `/login` | Autenticação com email e senha |
| Cadastro | `/register` | Criação de conta |
| Esqueci senha | `/forgot-password` | Envio de link de recuperação |
| Redefinir senha | `/reset-password` | Nova senha via link |
| Dashboard | `/dashboard` | Listagem de chamados |
| Novo Chamado | `/tickets/new` | Formulário de abertura |
| Detalhes | `/tickets/:id` | Histórico e atualização de status |

## Resultado da Etapa 6

```
✅ Login, cadastro e recuperação de senha
✅ Dashboard listando chamados com status e prioridade
✅ Formulário de novo chamado
✅ Detalhes com histórico de atualizações
✅ Atualização de status para admin
✅ Rotas protegidas com PrivateRoute
✅ Contexto de autenticação com JWT
✅ Integração completa com a API FastAPI
```

---

# ✅ Etapa 7 — Deploy completo

## Configuração do Railway (API)

- **Root Directory:** `/api`
- **Branch:** `main`
- **Procfile:** `web: uvicorn main:app --host 0.0.0.0 --port $PORT`
- **runtime.txt:** `python-3.12.0`
- **Variáveis de ambiente:** `SUPABASE_URL`, `SUPABASE_KEY`, `MISE_PYTHON_GITHUB_ATTESTATIONS=false`

## Configuração do Vercel (Frontend)

- **Root Directory:** `frontend`
- **Framework:** Vite
- **Variável de ambiente:** `VITE_API_URL=https://********.up.railway.app`
- **vercel.json:** rewrites para suporte a rotas React

## Configuração do Streamlit Cloud (Dashboard)

- **Repository:** `miguelnbs/helpdesk-pro`
- **Main file:** `dashboard/app.py`
- **Python:** 3.12
- **Secrets:** `SUPABASE_URL`, `SUPABASE_KEY`

## Resultado da Etapa 7

```
✅ API no Railway — online
✅ Frontend no Vercel — online
✅ Dashboard no Streamlit Cloud — online
✅ Recuperação de senha funcionando em produção
✅ Sistema completo em produção
```