# ============================================================
# src/tools/export_tool.py
# Tool de exportação de conversas (Excel e PDF)
# ============================================================
from __future__ import annotations

import io
from datetime import datetime

import pandas as pd


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

    # ── internals ────────────────────────────────────────────

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

            buf = io.BytesIO()
            c   = canvas.Canvas(buf, pagesize=A4)
            w, h = A4
            y    = h - 40

            c.setFont("Helvetica-Bold", 14)
            c.drawString(40, y, "Oráculo Analista — Histórico de Conversa")
            y -= 30

            c.setFont("Helvetica", 10)
            for msg in messages:
                role = msg.get("role", "").upper()
                text = msg.get("content", "")
                lines = [f"{role}: {text[i:i+100]}" for i in range(0, len(text), 100)]
                for line in lines:
                    if y < 40:
                        c.showPage()
                        y = h - 40
                        c.setFont("Helvetica", 10)
                    c.drawString(40, y, line)
                    y -= 14
                y -= 6

            c.save()
            return buf.getvalue()

        except ImportError:
            # fallback sem reportlab
            lines = [f"{m.get('role','').upper()}: {m.get('content','')}" for m in messages]
            return "\n".join(lines).encode("utf-8")
