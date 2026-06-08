"""
Armazenamento e recuperação de sessões do Oráculo Analista.

Responsabilidades:
  - Salvar sessões encerradas em JSON para auditoria
  - Recuperar sessões anteriores de um usuário
  - Listar sessões ativas e histórico

Estrutura de arquivos:
  user_profiles/{user_id}/sessions/{session_id}.json
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.constants.settings import MEMORY_DIR
from src.types.base import SessionState


class SessionStore:
    """
    Persistência de sessões por usuário.
    Cada sessão encerrada é salva como um arquivo JSON.
    """

    def __init__(self, user_id: str):
        self.user_id = user_id
        self.sessions_dir = Path(MEMORY_DIR) / user_id / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def save(self, session: SessionState) -> bool:
        """
        Persiste uma sessão encerrada em disco.
        Retorna True se salvo com sucesso.
        """
        try:
            session_data = {
                "session_id": session.session_id,
                "user_id": session.user.user_id,
                "user_name": session.user.name,
                "started_at": session.started_at,
                "ended_at": datetime.now().timestamp(),
                "message_count": session.message_count,
                "tool_calls_count": session.tool_calls_count,
                "total_tokens": session.total_tokens,
                "active_document": session.active_document,
                "messages": [
                    {
                        "role": m.role.value,
                        "content": m.content[:500],  # truncado para economizar espaço
                        "timestamp": m.timestamp,
                    }
                    for m in session.messages
                ],
            }

            filepath = self.sessions_dir / f"{session.session_id}.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def load(self, session_id: str) -> Optional[Dict]:
        """
        Carrega os dados de uma sessão específica pelo ID.
        Retorna None se não encontrada.
        """
        filepath = self.sessions_dir / f"{session_id}.json"
        if not filepath.exists():
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def list_sessions(self, limit: int = 10) -> List[Dict]:
        """
        Lista as sessões mais recentes do usuário.
        Retorna metadados resumidos (sem o histórico completo de mensagens).
        """
        session_files = sorted(
            self.sessions_dir.glob("*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True  # mais recentes primeiro
        )[:limit]

        sessions = []
        for filepath in session_files:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Retorna apenas metadados, sem as mensagens
                sessions.append({
                    "session_id": data.get("session_id"),
                    "started_at": data.get("started_at"),
                    "ended_at": data.get("ended_at"),
                    "message_count": data.get("message_count", 0),
                    "tool_calls_count": data.get("tool_calls_count", 0),
                    "total_tokens": data.get("total_tokens", 0),
                    "active_document": data.get("active_document"),
                })
            except (json.JSONDecodeError, IOError):
                continue

        return sessions

    def get_total_sessions(self) -> int:
        """Retorna o número total de sessões salvas do usuário."""
        return len(list(self.sessions_dir.glob("*.json")))

    def get_last_session(self) -> Optional[Dict]:
        """Retorna os dados da sessão mais recente do usuário."""
        sessions = self.list_sessions(limit=1)
        return sessions[0] if sessions else None

    def cleanup_old_sessions(self, keep_last: int = 50) -> int:
        """
        Remove sessões antigas, mantendo apenas as N mais recentes.
        Retorna o número de arquivos removidos.
        """
        all_files = sorted(
            self.sessions_dir.glob("*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )
        to_delete = all_files[keep_last:]
        for f in to_delete:
            try:
                f.unlink()
            except OSError:
                pass
        return len(to_delete)
