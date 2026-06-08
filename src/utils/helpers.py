"""
Funções utilitárias reutilizáveis em todo o sistema.
"""
import uuid
import re
import os
from pathlib import Path


def generate_id(prefix: str = "") -> str:
    """
    Gera um ID único com prefixo opcional.
    Exemplo: generate_id("session") → "session_a3f9b2c1"
    """
    short_id = str(uuid.uuid4()).replace("-", "")[:12]
    return f"{prefix}_{short_id}" if prefix else short_id


def format_file_size(size_bytes: int) -> str:
    """
    Formata tamanho em bytes para string legível.
    Exemplo: format_file_size(1_048_576) → "1.0 MB"
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def truncate_text(text: str, max_chars: int = 500, suffix: str = "...") -> str:
    """
    Trunca texto para um número máximo de caracteres.
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars - len(suffix)] + suffix


def sanitize_filename(filename: str) -> str:
    """
    Remove caracteres inválidos de um nome de arquivo.
    Exemplo: sanitize_filename("meu arquivo (1).pdf") → "meu_arquivo_1.pdf"
    """
    # Remove caracteres especiais exceto ponto, hífen e underscore
    clean = re.sub(r"[^\w\s.-]", "", filename)
    # Substitui espaços por underscore
    clean = re.sub(r"\s+", "_", clean)
    return clean.strip("._")


def estimate_tokens(text: str) -> int:
    """
    Estimativa simples de tokens: ~4 caracteres por token.
    Usada para controle de custo antes de chamar a API.
    """
    return max(1, len(text) // 4)


def get_file_extension(filepath: str) -> str:
    """
    Retorna a extensão do arquivo em minúsculas.
    Exemplo: get_file_extension("relatorio.PDF") → ".pdf"
    """
    return Path(filepath).suffix.lower()


def safe_read_file(filepath: str, encoding: str = "utf-8") -> str:
    """
    Lê um arquivo de texto com tratamento de erro.
    Retorna string vazia se o arquivo não existir.
    """
    try:
        with open(filepath, "r", encoding=encoding) as f:
            return f.read()
    except (FileNotFoundError, PermissionError, UnicodeDecodeError):
        return ""


def safe_write_file(filepath: str, content: str, encoding: str = "utf-8") -> bool:
    """
    Escreve conteúdo em um arquivo, criando diretórios se necessário.
    Retorna True se bem-sucedido.
    """
    try:
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding=encoding) as f:
            f.write(content)
        return True
    except (PermissionError, OSError):
        return False
