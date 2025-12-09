import streamlit as st
from supabase import create_client
from datetime import datetime
from zoneinfo import ZoneInfo


# ============================================================
# CARREGAR CREDENCIAIS DO STREAMLIT SECRETS
# ============================================================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ============================================================
# AUTENTICAÇÃO
# ============================================================
def auth_login(email, password):
    """Realiza login no Supabase Auth."""
    return supabase.auth.sign_in_with_password({"email": email, "password": password})


def auth_logout():
    """Realiza logout do usuário autenticado."""
    supabase.auth.sign_out()


# ============================================================
# CRIAR ATENDIMENTO
# ============================================================
def criar_atendimento(data: dict):
    """Insere um novo atendimento no banco."""
    return supabase.table("atendimentos").insert(data).execute()


# ============================================================
# LISTAR ATENDIMENTOS
# ============================================================
def listar_atendimentos(user_id):
    """Lista atendimentos do usuário logado."""
    return (
        supabase.table("atendimentos")
        .select("*")
        .eq("user_id", user_id)
        .order("data_atendimento", desc=True)
        .execute()
    )


# ============================================================
# ATUALIZAR ATENDIMENTO
# ============================================================
def atualizar_atendimento(id_atendimento, dados: dict):
    """
    Atualiza campos de um atendimento no banco.
    Sempre atualiza também o updated_at com timezone Brasil.
    """
    dados["updated_at"] = datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat()

    return (
        supabase.table("atendimentos")
        .update(dados)
        .eq("id", id_atendimento)
        .execute()
    )


# ============================================================
# EXCLUIR (MARCAR COMO EXCLUÍDO)
# ============================================================
def excluir_atendimento(id_atendimento):
    """
    Marca o atendimento como excluído.
    """
    return (
        supabase.table("atendimentos")
        .update({
            "andamento": "Excluído",
            "updated_at": datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat(),
        })
        .eq("id", id_atendimento)
        .execute()
    )
