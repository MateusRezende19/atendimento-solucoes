import streamlit as st
from supabase_client import (
    auth_login, auth_logout,
    criar_atendimento, listar_atendimentos,
    atualizar_atendimento
)
from datetime import datetime, date, timedelta, timezone
from zoneinfo import ZoneInfo
import random
import time

# -------------------------------------------------------
# TIMEZONES
# -------------------------------------------------------
TZ_UTC = timezone.utc
TZ_BR = ZoneInfo("America/Sao_Paulo")

# -------------------------------------------------------
# ADMINS (POR E-MAIL)
# -------------------------------------------------------
ADMINS = {
    "admin@gmail.com",
}

# -------------------------------------------------------
# HELPERS DE TEMPO
# -------------------------------------------------------
def agora_utc():
    return datetime.now(TZ_UTC)

def utc_to_br(dt: datetime):
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ_UTC)
    return dt.astimezone(TZ_BR)

def from_db_to_br(value):
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.fromisoformat(str(value))
    return utc_to_br(dt)

# -------------------------------------------------------
# CONFIG
# -------------------------------------------------------
st.set_page_config(page_title="Atendimentos", layout="wide")

# -------------------------------------------------------
# AUXILIARES
# -------------------------------------------------------
def gerar_ticket():
    return f"ATD-{datetime.now(TZ_BR).strftime('%Y%m%d')}-{random.randint(1000, 9999)}"

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
    st.title("🕑 Atendimentos")
    email = st.text_input("E-mail")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        try:
            user = auth_login(email, senha)
            st.session_state.user = user.user
            st.rerun()
        except Exception:
            st.error("Erro ao logar. Verifique e-mail e senha.")

def logout_button():
    if st.sidebar.button("Sair"):
        auth_logout()
        st.session_state.user = None
        st.rerun()

if not st.session_state.user:
    login_screen()
    st.stop()

# -------------------------------------------------------
# FLAG DE ADMIN
# -------------------------------------------------------
USER_EMAIL = getattr(st.session_state.user, "email", None)
IS_ADMIN = USER_EMAIL in ADMINS

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
st.title("📞 Gerenciamento de Atendimentos")

# =========================================================
# NOVO ATENDIMENTO
# =========================================================
if opcao == "Novo Atendimento":

    st.subheader("📝 Registrar Atendimento")

    with st.expander("📂 Dados da Abertura do Atendimento", expanded=True):

        agora_br = datetime.now(TZ_BR)
        data_br = agora_br.strftime("%d/%m/%Y %H:%M")

        agora_utc_iso = agora_utc().isoformat()

        st.write(f"📅 **Data e hora do atendimento (Brasília):** {data_br}")

        funcionario = st.text_input("Nome do funcionário atendido")
        quem = st.text_input("Quem realizou o atendimento")
        motivo = st.text_area("Motivo do contato")
        meio = st.selectbox("Meio de atendimento", ["Telefone", "WhatsApp", "E-mail", "Presencial", "Solicitação Interna"])

        assunto = st.selectbox(
            "Assunto",
            [
                "Salário",
                "Salário Família",
                "Movimentações Megaged",
                "Vale Transporte",
                "Vale Alimentação / Refeição",
                "Retorno ao Trabalho",
                "Solicitações"
            ],
        )

        numero_chamado = gerar_ticket()
        st.write(f"🎫 **Número do chamado:** `{numero_chamado}`")

        if st.button("💾 Salvar atendimento"):

            dados = {
                "user_id": st.session_state.user.id,
                "criado_por": st.session_state.user.email,
                "data_atendimento": agora_utc_iso,
                "ultima_atualizacao": agora_utc_iso,
                "quem_realizou": quem,
                "funcionario_atendido": funcionario,
                "motivo_contato": motivo,
                "meio_atendimento": meio,
                "assunto": assunto,
                "andamento": "Aguardando",
                "numero_chamado": numero_chamado,
                "tratativa": None,
                "data_conclusao": None,
            }

            criar_atendimento(dados)
            st.success("✅ Atendimento registrado!")
            time.sleep(1)
            st.rerun()

# =========================================================
# LISTAR ATENDIMENTOS
# =========================================================
if opcao == "Listar Atendimentos":

    st.subheader("📋 Atendimentos Registrados")

    if IS_ADMIN:
        dados = listar_atendimentos(None, admin=True).data
    else:
        dados = listar_atendimentos(st.session_state.user.id).data

    if not dados:
        st.info("Nenhum atendimento encontrado.")
        st.stop()

    # -------------------------------------------------------
    # FILTROS
    # -------------------------------------------------------
    with st.expander("🔍 Filtros de pesquisa", expanded=True):

        col1, col2, col3, col4 = st.columns(4)

        # — STATUS + EXCLUÍDOS
        with col1:
            status_selecionados = st.multiselect(
                "Status",
                ["Aguardando", "Concluído"],
                default=["Aguardando", "Concluído"],
            )
            incluir_excluidos = st.checkbox("Incluir excluídos")

        # — ASSUNTO
        with col2:
            assuntos = sorted({d.get("assunto") for d in dados if d.get("assunto")})
            filtro_assunto = st.selectbox("Assunto", ["Todos"] + assuntos)

        # — PERÍODO
        with col3:
            filtrar_periodo = st.checkbox("Filtrar por período")
            if filtrar_periodo:
                data_inicio = st.date_input("Data inicial", date.today() - timedelta(days=7))
                data_fim = st.date_input("Data final", date.today())
            else:
                data_inicio = data_fim = None

        # — CHAMADO
        with col4:
            filtro_chamado = st.text_input("Número do chamado")

        # -------------------------------------------------------
        # NOVOS FILTROS (OPÇÃO A)
        # -------------------------------------------------------
        colA, colB = st.columns(2)

        with colA:
            filtro_funcionario = st.text_input("Funcionário")

        with colB:
            filtro_quem_realizou = st.text_input("Atendente")

    # -------------------------------------------------------
    # APLICAR FILTROS
    # -------------------------------------------------------
    filtrados = []

    for row in dados:
        status = row.get("andamento")

        if status == "Excluído" and not incluir_excluidos:
            continue

        if status != "Excluído" and status not in status_selecionados:
            continue

        if filtro_assunto != "Todos" and row.get("assunto") != filtro_assunto:
            continue

        if filtro_chamado and filtro_chamado.strip() not in str(row.get("numero_chamado")):
            continue

        # — FILTRAR FUNCIONÁRIO
        if filtro_funcionario and filtro_funcionario.lower() not in (row.get("funcionario_atendido") or "").lower():
            continue

        # — FILTRAR QUEM REALIZOU
        if filtro_quem_realizou and filtro_quem_realizou.lower() not in (row.get("quem_realizou") or "").lower():
            continue

        dt_abertura_br = from_db_to_br(row.get("data_atendimento"))

        if filtrar_periodo and dt_abertura_br:
            if not (data_inicio <= dt_abertura_br.date() <= data_fim):
                continue

        filtrados.append(row)

    if not filtrados:
        st.info("Nenhum resultado com os filtros aplicados.")
        st.stop()

    # -------------------------------------------------------
    # PAGINAÇÃO
    # -------------------------------------------------------
    itens_por_pagina = 5
    total_registros = len(filtrados)
    total_paginas = (total_registros + itens_por_pagina - 1) // itens_por_pagina

    if "pagina_atual" not in st.session_state:
        st.session_state.pagina_atual = 1

    inicio = (st.session_state.pagina_atual - 1) * itens_por_pagina
    fim = inicio + itens_por_pagina
    pagina_dados = filtrados[inicio:fim]

    # -------------------------------------------------------
    # EXIBIÇÃO DOS REGISTROS
    # -------------------------------------------------------
    for row in pagina_dados:

        dt_abertura_br = from_db_to_br(row.get("data_atendimento"))
        dt_update_br = from_db_to_br(row.get("ultima_atualizacao"))

        abertura_br = dt_abertura_br.strftime("%d/%m/%Y") if dt_abertura_br else "—"
        update_br = dt_update_br.strftime("%d/%m/%Y") if dt_update_br else "—"

        bg, borda, icon = estilo_por_status(row.get("andamento"))

        criador_html = f"<p>👤 <b>Criado por:</b> {row.get('criado_por')}</p>" if IS_ADMIN else ""

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

  {criador_html}

  <p>📅 <b>Abertura:</b> {abertura_br}</p>
  <p>🟢 <b>Última atualização:</b> {update_br}</p>

  <p>{icon} <b>Status:</b> {row.get('andamento')}</p>
  <p>📝 <b>Tratativa:</b> {row.get('tratativa') or "—"}</p>
</div>
""",
            unsafe_allow_html=True,
        )

        pode_editar = IS_ADMIN or (row.get("user_id") == st.session_state.user.id)

        if pode_editar:
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
                        ["Telefone", "WhatsApp", "E-mail", "Presencial", "Solicitação Interna"],
                        index=["Telefone", "WhatsApp", "E-mail", "Presencial", "Solicitação Interna"].index(row.get("meio_atendimento")),
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
                    agora_utc_iso = agora_utc().isoformat()

                    update_data = {
                        "funcionario_atendido": novo_funcionario,
                        "quem_realizou": novo_quem,
                        "meio_atendimento": novo_meio,
                        "assunto": novo_assunto,
                        "andamento": novo_status,
                        "tratativa": nova_tratativa,
                        "ultima_atualizacao": agora_utc_iso,
                    }

                    if novo_status == "Concluído" and not row.get("data_conclusao"):
                        update_data["data_conclusao"] = agora_utc_iso

                    atualizar_atendimento(row["id"], update_data)
                    st.success("Alterações salvas!")
                    time.sleep(0.5)
                    st.rerun()

        if pode_editar and row.get("andamento") != "Excluído":
            if st.button(f"🗑️ Excluir atendimento", key=f"del_{row['id']}"):
                agora_utc_iso = agora_utc().isoformat()
                atualizar_atendimento(row["id"], {
                    "andamento": "Excluído",
                    "ultima_atualizacao": agora_utc_iso
                })
                st.warning("Atendimento excluído!")
                time.sleep(0.5)
                st.rerun()

        st.markdown("---")

    # -------------------------------------------------------
    # PAGINAÇÃO (NO FINAL)
    # -------------------------------------------------------
    col_pag1, col_pag2, col_pag3 = st.columns([1, 2, 1])

    with col_pag1:
        if st.button("⬅️ Anterior") and st.session_state.pagina_atual > 1:
            st.session_state.pagina_atual -= 1
            st.rerun()

    with col_pag3:
        if st.button("Próxima ➡️") and st.session_state.pagina_atual < total_paginas:
            st.session_state.pagina_atual += 1
            st.rerun()

    st.write(f"📄 Página {st.session_state.pagina_atual} de {total_paginas}")
