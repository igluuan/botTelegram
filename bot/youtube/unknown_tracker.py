from __future__ import annotations
import pathlib

_UNKNOWN_LOG = pathlib.Path("unknown_models.log")

def registrar(marca: str, candidato: str, titulo: str = "") -> None:
    try:
        with _UNKNOWN_LOG.open("a", encoding="utf-8") as f:
            f.write(f"{marca}\t{candidato}\t{titulo}\n")
    except Exception:
        pass