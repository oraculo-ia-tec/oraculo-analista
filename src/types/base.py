# ============================================================
# src/types/base.py
# Tipos base compartilhados por toda a aplicação
# ============================================================
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class UserProfile:
    user_id: str
    name:    str  = ""
    email:   str  = ""
    plan:    str  = "free"
    profile_image_path: str = ""


@dataclass
class SessionState:
    session_id: str
    user:       UserProfile = field(default_factory=lambda: UserProfile(user_id="anon"))
    context:    str         = ""
