# ============================================================
# src/permissions.py
# Sistema de permissões allow / ask / deny
# Baseado na arquitetura de permissões do Claude Code
# ============================================================
from .constants.settings import DEFAULT_PERMISSIONS


class PermissionError(Exception):
    """Levantada quando uma ação é negada pelo sistema de permissões."""


class Permissions:
    def __init__(self, overrides: dict | None = None):
        self._rules = {**DEFAULT_PERMISSIONS, **(overrides or {})}

    def check(self, action: str) -> bool:
        rule = self._rules.get(action, "ask")
        if rule == "allow":
            return True
        if rule == "deny":
            raise PermissionError(
                f"Ação '{action}' negada pelas permissões da sessão."
            )
        return False

    def set(self, action: str, rule: str) -> None:
        assert rule in ("allow", "ask", "deny"), f"Regra inválida: {rule}"
        self._rules[action] = rule

    def as_dict(self) -> dict:
        return dict(self._rules)
