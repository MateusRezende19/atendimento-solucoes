import streamlit as st
from supabase_client import (
    auth_login, auth_logout,
    criar_atendimento, listar_atendimentos,
    atualizar_atendimento
)
from datetime import datetime, date, timedelta
import random
import time


# -------------------------------------------------------
# FUNÇÃO PARA GERAR HORÁRIO EXATO SEM UTC
# -------------------------------------------------------
def agora_br_supabase():
    """
    Retorna datetime local como string no formato:
    YYYY-MM-DD HH:MM:SS

    Esse formato impede o Supabase de converter para UTC.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# -------------------------------------------------------
# CONFIGURAÇÃO DO APP
# -------------------------------------------------------
st.set_page_config(page_title="Sistema de Atendimento", layout="wide")


# -------------------------------------------------------
# FUNÇÕES AUXILIARES
# -------------------------------------------------------
def gerar_ticket():
    return f"ATD-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"


def parse_iso_datetime(value):
    """Converte a string salva no banco (YYYY-MM-DD HH:MM:SS) em datetime."""
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except:
        return None


def estilo_por_status(status):
    status = (status or "").capitalize()
    if status == "Concluído":
        return "#E8F5E9", "#2E7D32", "🟢"
    if status == "Excluído":
        return "#FFEBEE", "#C62828", "🟥"
    return "#E3F2FD", "#1565C0", "🔵"


# -------------------------------------------------------
# LOGIN
# -------------------------------------------------------
if "user" not in st.session_state:
    st.session_state.user = None


def login_screen():
    st.title("🔐 Login do Sistema")
    email = st.text_input("E-mail")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        try:
            user = auth_login(email, senha)
            st.session_state.user = user.user
            st.rerun()
        except:
            st.error("Erro ao logar.")


def logout_button():
    if st.sidebar.button("Sair"):
        auth_logout()
        st.session_state.user = None
        st.rerun()


if not st.session_state.user:
    login_screen()
    st.stop()


# -------------------------------------------------------
# MENU
# -------------------------------------------------------
st.sidebar.title("Menu")

if "pagina" not in st.session_state:
    st.session_state.pagina = "Novo Atendimento"

if st.sidebar.button("Novo Atendimento"):
    st.session_state.pagina = "Novo Atendimento"

if st.sidebar.button("Listar Atendimentos"):
    st.session_state.pagina = "Listar Atendimentos"

logout_button()

opcao = st.session_state.pagina


# -------------------------------------------------------
# NOVO ATENDIMENTO
# -------------------------------------------------------
if opcao == "Novo Atendimento":

    st.subheader("📝 Registrar Atendimento")

    with st.expander("📂 Dados da Abertura do Atendimento", expanded=True):

        agora = agora_br_supabase()

        dt_exibir = datetime.now().strftime("%d/%m/%Y %H:%M")
        st.write(f"📅 **Data e hora do atendimento:** {dt_exibir}")

        funcionario = st.text_input("Nome do funcionário atendido")
        quem = st.text_input("Quem realizou o atendimento")
        motivo = st.text_area("Motivo do contato")
        meio = st.selectbox("Meio", ["Telefone", "WhatsApp", "E-mail", "Presencial"])

        assunto = st.selectbox(
            "Assunto",
            [
                "Salário",
                "Salário Família",
                "Movimentações Megaged",
                "Vale Transporte",
                "Vale Alimentação / Refeição",
                "Retorno ao Trabalho",
            ],
        )

        numero = gerar_ticket()
        st.write(f"🎫 **Número do chamado:** `{numero}`")

        if st.button("💾 Salvar atendimento"):

            dados = {
                "user_id": st.session_state.user.id,
                "data_atendimento": agora,
                "ultima_atualizacao": agora,
                "quem_realizou": quem,
                "funcionario_atendido": funcionario,
                "motivo_contato": motivo,
                "meio_atendimento": meio,
                "assunto": assunto,
                "andamento": "Aguardando",
                "numero_chamado": numero,
                "tratativa": None,
                "data_conclusao": None,
            }

            criar_atendimento(dados)
            st.success("Atendimento salvo!")
            time.sleep(1)
            st.rerun()


# -------------------------------------------------------
# LISTAR ATENDIMENTOS
# -------------------------------------------------------
if opcao == "Listar Atendimentos":

    st.subheader("📋 Atendimentos Registrados")

    dados = listar_atendimentos(st.session_state.user.id).data

    if not dados:
        st.info("Nenhum atendimento encontrado.")
        st.stop()

    for row in dados:

        dt_abertura = parse_iso_datetime(row.get("data_atendimento"))
        dt_update = parse_iso_datetime(row.get("ultima_atualizacao"))

        abertura_br = dt_abertura.strftime("%d/%m/%Y %H:%M") if dt_abertura else "—"
        update_br = dt_update.strftime("%d/%m/%Y %H:%M") if dt_update else "—"

        bg, borda, icon = estilo_por_status(row.get("andamento"))

        st.markdown(
            f"""
<div style="
border-radius: 12px;
border: 2px solid {borda};
background-color: {bg};
padding: 18px;
margin-bottom: 16px;
">
<b>🗂 Chamado:</b> {row.get('numero_chamado')}<br>
<b>🧑‍💼 Funcionário atendido:</b> {row.get('funcionario_atendido')}<br>
<b>👤 Quem realizou:</b> {row.get('quem_realizou')}<br>
<b>📞 Meio:</b> {row.get('meio_atendimento')}<br>
<b>🎯 Assunto:</b> {row.get('assunto')}<br><br>

<b>📅 Abertura:</b> {abertura_br}<br>
<b>🟢 Última atualização:</b> {update_br}<br><br>

<b>{icon} Status:</b> {row.get('andamento')}<br>
<b>📝 Tratativa:</b> {row.get('tratativa') or "—"}<br>

</div>
""",
            unsafe_allow_html=True,
        )

        # -----------------------------------------------------
        # EDIÇÃO
        # -----------------------------------------------------

        with st.expander("✏️ Editar / Detalhar este atendimento"):

            novo_func = st.text_input(
                "Funcionário atendido", row.get("funcionario_atendido"), key=f"func{row['id']}"
            )

            novo_quem = st.text_input(
                "Quem realizou", row.get("quem_realizou"), key=f"quem{row['id']}"
            )

            novo_meio = st.selectbox(
                "Meio",
                ["Telefone", "WhatsApp", "E-mail", "Presencial"],
                index=["Telefone", "WhatsApp", "E-mail", "Presencial"].index(row.get("meio_atendimento")),
                key=f"meio{row['id']}",
            )

            novo_assunto = st.selectbox(
                "Assunto",
                [
                    "Salário",
                    "Salário Família",
                    "Movimentações Megaged",
                    "Vale Transporte",
                    "Vale Alimentação / Refeição",
                    "Retorno ao Trabalho",
                ],
                index=[
                    "Salário",
                    "Salário Família",
                    "Movimentações Megaged",
                    "Vale Transporte",
                    "Vale Alimentação / Refeição",
                    "Retorno ao Trabalho",
                ].index(row.get("assunto")),
                key=f"assunto{row['id']}",
            )

            novo_status = st.selectbox(
                "Status",
                ["Aguardando", "Concluído", "Excluído"],
                index=["Aguardando", "Concluído", "Excluído"].index(row.get("andamento")),
                key=f"status{row['id']}",
            )

            nova_tratativa = st.text_area(
                "Tratativa", row.get("tratativa") or "", key=f"trat{row['id']}"
            )

            if st.button("💾 Salvar alterações", key=f"save{row['id']}"):

                agora = agora_br_supabase()

                update_data = {
                    "funcionario_atendido": novo_func,
                    "quem_realizou": novo_quem,
                    "meio_atendimento": novo_meio,
                    "assunto": novo_assunto,
                    "andamento": novo_status,
                    "tratativa": nova_tratativa,
                    "ultima_atualizacao": agora,  # agora exato
                }

                if novo_status == "Concluído" and not row.get("data_conclusao"):
                    update_data["data_conclusao"] = agora

                atualizar_atendimento(row["id"], update_data)

                st.success("Alterações salvas!")
                time.sleep(1)
                st.rerun()

        st.markdown("---")
