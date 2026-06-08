"""
Loader central de todas as tools.
Importe este módulo UMA VEZ na inicialização do sistema
para garantir que todas as tools sejam registradas no ToolRegistry.
"""

# A simples importação de cada módulo já dispara o ToolRegistry.register()
# ao final de cada arquivo de tool (padrão auto-registro).
from src.tools import tool_pdf      # noqa: F401
from src.tools import tool_excel    # noqa: F401
from src.tools import tool_txt      # noqa: F401
from src.tools import tool_email    # noqa: F401
from src.tools import tool_asaas    # noqa: F401


def load_all_tools() -> None:
    """
    Função explícita de carregamento.
    Chame no bootstrap da aplicação para garantir o registro.
    """
    from src.tools.base import ToolRegistry
    tools = ToolRegistry.list_names()
    print(f"[ToolRegistry] {len(tools)} tool(s) carregada(s): {tools}")
