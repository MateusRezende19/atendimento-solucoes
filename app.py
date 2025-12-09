import streamlit as st
from supabase_client import (
    auth_login, auth_logout,
    criar_atendimento, listar_atendimentos,
    atualizar_atendimento
)
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
import random
import time


# -------------------------------------------------------
# CONFIGURAÇÃO
# -------------------------------------------------------
st.set_page_config(page_title="Sistema de Atendimento", layout="wide")


# -------------------------------------------------------
# Helpers
# -------------------------------------------------------
def gerar_ticket():
    return f"ATD-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"


def parse_iso_datetime(value: str):
    """Converte datas ISO UTC para horário brasileiro."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone(ZoneInfo("America/Sao_Paulo"))
    except:
        return None


def estilo_por_status(status: str):
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
        except Exception as e:
            st.error("Erro ao logar. Verifique e-mail e senha.")


def logout_button():
    if st.button("Sair"):
        auth_logout()
        st.session_state.user = None
        st.rerun()


if not st.session_state.user:
    login_screen()
    st.stop()


# -------------------------------------------------------
# MENU ESTILIZADO
# -------------------------------------------------------
menu_css = """
<style>
.menu-btn {
    width: 100%;
    padding: 12px 16px;
    border-radius: 8px;
    border: 1px solid #d1d5db;
    background-color: white;
    margin-bottom: 10px;
    font-size: 15px;
    font-weight: 500;
    text-align: left;
    cursor: pointer;
}
.menu-btn:hover {
    background-color: #e5e7eb;
}
.menu-btn-active {
    background-color: #2563eb !important;
    color: white !important;
}
</style>
"""
st.markdown(menu_css, unsafe_allow_html=True)

st.sidebar.title("Menu")

if "pagina" not in st.session_state:
    st.session_state["pagina"] = "Novo Atendimento"

def set_page(pg):
    st.session_state["pagina"] = pg

if st.sidebar.button("Novo Atendimento"):
    set_page("Novo Atendimento")

if st.sidebar.button("Listar Atendimentos"):
    set_page("Listar Atendimentos")

logout_button()

opcao = st.session_state["pagina"]

st.title("📞 Sistema de Gerenciamento de Atendimentos")


# =========================================================
# NOVO ATENDIMENTO
# =========================================================
if opcao == "Novo Atendimento":

    st.subheader("📝 Registrar Atendimento")

    with st.expander("📂 Dados da Abertura do Atendimento", expanded=True):

        agora = datetime.now(ZoneInfo("America/Sao_Paulo"))
        data_br = agora.strftime("%d/%m/%Y %H:%M")
        st.write(f"📅 **Data e hora do atendimento:** {data_br}")

        funcionario = st.text_input("Nome do funcionário atendido")
        quem = st.text_input("Quem realizou o atendimento")
        motivo = st.text_area("Motivo do contato")
        meio = st.selectbox("Meio de atendimento", ["Telefone", "WhatsApp", "E-mail", "Presencial"])

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

        numero_chamado = gerar_ticket()
        st.write(f"🎫 **Número do chamado:** `{numero_chamado}`")

        if st.button("💾 Salvar atendimento"):

            dados = {
                "user_id": st.session_state.user.id,
                "data_atendimento": agora.isoformat(),
                "quem_realizou": quem,
                "funcionario_atendido": funcionario,
                "motivo_contato": motivo,
                "meio_atendimento": meio,
                "assunto": assunto,
                "andamento": "Aguardando",
                "numero_chamado": numero_chamado,
                "tratativa": None,
                "data_conclusao": None,
                "updated_at": agora.isoformat(),
            }

            criar_atendimento(dados)
            st.success("✅ Atendimento registrado com sucesso!")

            time.sleep(1.5)
            st.rerun()



# =========================================================
# LISTAR ATENDIMENTOS
# =========================================================
if opcao == "Listar Atendimentos":

    st.subheader("📋 Atendimentos Registrados")

    dados = listar_atendimentos(st.session_state.user.id).data

    if not dados:
        st.info("Nenhum atendimento encontrado.")
        st.stop()

    # -------------------------
    # FILTROS
    # -------------------------
    with st.expander("🔍 Filtros de pesquisa", expanded=True):

        col1, col2, col3 = st.columns(3)

        with col1:
            status_selecionados = st.multiselect(
                "Status",
                ["Aguardando", "Concluído"],
                default=["Aguardando", "Concluído"],
            )
            incluir_excluidos = st.checkbox("Incluir excluídos", value=False)

        with col2:
            assuntos = sorted({d.get("assunto") for d in dados if d.get("assunto")})
            filtro_assunto = st.selectbox("Assunto", ["Todos"] + assuntos)

        with col3:
            filtrar_periodo = st.checkbox("Filtrar por período")
            if filtrar_periodo:
                data_inicio = st.date_input("Data inicial", date.today() - timedelta(days=7))
                data_fim = st.date_input("Data final", date.today())
            else:
                data_inicio = data_fim = None


    # -------------------------
    # FILTRAGEM
    # -------------------------
    filtrados = []
    for row in dados:

        status = row.get("andamento")

        if status == "Excluído" and not incluir_excluidos:
            continue

        if status != "Excluído" and status not in status_selecionados:
            continue

        if filtro_assunto != "Todos" and row.get("assunto") != filtro_assunto:
            continue

        dt_atendimento = parse_iso_datetime(row.get("data_atendimento"))
        if filtrar_periodo and dt_atendimento:
            if not (data_inicio <= dt_atendimento.date() <= data_fim):
                continue

        filtrados.append(row)

    filtrados.sort(
        key=lambda r: parse_iso_datetime(r.get("data_atendimento")) or datetime.min,
        reverse=True,
    )

    # -------------------------
    # EXIBIÇÃO DOS REGISTROS
    # -------------------------
    for row in filtrados:

        dt_abertura = parse_iso_datetime(row.get("data_atendimento"))
        abertura_br = dt_abertura.strftime("%d/%m/%Y %H:%M") if dt_abertura else "—"

        dt_update = parse_iso_datetime(row.get("updated_at"))
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
  <h3>🗂 Chamado: {row.get('numero_chamado')}</h3>

  <p>🧑‍💼 <b>Funcionário atendido:</b> {row.get('funcionario_atendido')}</p>
  <p>👤 <b>Quem realizou:</b> {row.get('quem_realizou')}</p>

  <p>📞 <b>Meio:</b> {row.get('meio_atendimento')}</p>
  <p>🎯 <b>Assunto:</b> {row.get('assunto')}</p>

  <p>📅 <b>Abertura:</b> {abertura_br}</p>
  <p>🟢 <b>Última atualização:</b> {update_br}</p>

  <p>{icon} <b>Status:</b> {row.get('andamento')}</p>

  <p>📝 <b>Tratativa:</b> {row.get('tratativa') or "—"}</p>
</div>
""",
            unsafe_allow_html=True,
        )

        # -----------------------------------------------------
        # EXPANDER DE EDIÇÃO
        # -----------------------------------------------------
        with st.expander("✏️ Editar / Detalhar este atendimento"):

            col1, col2 = st.columns(2)

            with col1:
                novo_funcionario = st.text_input(
                    "Funcionário atendido",
                    value=row.get("funcionario_atendido"),
                    key=f"func_{row['id']}",
                )

                novo_quem = st.text_input(
                    "Quem realizou",
                    value=row.get("quem_realizou"),
                    key=f"quem_{row['id']}",
                )

                novo_meio = st.selectbox(
                    "Meio",
                    ["Telefone", "WhatsApp", "E-mail", "Presencial"],
                    index=["Telefone", "WhatsApp", "E-mail", "Presencial"].index(row.get("meio_atendimento")),
                    key=f"meio_{row['id']}",
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
                    key=f"assunto_{row['id']}",
                )

            with col2:

                novo_status = st.selectbox(
                    "Status",
                    ["Aguardando", "Concluído", "Excluído"],
                    index=["Aguardando", "Concluído", "Excluído"].index(row.get("andamento")),
                    key=f"status_{row['id']}",
                )

                nova_tratativa = st.text_area(
                    "Tratativa",
                    value=row.get("tratativa") or "",
                    key=f"trat_{row['id']}",
                )


            if st.button("💾 Salvar alterações", key=f"save_{row['id']}"):

                update_data = {
                    "funcionario_atendido": novo_funcionario,
                    "quem_realizou": novo_quem,
                    "meio_atendimento": novo_meio,
                    "assunto": novo_assunto,
                    "andamento": novo_status,
                    "tratativa": nova_tratativa,
                    "updated_at": datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat(),
                }

                if novo_status == "Concluído" and not row.get("data_conclusao"):
                    update_data["data_conclusao"] = datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat()

                atualizar_atendimento(row["id"], update_data)

                st.success("Alterações salvas!")
                time.sleep(0.5)
                st.rerun()


        if row.get("andamento") != "Excluído":
            if st.button(f"🗑️ Excluir atendimento", key=f"del_{row['id']}"):
                atualizar_atendimento(
                    row["id"],
                    {
                        "andamento": "Excluído",
                        "updated_at": datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat()
                    }
                )
                st.warning("Atendimento excluído!")
                time.sleep(0.5)
                st.rerun()

        st.markdown("---")
