"""
Gerenciador de memória persistente por usuário — padrão AutoDream.

Cada usuário possui um arquivo MEMORY.md em:
  user_profiles/{user_id}/MEMORY.md

Este arquivo é carregado automaticamente no início de cada sessão
e atualizado ao final de cada interação significativa.

Estrutura do MEMORY.md:
  ## Perfil
  ## Documentos Analisados
  ## Preferências Identificadas
  ## Insights Salvos
  ## Histórico de Sessões
"""
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.constants.settings import MEMORY_DIR
from src.utils.helpers import safe_read_file, safe_write_file


class MemoryManager:
    """
    Gerencia a memória persistente de um usuário.
    Cada instância é ligada a um user_id específico.
    """

    MEMORY_FILENAME = "MEMORY.md"
    MAX_INSIGHTS = 50        # máximo de insights salvos
    MAX_SESSIONS_LOG = 20    # máximo de sessões no histórico
    MAX_DOCUMENTS_LOG = 30   # máximo de documentos registrados

    def __init__(self, user_id: str, user_name: str = "", user_email: str = ""):
        self.user_id = user_id
        self.user_name = user_name
        self.user_email = user_email
        self.memory_path = Path(MEMORY_DIR) / user_id / self.MEMORY_FILENAME
        self._ensure_memory_exists()

    # ─── Inicialização ──────────────────────────────────────────────────────────────

    def _ensure_memory_exists(self) -> None:
        """Cria o arquivo MEMORY.md se ainda não existir."""
        if not self.memory_path.exists():
            self.memory_path.parent.mkdir(parents=True, exist_ok=True)
            initial_content = self._build_initial_memory()
            safe_write_file(str(self.memory_path), initial_content)

    def _build_initial_memory(self) -> str:
        """Gera o conteúdo inicial do MEMORY.md para um novo usuário."""
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        return f"""# 🧠 Memória — {self.user_name or self.user_id}

> Arquivo gerenciado automaticamente pelo Oráculo Analista.
> Não edite manualmente. Última atualização: {now}

---

## 👤 Perfil
- **ID:** {self.user_id}
- **Nome:** {self.user_name or 'Não informado'}
- **E-mail:** {self.user_email or 'Não informado'}
- **Cadastro:** {now}
- **Plano:** free

---

## 📄 Documentos Analisados

_(nenhum documento analisado ainda)_

---

## ⚙️ Preferências Identificadas

_(nenhuma preferência registrada ainda)_

---

## 💡 Insights Salvos

_(nenhum insight salvo ainda)_

---

## 📊 Histórico de Sessões

_(nenhuma sessão registrada ainda)_
"""

    # ─── Leitura ───────────────────────────────────────────────────────────────────

    def load(self) -> str:
        """
        Carrega e retorna o conteúdo completo do MEMORY.md.
        Chamado no início de cada sessão para injetar no system prompt.
        """
        return safe_read_file(str(self.memory_path))

    def load_section(self, section_title: str) -> str:
        """
        Carrega apenas uma seção específica do MEMORY.md.
        Exemplo: load_section("Documentos Analisados")
        """
        content = self.load()
        lines = content.split("\n")
        in_section = False
        section_lines = []

        for line in lines:
            if line.startswith("## ") and section_title in line:
                in_section = True
                continue
            if in_section and line.startswith("## "):
                break
            if in_section:
                section_lines.append(line)

        return "\n".join(section_lines).strip()

    # ─── Escrita (AutoDream) ───────────────────────────────────────────────────────

    def record_document(self, filename: str, summary: str, pages: int = 0) -> None:
        """
        Registra um documento analisado na memória do usuário.
        Chamado automaticamente ao final da análise de um documento.
        """
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        new_entry = f"- **{filename}** ({now}) — {pages} pág. | {summary[:120]}..."
        self._update_section(
            section="Documentos Analisados",
            new_entry=new_entry,
            max_entries=self.MAX_DOCUMENTS_LOG,
            placeholder="_(nenhum documento analisado ainda)_",
        )

    def save_insight(self, insight: str, source_document: str = "") -> None:
        """
        Salva um insight gerado durante a análise.
        Chamado quando o LLM identifica informação relevante para guardar.
        """
        now = datetime.now().strftime("%d/%m/%Y")
        source = f" _[{source_document}]_" if source_document else ""
        new_entry = f"- ({now}){source} {insight[:200]}"
        self._update_section(
            section="Insights Salvos",
            new_entry=new_entry,
            max_entries=self.MAX_INSIGHTS,
            placeholder="_(nenhum insight salvo ainda)_",
        )

    def record_preference(self, preference: str) -> None:
        """
        Registra uma preferência identificada do usuário.
        Ex: "Prefere respostas em formato de tabela"
        """
        new_entry = f"- {preference}"
        self._update_section(
            section="Preferências Identificadas",
            new_entry=new_entry,
            max_entries=20,
            placeholder="_(nenhuma preferência registrada ainda)_",
        )

    def record_session(self, session_id: str, summary: str, tools_used: List[str]) -> None:
        """
        Registra o resumo de uma sessão encerrada.
        Chamado automaticamente ao fechar a sessão no runtime.
        """
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        tools_str = ", ".join(tools_used) if tools_used else "nenhuma"
        new_entry = (
            f"- **{now}** | ID: `{session_id[:8]}` | "
            f"Tools: {tools_str} | {summary[:150]}"
        )
        self._update_section(
            section="Histórico de Sessões",
            new_entry=new_entry,
            max_entries=self.MAX_SESSIONS_LOG,
            placeholder="_(nenhuma sessão registrada ainda)_",
        )
        # Atualiza timestamp no cabeçalho
        self._update_timestamp()

    def update_plan(self, new_plan: str) -> None:
        """
        Atualiza o plano do usuário na seção Perfil.
        """
        content = self.load()
        content = content.replace(
            "- **Plano:** free",
            f"- **Plano:** {new_plan}"
        ).replace(
            "- **Plano:** pro",
            f"- **Plano:** {new_plan}"
        ).replace(
            "- **Plano:** enterprise",
            f"- **Plano:** {new_plan}"
        )
        safe_write_file(str(self.memory_path), content)

    # ─── Métodos internos ─────────────────────────────────────────────────────────

    def _update_section(
        self,
        section: str,
        new_entry: str,
        max_entries: int,
        placeholder: str,
    ) -> None:
        """
        Adiciona uma nova entrada em uma seção do MEMORY.md.
        Remove entradas antigas se ultrapassar o limite.
        """
        content = self.load()
        lines = content.split("\n")
        new_lines = []
        in_section = False
        section_entries = []
        section_start_idx = None
        section_end_idx = None

        for i, line in enumerate(lines):
            if line.startswith("## ") and section in line:
                in_section = True
                section_start_idx = i
                continue
            if in_section and line.startswith("## "):
                in_section = False
                section_end_idx = i
                break
            if in_section and line.startswith("- "):
                section_entries.append(line)

        if section_start_idx is None:
            return  # seção não encontrada

        # Remove placeholder se presente
        section_entries = [e for e in section_entries if placeholder not in e]

        # Adiciona nova entrada no topo (mais recente primeiro)
        section_entries.insert(0, new_entry)

        # Limita ao máximo
        section_entries = section_entries[:max_entries]

        # Reconstrói o conteúdo
        new_content_lines = []
        i = 0
        while i < len(lines):
            if i == section_start_idx:
                new_content_lines.append(lines[i])  # header da seção
                new_content_lines.append("")         # linha em branco
                new_content_lines.extend(section_entries)
                # Pula linhas antigas da seção
                i += 1
                while i < len(lines) and (not lines[i].startswith("## ") or section in lines[i - 1]):
                    if lines[i].startswith("## ") and section not in lines[i]:
                        break
                    i += 1
                continue
            new_content_lines.append(lines[i])
            i += 1

        safe_write_file(str(self.memory_path), "\n".join(new_content_lines))

    def _update_timestamp(self) -> None:
        """Atualiza o timestamp no cabeçalho do MEMORY.md."""
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        content = self.load()
        import re
        content = re.sub(
            r"> Arquivo gerenciado automaticamente.*",
            f"> Arquivo gerenciado automaticamente pelo Oráculo Analista. "
            f"Última atualização: {now}",
            content
        )
        safe_write_file(str(self.memory_path), content)

    # ─── Utilitários ─────────────────────────────────────────────────────────────────

    def get_context_for_prompt(self) -> str:
        """
        Retorna um bloco compacto da memória para injetar no system prompt.
        Inclui apenas as informações mais relevantes para economizar tokens.
        """
        documents = self.load_section("Documentos Analisados")
        insights = self.load_section("Insights Salvos")
        preferences = self.load_section("Preferências Identificadas")

        parts = []
        if documents and "nenhum documento" not in documents:
            # Apenas os 5 documentos mais recentes
            doc_lines = [l for l in documents.split("\n") if l.startswith("- ")][:5]
            parts.append("**Documentos recentes do usuário:**\n" + "\n".join(doc_lines))

        if insights and "nenhum insight" not in insights:
            # Apenas os 10 insights mais recentes
            insight_lines = [l for l in insights.split("\n") if l.startswith("- ")][:10]
            parts.append("**Insights anteriores:**\n" + "\n".join(insight_lines))

        if preferences and "nenhuma preferência" not in preferences:
            parts.append("**Preferências do usuário:**\n" + preferences)

        if not parts:
            return "_(sem histórico anterior para este usuário)_"

        return "\n\n".join(parts)

    @property
    def exists(self) -> bool:
        """Retorna True se o arquivo MEMORY.md existe."""
        return self.memory_path.exists()

    @property
    def size_kb(self) -> float:
        """Retorna o tamanho do MEMORY.md em KB."""
        if not self.memory_path.exists():
            return 0.0
        return self.memory_path.stat().st_size / 1024
