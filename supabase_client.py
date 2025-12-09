import os
import streamlit as st
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime
from zoneinfo import ZoneInfo


# ============================================================
# 1) Carregar .env (LOCAL)
# ============================================================
if os.path.exists(".env"):
    load_dotenv()


# ============================================================
# 2) Função segura para pegar secrets
#    → Streamlit Secrets (se existir)
#    → Caso contrário, usa .env
# ============================================================
def get_secret(key: str):

    # Tenta pegar via st.secrets SEM deixar Streamlit lançar erro
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass  # Ignora erro "No secrets found"

    # Fallback para .env
    return os.getenv(key)


SUPABASE_URL = get_secret("SUPABASE_URL")
SUPABASE_KEY = get_secret("SUPABASE_KEY")


# ============================================================
# 3) Validação
# ============================================================
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "❌ Erro: SUPABASE_URL ou SUPABASE_KEY não encontrados.\n"
        "Certifique-se de que:\n"
        "• Existe um arquivo .env com as chaves\n"
        "OU\n"
        "• Existe um .streamlit/secrets.toml quando rodando no Streamlit Cloud."
    )


# ============================================================
# 4) Criar cliente Supabase
# ============================================================
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ============================================================
# AUTENTICAÇÃO
# ============================================================
def auth_login(email, password):
    return supabase.auth.sign_in_with_password({"email": email, "password": password})


def auth_logout():
    supabase.auth.sign_out()


# ============================================================
# CRUD
# ============================================================
def criar_atendimento(data: dict):
    return supabase.table("atendimentos").insert(data).execute()


def listar_atendimentos(user_id):
    return (
        supabase.table("atendimentos")
        .select("*")
        .eq("user_id", user_id)
        .order("data_atendimento", desc=True)
        .execute()
    )


def atualizar_atendimento(id_atendimento, dados: dict):
    dados["updated_at"] = datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat()
    return (
        supabase.table("atendimentos")
        .update(dados)
        .eq("id", id_atendimento)
        .execute()
    )


def excluir_atendimento(id_atendimento):
    return (
        supabase.table("atendimentos")
        .update({
            "andamento": "Excluído",
            "updated_at": datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat(),
        })
        .eq("id", id_atendimento)
        .execute()
    )
