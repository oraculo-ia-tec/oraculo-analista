# ============================================================
# src/tools/file_tools.py
# Tool de leitura de arquivos carregados pelo usuário
# ============================================================
import streamlit as st


class FileReadTool:
    """
    Lê o conteúdo dos arquivos carregados na sessão atual.
    Retorna um resumo estruturado pronto para o LLM.
    """

    name        = "file_read"
    description = "Lê e resume os arquivos carregados pelo usuário na sessão."
    permission  = "file_read"

    def __call__(self, file_name: str | None = None) -> str:
        arquivos = st.session_state.get("arquivos_processados", [])

        if not arquivos:
            return "Nenhum arquivo carregado na sessão."

        if file_name:
            arquivos = [a for a in arquivos if a.get("name") == file_name]
            if not arquivos:
                return f"Arquivo '{file_name}' não encontrado na sessão."

        blocos = []
        for arq in arquivos:
            nome  = arq.get("name", "arquivo")
            tipo  = arq.get("type", "?")
            pags  = arq.get("pages")
            texto = (arq.get("text", "") or "")[:6000]

            meta = f"📄 {nome} [{tipo.upper()}]"
            if pags:
                meta += f" — {pags} páginas"
            blocos.append(f"{meta}\n{texto}")

        return "\n\n---\n\n".join(blocos)
