"""Notação numérica brasileira, sem alterar a precisão usada nos cálculos."""
import math
import re


def format_number(value: float, decimals: int = 1, grouping: bool = True) -> str:
    spec = f",.{decimals}f" if grouping else f".{decimals}f"
    return format(value, spec).translate(str.maketrans({",": ".", ".": ","}))


def parse_number(text: str, integer: bool = False) -> float | int:
    text = text.strip().replace("−", "-")
    if not re.fullmatch(r"[+-]?(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d+)?", text):
        raise ValueError("Use vírgula para os decimais, como 25,4. O ponto separa milhares, como 1.000,50.")
    value = float(text.replace(".", "").replace(",", "."))
    if not math.isfinite(value):
        raise ValueError("Informe um número finito.")
    if integer:
        if not value.is_integer():
            raise ValueError("Informe um número inteiro.")
        return int(value)
    return value
