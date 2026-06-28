# ============================================================
# agenda_analista.py  —  Oráculo Analista
# Classe AgendaAnalista: detecta intenção e exibe formulário
# personalizado de agendamento de reunião.
# ============================================================
from __future__ import annotations

import streamlit as st
from notification import Notificador


# ============================================================
# Palavras-chave que disparam a intenção de agendamento
# ============================================================
_KEYWORDS_AGENDA = [
    "reunião", "reuniao", "agendar", "agendamento",
    "consultoria", "falar com o desenvolvedor",
    "encontro", "marcar horário", "marcar horario",
    "quero conversar", "falar com alguém", "suporte presencial",
]

# CSS da borda do card do formulário
_CARD_CSS = """
<style>
.agenda-card {
    border: 1.5px solid #a084ca;
    border-radius: 14px;
    padding: 28px 32px 20px 32px;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    box-shadow: 0 4px 24px 0 rgba(160,132,202,0.18);
    margin-bottom: 18px;
}
.agenda-titulo {
    font-size: 1.35rem;
    font-weight: 700;
    background: linear-gradient(90deg, #a084ca, #e0c3fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 4px;
}
.agenda-subtitulo {
    font-size: 0.95rem;
    color: #b0b8d1;
    margin-bottom: 18px;
}
</style>
"""


class AgendaAnalista:
    """
    Gerencia detecção de intenção de agendamento e
    exibição do formulário personalizado no chat.
    """

    # ----------------------------------------------------------
    # 1. Detecção de intenção
    # ----------------------------------------------------------
    @staticmethod
    def detectar_intencao(prompt: str) -> bool:
        """Retorna True se o prompt contiver intenção de agendamento."""
        texto = prompt.lower().strip()
        return any(kw in texto for kw in _KEYWORDS_AGENDA)

    # ----------------------------------------------------------
    # 2. Validação dos campos
    # ----------------------------------------------------------
    @staticmethod
    def _validar_campos(nome: str, whatsapp: str, email: str) -> list[str]:
        """Retorna lista de erros de validação."""
        erros = []
        if not nome.strip():
            erros.append("Nome completo é obrigatório.")
        if not whatsapp.strip():
            erros.append("WhatsApp é obrigatório.")
        if not email.strip() or "@" not in email:
            erros.append("E-mail válido é obrigatório.")
        return erros

    # ----------------------------------------------------------
    # 3. Envio da confirmação por e-mail
    # ----------------------------------------------------------
    @staticmethod
    def _enviar_confirmacao(
        nome: str,
        email: str,
        whatsapp: str,
        empresa: str,
        assunto_reuniao: str,
        data: str,
        hora: str,
        modalidade: str,
    ) -> None:
        """Envia e-mail de confirmação via SMTP Hostinger."""
        notificador = Notificador()

        # E-mail para o solicitante
        mensagem_cliente = f"""
        <div style="font-family:Arial,sans-serif;max-width:520px;margin:auto;">
          <h2 style="color:#a084ca;">&#128197; Agendamento Confirmado!</h2>
          <p>Olá, <strong>{nome}</strong>!</p>
          <p>Seu agendamento foi recebido com sucesso. Em breve entraremos em contato para confirmar.</p>
          <table style="width:100%;border-collapse:collapse;margin-top:16px;">
            <tr><td style="padding:8px;background:#1a1a2e;color:#e0c3fc;"><b>Data</b></td>
                <td style="padding:8px;background:#16213e;color:#fff;">{data}</td></tr>
            <tr><td style="padding:8px;background:#1a1a2e;color:#e0c3fc;"><b>Horário</b></td>
                <td style="padding:8px;background:#16213e;color:#fff;">{hora}</td></tr>
            <tr><td style="padding:8px;background:#1a1a2e;color:#e0c3fc;"><b>Modalidade</b></td>
                <td style="padding:8px;background:#16213e;color:#fff;">{modalidade}</td></tr>
            <tr><td style="padding:8px;background:#1a1a2e;color:#e0c3fc;"><b>Assunto</b></td>
                <td style="padding:8px;background:#16213e;color:#fff;">{assunto_reuniao}</td></tr>
          </table>
          <p style="margin-top:18px;color:#b0b8d1;font-size:0.9rem;">Oráculo Analista &mdash; Transformando dados em decisões.</p>
        </div>
        """
        notificador.enviar_email(
            destino=email,
            assunto="✅ Agendamento recebido — Oráculo Analista",
            mensagem=mensagem_cliente,
        )

        # Cópia interna para o remetente configurado
        remetente_interno = st.secrets.get("email", {}).get("EMAIL_REMETENTE", "")
        if remetente_interno:
            mensagem_interna = f"""
            <h3>Novo agendamento solicitado</h3>
            <ul>
              <li><b>Nome:</b> {nome}</li>
              <li><b>Empresa:</b> {empresa or 'Não informada'}</li>
              <li><b>WhatsApp:</b> {whatsapp}</li>
              <li><b>E-mail:</b> {email}</li>
              <li><b>Data:</b> {data}</li>
              <li><b>Horário:</b> {hora}</li>
              <li><b>Modalidade:</b> {modalidade}</li>
              <li><b>Assunto:</b> {assunto_reuniao}</li>
            </ul>
            """
            notificador.enviar_email(
                destino=remetente_interno,
                assunto=f"📅 Novo agendamento: {nome}",
                mensagem=mensagem_interna,
            )

    # ----------------------------------------------------------
    # 4. Formulário principal (público)
    # ----------------------------------------------------------
    def renderizar_formulario(self) -> None:
        """
        Renderiza o card de agendamento com bordas,
        duas colunas e envio de confirmação por e-mail.
        """
        st.markdown(_CARD_CSS, unsafe_allow_html=True)
        st.markdown(
            """
            <div class="agenda-card">
              <div class="agenda-titulo">&#128197; Agendar Reunião com o Consultor</div>
              <div class="agenda-subtitulo">
                Preencha os dados abaixo e entraremos em contato para confirmar.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("form_agenda_analista", clear_on_submit=True):

            # ─ Linha 1: Nome | Empresa
            col1, col2 = st.columns(2)
            with col1:
                nome = st.text_input("👤 Nome completo *")
            with col2:
                empresa = st.text_input("🏢 Empresa (opcional)")

            # ─ Linha 2: WhatsApp | E-mail
            col3, col4 = st.columns(2)
            with col3:
                whatsapp = st.text_input("📱 WhatsApp *", placeholder="(11) 99999-9999")
            with col4:
                email = st.text_input("📧 E-mail *", placeholder="seu@email.com")

            # ─ Linha 3: Data | Horário
            col5, col6 = st.columns(2)
            with col5:
                data = st.date_input("📆 Data preferida")
            with col6:
                hora = st.time_input("⏰ Horário preferido")

            # ─ Linha 4: Modalidade | Assunto
            col7, col8 = st.columns(2)
            with col7:
                modalidade = st.selectbox(
                    "💻 Modalidade",
                    ["Google Meet", "Microsoft Teams", "Zoom", "Presencial", "WhatsApp"],
                )
            with col8:
                assunto_reuniao = st.selectbox(
                    "📌 Assunto da reunião",
                    [
                        "Demonstração do Oráculo Analista",
                        "Consultoria estratégica",
                        "Suporte técnico",
                        "Planos e preços",
                        "Outro",
                    ],
                )

            # ─ Observações (largura total)
            observacoes = st.text_area(
                "📝 Observações (opcional)",
                placeholder="Descreva brevemente o que deseja abordar na reunião...",
                height=80,
            )

            enviado = st.form_submit_button(
                "📅 Confirmar Agendamento",
                use_container_width=True,
            )

        if enviado:
            erros = self._validar_campos(nome, whatsapp, email)
            if erros:
                for erro in erros:
                    st.warning(f"⚠️ {erro}")
            else:
                try:
                    self._enviar_confirmacao(
                        nome=nome,
                        email=email,
                        whatsapp=whatsapp,
                        empresa=empresa,
                        assunto_reuniao=assunto_reuniao,
                        data=str(data),
                        hora=str(hora),
                        modalidade=modalidade,
                    )
                    st.success(
                        f"✅ Obrigado, **{nome}**! "
                        "Seu agendamento foi recebido. "
                        "Você receberrá uma confirmação no e-mail informado."
                    )
                    st.balloons()
                except Exception as e:
                    st.error(f"❌ Erro ao enviar confirmação: {e}")
