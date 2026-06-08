"""
Tipos base da Arquitetura Claude Code — Oráculo Analista
Define as estruturas de dados usadas em todo o sistema.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
import time


class ToolStatus(Enum):
    """Status de execução de uma tool."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    DENIED = "denied"


class MessageRole(Enum):
    """Papéis possíveis em uma mensagem."""
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    SYSTEM = "system"


@dataclass
class ToolCall:
    """Representa uma chamada de tool solicitada pelo LLM."""
    tool_name: str
    tool_id: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict:
        return {
            "tool_name": self.tool_name,
            "tool_id": self.tool_id,
            "parameters": self.parameters,
            "timestamp": self.timestamp,
        }


@dataclass
class ToolResult:
    """Resultado da execução de uma tool."""
    tool_id: str
    tool_name: str
    status: ToolStatus
    output: Any = None
    error: Optional[str] = None
    tokens_used: int = 0
    duration_ms: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "tool_id": self.tool_id,
            "tool_name": self.tool_name,
            "status": self.status.value,
            "output": str(self.output) if self.output else None,
            "error": self.error,
            "tokens_used": self.tokens_used,
            "duration_ms": self.duration_ms,
        }

    @property
    def success(self) -> bool:
        return self.status == ToolStatus.SUCCESS


@dataclass
class Message:
    """Mensagem no histórico de uma sessão."""
    role: MessageRole
    content: str
    tool_call: Optional[ToolCall] = None
    tool_result: Optional[ToolResult] = None
    timestamp: float = field(default_factory=time.time)

    def to_groq_format(self) -> Dict:
        """Converte para o formato esperado pela API Groq."""
        msg: Dict[str, Any] = {
            "role": self.role.value,
            "content": self.content,
        }
        if self.tool_call:
            msg["tool_calls"] = [{
                "id": self.tool_call.tool_id,
                "type": "function",
                "function": {
                    "name": self.tool_call.tool_name,
                    "arguments": str(self.tool_call.parameters),
                },
            }]
        return msg


@dataclass
class UserProfile:
    """Perfil completo de um usuário do sistema."""
    user_id: str
    name: str
    email: str
    plan: str = "free"
    created_at: float = field(default_factory=time.time)
    memory_path: str = ""
    total_tokens_used: int = 0
    sessions_count: int = 0

    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "plan": self.plan,
            "created_at": self.created_at,
            "memory_path": self.memory_path,
            "total_tokens_used": self.total_tokens_used,
            "sessions_count": self.sessions_count,
        }


@dataclass
class SessionState:
    """Estado completo de uma sessão em andamento."""
    session_id: str
    user: UserProfile
    messages: List[Message] = field(default_factory=list)
    active_document: Optional[str] = None
    document_content: Optional[str] = None
    tool_calls_count: int = 0
    total_tokens: int = 0
    started_at: float = field(default_factory=time.time)
    is_active: bool = True

    def add_message(self, message: Message) -> None:
        self.messages.append(message)

    def get_history_for_groq(self) -> List[Dict]:
        """Retorna histórico no formato esperado pelo Groq."""
        return [m.to_groq_format() for m in self.messages]

    @property
    def message_count(self) -> int:
        return len(self.messages)
