"""
Tool de leitura e análise de planilhas Excel e CSV.
Substitui a lógica de planilhas dispersa em analista.py.
"""
from typing import Any, Dict

from src.tools.base import BaseTool, ToolRegistry


class ToolExcel(BaseTool):
    name = "tool_excel"
    description = (
        "Lê planilhas Excel (.xlsx, .xls) ou CSV e retorna um resumo estruturado "
        "com cabeçalhos, primeiras linhas, estatísticas e informações das colunas. "
        "Use para analisar dados financeiros, relatórios e tabelas."
    )
    plan_required = "free"

    @property
    def parameters_schema(self) -> Dict:
        return {
            "type": "object",
            "properties": {
                "filepath": {
                    "type": "string",
                    "description": "Caminho para o arquivo Excel ou CSV.",
                },
                "sheet_name": {
                    "type": "string",
                    "description": "Nome da aba a ler. Padrão: primeira aba.",
                    "default": "",
                },
                "preview_rows": {
                    "type": "integer",
                    "description": "Número de linhas de preview a retornar. Padrão: 10.",
                    "default": 10,
                },
            },
            "required": ["filepath"],
        }

    def validate(self, parameters: Dict[str, Any]) -> tuple[bool, str]:
        filepath = parameters.get("filepath", "")
        if not filepath:
            return False, "Parâmetro 'filepath' é obrigatório."
        ext = filepath.lower().split(".")[-1]
        if ext not in ["xlsx", "xls", "csv"]:
            return False, f"Formato não suportado: .{ext}. Use .xlsx, .xls ou .csv"
        return True, ""

    def _execute(self, parameters: Dict[str, Any]) -> Any:
        import pandas as pd
        from pathlib import Path

        filepath = parameters["filepath"]
        sheet_name = parameters.get("sheet_name", 0) or 0
        preview_rows = parameters.get("preview_rows", 10)

        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {filepath}")

        # Leitura adaptada ao tipo de arquivo
        ext = path.suffix.lower()
        if ext == ".csv":
            df = pd.read_csv(filepath, encoding="utf-8", sep=None, engine="python")
        else:
            df = pd.read_excel(filepath, sheet_name=sheet_name)

        # Monta resumo estruturado
        preview = df.head(preview_rows).to_dict(orient="records")

        # Estatísticas das colunas numéricas
        numeric_cols = df.select_dtypes(include="number").columns.tolist()
        stats = {}
        for col in numeric_cols:
            stats[col] = {
                "min": float(df[col].min()),
                "max": float(df[col].max()),
                "mean": round(float(df[col].mean()), 2),
                "sum": float(df[col].sum()),
                "null_count": int(df[col].isnull().sum()),
            }

        return {
            "filename": path.name,
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "columns": df.columns.tolist(),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "preview": preview,
            "numeric_stats": stats,
            "null_counts": df.isnull().sum().to_dict(),
        }


ToolRegistry.register(ToolExcel())
