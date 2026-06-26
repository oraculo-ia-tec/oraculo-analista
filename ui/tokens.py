"""
ORÁCULO ANALISTA — Design Tokens (Python)
Fonte única de verdade para cores, espaçamento, raios, sombras.
Use sempre estas variáveis nos componentes — nunca hardcode hex.
"""

# ── Paleta semântica ────────────────────────────────────────
COLOR = {
    # Superfícies (escala de profundidade)
    "bg":              "#0D0D0F",
    "surface":         "#141417",
    "surface_2":       "#1A1A1F",
    "surface_3":       "#1F1F26",
    "border":          "#2A2A35",
    "border_subtle":   "#1E1E28",

    # Texto
    "text":            "#E8E6E1",
    "text_muted":      "#9896A0",
    "text_faint":      "#55545C",

    # Acento dourado (identidade Oráculo)
    "gold":            "#C9A84C",
    "gold_hover":      "#DFC06A",
    "gold_dim":        "#3A2F10",
    "gold_glow":       "rgba(201, 168, 76, 0.18)",

    # Acento violeta (herança visual — uso restrito)
    "violet":          "#7C3AED",
    "violet_dim":      "#2D1A5A",

    # Semânticos
    "success":         "#3EAF7C",
    "success_dim":     "#0F3020",
    "warning":         "#E09A3A",
    "warning_dim":     "#3A2610",
    "error":           "#E05252",
    "error_dim":       "#3A1010",
    "info":            "#3A9BE0",
    "info_dim":        "#0F2340",
}

# ── Espaçamentos ────────────────────────────────────────────
SPACE = {
    1:  "4px",
    2:  "8px",
    3:  "12px",
    4:  "16px",
    6:  "24px",
    8:  "32px",
    10: "40px",
    12: "48px",
    16: "64px",
}

# ── Raios de borda ──────────────────────────────────────────
RADIUS = {
    "sm":   "4px",
    "md":   "8px",
    "lg":   "12px",
    "xl":   "16px",
    "full": "9999px",
}

# ── Transições ─────────────────────────────────────────────
TRANSITION = "180ms cubic-bezier(0.16, 1, 0.3, 1)"
