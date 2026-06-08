"""
Classe base e registro de todas as tools do Oráculo Analista.
Toda nova tool deve herdar de BaseTool e se registrar no ToolRegistry.
"""
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from src.types.base import ToolCall, ToolResult, ToolStatus


class BaseTool(ABC):
    """
    Interface que toda tool deve implementar.
    Padrão direto do claw-code: cada tool é auto-descritiva
    e sabe validar seus próprios parâmetros.
    """

    # --- Metadados obrigatórios (definidos na subclasse) ---
    name: str = ""          # identificador único usado pelo LLM
    description: str = ""  # descrição que o LLM vê para decidir quando usar
    plan_required: str = "free"  # plano mínimo: "free", "pro", "enterprise"

    @property
    @abstractmethod
    def parameters_schema(self) -> Dict:
        """
        Schema JSON dos parâmetros aceitos.
        Enviado ao Groq como parte da definição da tool.
        """
        ...

    @abstractmethod
    def _execute(self, parameters: Dict[str, Any]) -> Any:
        """
        Lógica principal da tool. Implementada por cada subclasse.
        Retorna o output bruto (string, dict, list, etc.).
        """
        ...

    def validate(self, parameters: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validação opcional de parâmetros antes da execução.
        Sobrescreva nas subclasses para validações específicas.
        Retorna (is_valid, error_message).
        """
        return True, ""

    def execute(self, tool_call: ToolCall) -> ToolResult:
        """
        Método público de execução. Não sobrescrever nas subclasses.
        Controla: validação → execução → tratamento de erro → métricas.
        """
        start = time.time()

        # 1. Valida parâmetros
        is_valid, error_msg = self.validate(tool_call.parameters)
        if not is_valid:
            return ToolResult(
                tool_id=tool_call.tool_id,
                tool_name=self.name,
                status=ToolStatus.ERROR,
                error=f"Validação falhou: {error_msg}",
                duration_ms=(time.time() - start) * 1000,
            )

        # 2. Executa
        try:
            output = self._execute(tool_call.parameters)
            return ToolResult(
                tool_id=tool_call.tool_id,
                tool_name=self.name,
                status=ToolStatus.SUCCESS,
                output=output,
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return ToolResult(
                tool_id=tool_call.tool_id,
                tool_name=self.name,
                status=ToolStatus.ERROR,
                error=f"Erro na execução de '{self.name}': {str(e)}",
                duration_ms=(time.time() - start) * 1000,
            )

    def to_groq_schema(self) -> Dict:
        """
        Formata a tool no schema esperado pela API Groq/OpenAI.
        Usado pelo query_engine ao montar a lista de tools disponíveis.
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema,
            },
        }


class ToolRegistry:
    """
    Registro central de todas as tools disponíveis.
    O query_engine consulta o registry para saber quais tools
    enviar ao Groq e para rotear as tool_calls de volta.
    """
    _tools: Dict[str, BaseTool] = {}

    @classmethod
    def register(cls, tool: BaseTool) -> None:
        """Registra uma tool pelo seu nome."""
        cls._tools[tool.name] = tool

    @classmethod
    def get(cls, name: str) -> Optional[BaseTool]:
        """Recupera uma tool pelo nome. Retorna None se não encontrada."""
        return cls._tools.get(name)

    @classmethod
    def get_all(cls) -> List[BaseTool]:
        """Retorna todas as tools registradas."""
        return list(cls._tools.values())

    @classmethod
    def get_for_plan(cls, plan: str) -> List[BaseTool]:
        """
        Retorna apenas as tools permitidas para um plano.
        Garante que usuários free não acessem tools premium.
        """
        plan_order = {"free": 0, "pro": 1, "enterprise": 2}
        user_level = plan_order.get(plan, 0)
        return [
            t for t in cls._tools.values()
            if plan_order.get(t.plan_required, 0) <= user_level
        ]

    @classmethod
    def get_schemas_for_plan(cls, plan: str) -> List[Dict]:
        """Retorna os schemas Groq das tools permitidas para um plano."""
        return [t.to_groq_schema() for t in cls.get_for_plan(plan)]

    @classmethod
    def list_names(cls) -> List[str]:
        """Retorna os nomes de todas as tools registradas."""
        return list(cls._tools.keys())
