# HelpDesk Pro

Sistema de gestão de chamados técnicos: abertura, acompanhamento e atendimento de chamados, com perfis de acesso (usuário e administrador), histórico de interações e dashboard operacional.

Projeto da disciplina Projeto Integrado (EAD) — Análise e Desenvolvimento de Sistemas.
Aluno: **Miguel Nóbrega Scheidegger**

## Links de produção

| Serviço | URL |
|---|---|
| Frontend | https://helpdesk-pro-rosy.vercel.app |
| API (documentação interativa) | https://helpdesk-pro-f55t.onrender.com/docs |
| Dashboard analítico | https://appdesk-pro-hf2cgtvatyycth8udqclw6.streamlit.app |

> A API roda no plano gratuito do Render, que "dorme" após alguns minutos sem uso. A primeira requisição depois disso pode levar cerca de 1 minuto para responder.

## Stack

| Camada | Tecnologia |
|---|---|
| Frontend | React 18 + TypeScript + Vite 5 + Tailwind CSS |
| API | Python + FastAPI + Pydantic |
| Banco e autenticação | Supabase (PostgreSQL, Auth, RLS) |
| Dashboard | Streamlit + Pandas + Plotly |
| Deploy | Vercel (frontend), Render (API), Streamlit Cloud (dashboard) |

## Arquitetura

```
React (Vercel) ──REST──> FastAPI (Render) ──> Supabase (PostgreSQL + Auth)
                                                   ▲
                              Streamlit (Streamlit Cloud) ──┘ (leitura)
```

Cada requisição à API usa um cliente do banco autenticado com o token do próprio usuário. Assim o RLS do PostgreSQL enxerga a identidade correta mesmo com vários usuários conectados ao mesmo tempo.

## Histórias de usuário implementadas (EPIC 1 e EPIC 2)

| ID | História | Onde está no código |
|---|---|---|
| 1.1 | Cadastro de usuário | `POST /auth/register` · `pages/Register.tsx` · trigger `on_auth_user_created` |
| 1.2 | Gerenciamento de perfil | `GET` e `PATCH /me` · `pages/Profile.tsx` |
| 1.3 | Autenticação e recuperação de senha | `/auth/login`, `/auth/forgot-password`, `/auth/reset-password` · `pages/Login`, `ForgotPassword`, `ResetPassword` |
| 1.4 | Perfis de acesso diferenciados | `require_admin` · `PATCH /admin/users/{id}/role` · policies RLS |
| 1.5 | Banco de dados | `banco_de_dados_EPIC1_e_2.sql` |
| 1.6 | Interface de usuário | `frontend/src/pages` |
| 1.7 | Proteção de rotas | `components/PrivateRoute.tsx` · `middlewares/auth.py` |
| 1.8 | Documentação automática da API | `/docs` (Swagger UI do FastAPI) |
| 2.1 | Criar chamado | `POST /tickets` · `pages/NewTicket.tsx` |
| 2.2 | Consultar chamados | `GET /tickets`, `/tickets/all`, `/tickets/{id}` · `pages/Dashboard.tsx`, `TicketDetail.tsx` |
| 2.3 | Atualizar chamado | `PATCH /tickets/{id}/status` · `POST /tickets/{id}/updates` |
| 2.4 | Excluir chamado | `DELETE /tickets/{id}` · botão "Excluir chamado" em `TicketDetail.tsx` |
| 2.5 | Permissões de acesso aos chamados | `require_admin` · policies RLS de `tickets` e `ticket_updates` |
| 2.6 | Banco de dados dos chamados | tabelas `tickets` e `ticket_updates` no script SQL |
| 2.7 | Interface de gestão de chamados | `Dashboard.tsx`, `NewTicket.tsx`, `TicketDetail.tsx` |

## Rotas da API

| Método | Rota | Acesso |
|---|---|---|
| POST | `/auth/register` | público |
| POST | `/auth/login` | público |
| POST | `/auth/forgot-password` | público |
| POST | `/auth/reset-password` | link de recuperação |
| GET | `/me` | autenticado |
| PATCH | `/me` | autenticado (nome e setor) |
| POST | `/tickets` | autenticado |
| GET | `/tickets` | autenticado (somente os próprios) |
| GET | `/tickets/all` | administrador |
| GET | `/tickets/{id}` | dono do chamado ou administrador |
| PATCH | `/tickets/{id}/status` | administrador |
| POST | `/tickets/{id}/updates` | dono do chamado ou administrador |
| DELETE | `/tickets/{id}` | administrador |
| GET | `/admin/users` | administrador |
| PATCH | `/admin/users/{id}/role` | administrador |
| PATCH | `/admin/tickets/{id}/assign` | administrador |
| GET | `/admin/stats` | administrador |
| GET | `/health` | público |

## Banco de dados

O script `banco_de_dados_EPIC1_e_2.sql` cria as tabelas `profiles`, `tickets` e `ticket_updates`, o trigger de criação de perfil, as funções auxiliares de permissão e todas as policies de RLS. Ele pode ser executado do zero ou sobre um banco existente, e pode ser rodado mais de uma vez.

## Como rodar localmente

```bash
# API
cd api
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload          # http://localhost:8000/docs

# Frontend
cd frontend
npm install
npm run dev                        # http://localhost:5173

# Dashboard
cd dashboard
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py               # http://localhost:8501
```

Variáveis de ambiente (copie os arquivos `.env.example`):

| Pasta | Variáveis |
|---|---|
| `api` e `dashboard` | `SUPABASE_URL`, `SUPABASE_KEY` |
| `frontend` | `VITE_API_URL` |

## Deploy

| Serviço | Configuração |
|---|---|
| Render (API) | Root Directory `api` · Build `pip install -r requirements.txt` · Start `uvicorn main:app --host 0.0.0.0 --port $PORT` · variáveis `SUPABASE_URL` e `SUPABASE_KEY` |
| Vercel (frontend) | Root Directory `frontend` · variável `VITE_API_URL` apontando para a API no Render |
| Streamlit Cloud (dashboard) | Arquivo principal `dashboard/app.py` · secrets `SUPABASE_URL` e `SUPABASE_KEY` |

## Segurança

- Arquivos `.env` fora do repositório; somente `.env.example` é versionado.
- RLS ativo nas três tabelas. O usuário comum edita o próprio perfil, mas não consegue alterar a própria role.
- Ações de status, exclusão, atribuição e gestão de usuários são restritas ao administrador, na API e no banco.
- Cadastro, login e recuperação de senha usam clientes isolados, sem guardar sessão compartilhada no servidor.
