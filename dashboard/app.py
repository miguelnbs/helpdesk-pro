import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
from dotenv import load_dotenv
from pathlib import Path
import os

# --- Conexão ---
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- Config da página ---
st.set_page_config(
    page_title="HelpDesk Pro — Dashboard",
    page_icon="🎫",
    layout="wide"
)

st.title("🎫 HelpDesk Pro — Dashboard Operacional")
st.markdown("---")

# --- Buscar dados ---
@st.cache_data(ttl=30)
def load_tickets():
    result = supabase.table("tickets") \
        .select("*, profiles!tickets_created_by_fkey(full_name, sector)") \
        .execute()
    return pd.DataFrame(result.data)

@st.cache_data(ttl=30)
def load_updates():
    result = supabase.table("ticket_updates").select("*").execute()
    return pd.DataFrame(result.data)

df = load_tickets()
df_updates = load_updates()

if df.empty:
    st.warning("Nenhum chamado encontrado.")
    st.stop()

# --- Conversão de datas ---
df["created_at"] = pd.to_datetime(df["created_at"])
df["resolved_at"] = pd.to_datetime(df["resolved_at"], errors="coerce")

# --- KPIs ---
total = len(df)
abertos = len(df[df["status"] == "open"])
em_atendimento = len(df[df["status"] == "in_progress"])
resolvidos = len(df[df["status"] == "resolved"])

resolvidos_df = df.dropna(subset=["resolved_at"])
if not resolvidos_df.empty:
    tempo_medio = (resolvidos_df["resolved_at"] - resolvidos_df["created_at"]).mean()
    tempo_medio_str = f"{tempo_medio.seconds // 3600}h {(tempo_medio.seconds % 3600) // 60}min"
else:
    tempo_medio_str = "N/A"

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total de Chamados", total)
col2.metric("Abertos", abertos)
col3.metric("Em Atendimento", em_atendimento)
col4.metric("Resolvidos", resolvidos)
col5.metric("Tempo Médio de Resolução", tempo_medio_str)

st.markdown("---")

# --- Gráficos ---
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Chamados por Status")
    status_count = df["status"].value_counts().reset_index()
    status_count.columns = ["Status", "Quantidade"]
    fig1 = px.bar(status_count, x="Status", y="Quantidade", color="Status")
    st.plotly_chart(fig1, use_container_width=True)

with col_b:
    st.subheader("Chamados por Prioridade")
    priority_count = df["priority"].value_counts().reset_index()
    priority_count.columns = ["Prioridade", "Quantidade"]
    fig2 = px.pie(priority_count, names="Prioridade", values="Quantidade")
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

col_c, col_d = st.columns(2)

with col_c:
    st.subheader("Chamados por Categoria")
    category_count = df["category"].value_counts().reset_index()
    category_count.columns = ["Categoria", "Quantidade"]
    fig3 = px.bar(category_count, x="Categoria", y="Quantidade", color="Categoria")
    st.plotly_chart(fig3, use_container_width=True)

with col_d:
    st.subheader("Chamados ao Longo do Tempo")
    df["data"] = df["created_at"].dt.date
    timeline = df.groupby("data").size().reset_index(name="Quantidade")
    fig4 = px.line(timeline, x="data", y="Quantidade", markers=True)
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

# --- Tabela completa ---
st.subheader("Todos os Chamados")

status_filter = st.multiselect(
    "Filtrar por status:",
    options=df["status"].unique().tolist(),
    default=df["status"].unique().tolist()
)

df_filtered = df[df["status"].isin(status_filter)]
