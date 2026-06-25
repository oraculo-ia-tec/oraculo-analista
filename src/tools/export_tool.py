# ============================================================
# src/tools/export_tool.py
# Tool de exportação de conversas (Excel e PDF)
# ============================================================
from __future__ import annotations

import io
import os
import unicodedata
from datetime import datetime

import pandas as pd


def _sanitize(text: str) -> str:
    """
    Remove caracteres fora do plano BMP (emojis, alguns Unicode)
    e normaliza para NFC para compatibilidade com ReportLab+Helvetica.
    Usado apenas como fallback se a fonte Unicode não estiver disponível.
    """
    text = "".join(c for c in text if ord(c) < 0xFFFF)
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\u2014", "--").replace("\u2013", "-")
    text = "".join(c if ord(c) < 128 or unicodedata.category(c) not in ("Cs", "Co") else "?" for c in text)
    return text


class ExportTool:
    name        = "export"
    description = "Exporta o histórico de conversa para Excel ou PDF."
    permission  = "allow"

    def __call__(self, format: str = "excel", messages: list | None = None, **kwargs):
        msgs = messages or []
        if format == "excel":
            return self._to_excel(msgs)
        if format == "pdf":
            return self._to_pdf(msgs)
        raise ValueError(f"Formato '{format}' não suportado. Use 'excel' ou 'pdf'.")

    # ── internals ─────────────────────────────────────────────────

    def _to_excel(self, messages: list) -> bytes:
        rows = [
            {
                "#":        i + 1,
                "Papel":    m.get("role", "").capitalize(),
                "Mensagem": m.get("content", ""),
                "Hora":     datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            for i, m in enumerate(messages)
        ]
        df  = pd.DataFrame(rows)
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Conversa")
        return buf.getvalue()

    def _to_pdf(self, messages: list) -> bytes:
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont

            buf  = io.BytesIO()
            c    = canvas.Canvas(buf, pagesize=A4)
            w, h = A4
            y    = h - 40

            # ── Registra fonte Unicode para suportar acentos, travessões e emojis ──
            FONT_BODY  = "Helvetica"
            FONT_BOLD  = "Helvetica-Bold"
            unicode_ok = False

            # Caminhos comuns do DejaVu no sistema (funciona no Streamlit Cloud)
            _dejavu_body_candidates = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "./src/fonts/DejaVuSans.ttf",
            ]
            _dejavu_bold_candidates = [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "./src/fonts/DejaVuSans-Bold.ttf",
            ]

            body_path = next((p for p in _dejavu_body_candidates if os.path.exists(p)), None)
            bold_path = next((p for p in _dejavu_bold_candidates if os.path.exists(p)), None)

            if body_path:
                try:
                    pdfmetrics.registerFont(TTFont("DejaVuSans", body_path))
                    FONT_BODY  = "DejaVuSans"
                    unicode_ok = True
                except Exception:
                    pass

            if bold_path:
                try:
                    pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", bold_path))
                    FONT_BOLD = "DejaVuSans-Bold"
                except Exception:
                    pass

            # Título
            c.setFont(FONT_BOLD, 14)
            titulo = (
                "Oráculo Analista \u2014 Histórico de Conversa"
                if unicode_ok
                else "Oraculo Analista - Historico de Conversa"
            )
            c.drawString(40, y, titulo)
            y -= 30

            c.setFont(FONT_BODY, 10)

            for msg in messages:
                role = msg.get("role", "").upper()
                text = msg.get("content", "")

                # Se a fonte não suporta Unicode completo, sanitiza o texto
                if not unicode_ok:
                    text = _sanitize(text)
                else:
                    # Mesmo com DejaVu, remove emojis multi-codepoint acima de U+FFFF
                    text = "".join(ch for ch in text if ord(ch) <= 0xFFFF)

                texto_completo = f"{role}: {text}"
                chunk_size     = 95
                lines = [
                    texto_completo[i:i + chunk_size]
                    for i in range(0, len(texto_completo), chunk_size)
                ]

                for line in lines:
                    if y < 40:
                        c.showPage()
                        y = h - 40
                        c.setFont(FONT_BODY, 10)
                    c.drawString(40, y, line)
                    y -= 14
                y -= 6  # espaço entre mensagens

            c.save()
            return buf.getvalue()

        except ImportError:
            # fallback sem reportlab: retorna TXT simples como bytes
            lines = [f"{m.get('role','').upper()}: {m.get('content','')}" for m in messages]
            return "\n".join(lines).encode("utf-8")
