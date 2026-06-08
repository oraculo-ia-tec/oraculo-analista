"""
Validadores de entrada de dados para o sistema.
Garante que inputs malformados nunca chegam ao LLM ou às tools.
"""
from typing import Any, Dict, Tuple
from pathlib import Path
from src.constants.settings import MAX_DOCUMENT_SIZE_MB, SUPPORTED_DOCUMENT_TYPES


def validate_tool_call(tool_name: str, parameters: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Valida se uma tool call tem todos os parâmetros necessários.
    Retorna (is_valid, error_message).
    """
    if not tool_name or not isinstance(tool_name, str):
        return False, "tool_name inválido ou ausente."
    if not isinstance(parameters, dict):
        return False, "parameters deve ser um dicionário."
    return True, ""


def validate_user_input(text: str) -> Tuple[bool, str]:
    """
    Valida o input do usuário antes de enviar ao LLM.
    Retorna (is_valid, error_message).
    """
    if not text or not isinstance(text, str):
        return False, "Input não pode ser vazio."
    stripped = text.strip()
    if len(stripped) == 0:
        return False, "Input não pode conter apenas espaços."
    if len(stripped) > 32_000:
        return False, "Input excede o limite de 32.000 caracteres."
    return True, ""


def validate_document(filepath: str) -> Tuple[bool, str]:
    """
    Valida um documento antes de processar.
    Verifica: existência, tipo e tamanho.
    Retorna (is_valid, error_message).
    """
    path = Path(filepath)

    if not path.exists():
        return False, f"Arquivo não encontrado: {filepath}"

    extension = path.suffix.lower()
    if extension not in SUPPORTED_DOCUMENT_TYPES:
        supported = ", ".join(SUPPORTED_DOCUMENT_TYPES)
        return False, f"Tipo de arquivo '{extension}' não suportado. Use: {supported}"

    size_bytes = path.stat().st_size
    max_bytes = MAX_DOCUMENT_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        return False, f"Arquivo muito grande ({size_bytes / 1024 / 1024:.1f} MB). Máximo: {MAX_DOCUMENT_SIZE_MB} MB"

    return True, ""
