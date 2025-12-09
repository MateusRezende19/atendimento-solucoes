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
# CONFIGURAÇÃO DO STREAMLIT
# -------------------------------------------------------
st.set_page_config(page_title="Sistema de Atendimento", layout="wide")


# -------------------------------------------------------
# HELPERS
# -------------------------------------------------------
def gerar_ticket() -> str:
    """Gera um número de chamado no formato ATD-AAAAMMDD-####"""
    return f"ATD-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"


def parse_iso_datetime(value: str):
    """Tenta converter uma string ISO (com ou sem hora) em datetime."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        try:
            return datetime.strptime(value, "%Y-%m-%d")
        except Exception:
            return None


def estilo_por_status(status: str):
    """Define cores e ícones para o cartão conforme o status."""
    status = (status or "").capitalize()
    if status == "Concluído":
        return "#E8F5E9", "#2E7D32", "🟢"
    if status == "Excluído":
        return "#FFEBEE", "#C62828", "🟥"
    return "#E3F2FD", "#1565C0", "🔵"  # Aguardando


# -------------------------------------------------------
# SESSÃO DE LOGIN
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
            st.error(f"Erro ao logar: {e}")


def logout_button():
    if st.button("Sair"):
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
opcao = st.sidebar.radio("Escolha", ["Novo Atendimento", "Listar Atendimentos"])
logout_button()

st.title("📞 Sistema de Gerenciamento de Atendimentos")


# =====================================================================================
# NOVO ATENDIMENTO
# =====================================================================================
if opcao == "Novo Atendimento":

    st.subheader("📝 Registrar Atendimento")

    if "form_reset" not in st.session_state:
        st.session_state.form_reset = False

    with st.expander("📂 Dados da Abertura do Atendimento", expanded=True):

        agora = datetime.now()
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
                "andamento": "Aguardando",
                "numero_chamado": numero_chamado,
                "tratativa": None,
                "data_conclusao": None,
                "assunto": assunto,
                "ultima_atualizacao": agora.isoformat()  # <<< ADICIONADO
            }

            criar_atendimento(dados)

            st.success("✅ Atendimento registrado com sucesso!")
            time.sleep(2)
            st.rerun()


# =====================================================================================
# LISTAR ATENDIMENTOS
# =====================================================================================
if opcao == "Listar Atendimentos":

    st.subheader("📋 Atendimentos Registrados")

    dados = listar_atendimentos(st.session_state.user.id).data

    if len(dados) == 0:
        st.info("Nenhum atendimento encontrado.")
    else:

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

        filtrados = []

        for row in dados:
            status = row.get("andamento")

            if status == "Excluído" and not incluir_excluidos:
                continue

            if status != "Excluído" and status not in status_selecionados:
                continue

            if filtro_assunto != "Todos" and filtro_assunto != row.get("assunto"):
                continue

            dt = parse_iso_datetime(row.get("data_atendimento"))
            if filtrar_periodo and dt:
                if not (data_inicio <= dt.date() <= data_fim):
                    continue

            filtrados.append(row)

        filtrados.sort(
            key=lambda r: parse_iso_datetime(r.get("data_atendimento")) or datetime.min,
            reverse=True,
        )

        for row in filtrados:

            dt_abertura = parse_iso_datetime(row.get("data_atendimento"))
            abertura_br = dt_abertura.strftime("%d/%m/%Y %H:%M") if dt_abertura else "—"

            # <<< NOVO TRECHO: ÚLTIMA ATUALIZAÇÃO
            dt_update = parse_iso_datetime(row.get("ultima_atualizacao"))
            update_br = dt_update.strftime("%d/%m/%Y %H:%M") if dt_update else "—"

            bg, borda, icon = estilo_por_status(row.get("andamento"))

            st.markdown(
                f"""
<div style="
    border-radius: 12px;
    border: 2px solid {borda};
    background-color: {bg};
    padding: 18px;
    margin-bottom: 14px;
">
  <h3>🗂 Chamado: {row.get('numero_chamado')}</h3>

  <p>🧑‍💼 <b>Funcionário atendido:</b> {row.get('funcionario_atendido')}</p>
  <p>👤 <b>Quem realizou:</b> {row.get('quem_realizou')}</p>

  <p>📞 <b>Meio:</b> {row.get('meio_atendimento')}</p>
  <p>🎯 <b>Assunto:</b> {row.get('assunto')}</p>

  <p>📅 <b>Abertura:</b> {abertura_br}</p>
  <p>♻️ <b>Última atualização:</b> {update_br}</p>  <!-- <<< ADICIONADO -->

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
                        index=["Telefone", "WhatsApp", "E-mail", "Presencial"].index(
                            row.get("meio_atendimento")
                        ),
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
                        index=0
                        if not row.get("assunto")
                        else [
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
                        "ultima_atualizacao": datetime.now().isoformat(),   # <<< AQUI
                    }

                    if novo_status == "Concluído" and not row.get("data_conclusao"):
                        update_data["data_conclusao"] = datetime.now().isoformat()

                    atualizar_atendimento(row["id"], update_data)
                    st.success("Alterações salvas!")
                    time.sleep(1)
                    st.rerun()

            # -----------------------------------------------------
            # BOTÃO DE EXCLUSÃO
            # -----------------------------------------------------
            if row.get("andamento") != "Excluído":
                if st.button(f"🗑️ Excluir atendimento", key=f"del_{row['id']}"):
                    atualizar_atendimento(row["id"], {"andamento": "Excluído"})
                    st.warning("Atendimento excluído!")
                    time.sleep(1)
                    st.rerun()

            st.markdown("---")
