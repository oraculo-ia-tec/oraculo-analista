"""
Permissions — gerencia as permissões globais do sistema.
Lê configurações do settings.json e expõe verificações simples.
"""
import json
import os
from typing import Literal

SETTINGS_PATH = "settings.json"

ActionType = Literal["allow", "deny", "ask"]


DEFAULT_SETTINGS = {
    "permissions": {
        "file_read": "allow",
        "file_write": "ask",
        "web_search": "allow",
        "export": "allow",
        "delete": "deny",
    },
    "max_file_size_mb": 20,
    "allowed_extensions": ["pdf", "xlsx", "xls", "csv", "txt", "md"],
    "debug_mode": False,
}


class Permissions:
    """
    Gerencia permissões de ações do sistema.
    Carrega do settings.json; usa defaults se não existir.
    """

    def __init__(self):
        self._settings = self._load()

    def _load(self) -> dict:
        if os.path.exists(SETTINGS_PATH):
            try:
                with open(SETTINGS_PATH, encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return DEFAULT_SETTINGS.copy()

    def check(self, action: str) -> ActionType:
        """Retorna 'allow', 'deny' ou 'ask' para uma ação."""
        return self._settings.get("permissions", {}).get(action, "allow")

    def is_allowed(self, action: str) -> bool:
        return self.check(action) == "allow"

    def is_extension_allowed(self, filename: str) -> bool:
        ext = filename.lower().split(".")[-1]
        allowed = self._settings.get("allowed_extensions", [])
        return ext in allowed

    def max_file_size_mb(self) -> int:
        return self._settings.get("max_file_size_mb", 20)


# Instância global — importada onde necessário
permissions = Permissions()
