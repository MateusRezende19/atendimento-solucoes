from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def auth_login(email, password):
    return supabase.auth.sign_in_with_password({"email": email, "password": password})


def auth_logout():
    supabase.auth.sign_out()


def criar_atendimento(data):
    return supabase.table("atendimentos").insert(data).execute()


def listar_atendimentos(user_id):
    return (
        supabase.table("atendimentos")
        .select("*")
        .eq("user_id", user_id)
        .order("data_atendimento", desc=True)
        .execute()
    )


def atualizar_atendimento(id, dados):
    return (
        supabase.table("atendimentos")
        .update(dados)
        .eq("id", id)
        .execute()
    )
