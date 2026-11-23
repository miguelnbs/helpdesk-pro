import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


def new_client() -> Client:
    """Cliente novo e anônimo. Usado em cadastro, login e recuperação de senha,
    para que a sessão de um usuário nunca fique guardada em estado compartilhado."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def client_for_token(token: str) -> Client:
    """Cliente exclusivo da requisição: as consultas ao banco rodam com o JWT do
    usuário logado, então o RLS enxerga o auth.uid() correto."""
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    client.postgrest.auth(token)
    return client


# Cliente compartilhado, usado apenas para validar tokens (auth.get_user não guarda sessão)
supabase: Client = new_client()
