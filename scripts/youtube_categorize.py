from __future__ import annotations

import argparse
import csv
import json
import os
import time
from typing import Any

import anthropic
from dotenv import load_dotenv


load_dotenv()


def _get_api_key() -> str:
    value = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if not value:
        raise RuntimeError("ANTHROPIC_API_KEY não configurado")
    return value


def _load_categories(path: str) -> dict[str, list[str]]:
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    equipamentos = [str(x) for x in payload.get("equipamentos", []) if str(x).strip()]
    topicos = [str(x) for x in payload.get("topicos", []) if str(x).strip()]
    if not equipamentos or not topicos:
        raise RuntimeError("Categorias inválidas no arquivo informado")
    return {"equipamentos": equipamentos, "topicos": topicos}


def _system_prompt(categories: dict[str, list[str]]) -> str:
    return (
        "Categorize vídeos técnicos.\n"
        f"Equipamentos válidos: {categories['equipamentos']}\n"
        f"Tópicos válidos: {categories['topicos']}\n"
        "Retorne SOMENTE JSON:\n"
        '{"equipamento":"...","topico":"...","tags":["..."],"nivel":"Básico|Intermediário|Avançado"}'
    )


def _categorizar(
    client: anthropic.Anthropic, *, system_prompt: str, titulo: str, descricao: str
) -> dict[str, Any]:
    res = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=200,
        system=system_prompt,
        messages=[{"role": "user", "content": f"Título: {titulo}\nDescrição: {descricao}"}],
    )
    content = res.content[0].text if res.content else "{}"
    return json.loads(content)


def _normalize_result(result: dict[str, Any]) -> dict[str, Any]:
    equipamento = str(result.get("equipamento", "")).strip()
    topico = str(result.get("topico", "")).strip()
    nivel = str(result.get("nivel", "")).strip()
    tags_value = result.get("tags", [])
    if isinstance(tags_value, list):
        tags = ", ".join(str(t).strip() for t in tags_value if str(t).strip())
    else:
        tags = str(tags_value).strip()
    return {
        "equipamento": equipamento,
        "topico": topico,
        "tags": tags,
        "nivel": nivel,
    }


def categorize_csv(
    *,
    input_path: str,
    output_path: str,
    categories_path: str,
    sleep_seconds: float,
    limit: int | None,
    dry_run: bool,
) -> None:
    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        raise RuntimeError("CSV vazio")

    client = None
    system_prompt = ""
    if not dry_run:
        categories = _load_categories(categories_path)
        client = anthropic.Anthropic(api_key=_get_api_key())
        system_prompt = _system_prompt(categories)

    total = len(rows) if limit is None else min(limit, len(rows))
    for i, row in enumerate(rows[:total], start=1):
        if dry_run:
            row.setdefault("equipamento", "")
            row.setdefault("topico", "")
            row.setdefault("tags", "")
            row.setdefault("nivel", "")
        else:
            try:
                result = _categorizar(
                    client,
                    system_prompt=system_prompt,
                    titulo=row.get("titulo", ""),
                    descricao=row.get("descricao", ""),
                )
                row.update(_normalize_result(result))
            except Exception:
                row.update({"equipamento": "", "topico": "", "tags": "", "nivel": ""})
        print(f"[{i}/{total}] {row.get('titulo','')[:60]}")
        time.sleep(sleep_seconds)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", dest="input_path", default="videos.csv")
    parser.add_argument("--output", dest="output_path", default="videos_cat.csv")
    parser.add_argument("--categories", dest="categories_path", default="categorias.json")
    parser.add_argument("--sleep", dest="sleep_seconds", type=float, default=0.3)
    parser.add_argument("--limit", dest="limit", type=int)
    parser.add_argument("--dry-run", dest="dry_run", action="store_true")
    args = parser.parse_args()

    categorize_csv(
        input_path=args.input_path,
        output_path=args.output_path,
        categories_path=args.categories_path,
        sleep_seconds=args.sleep_seconds,
        limit=args.limit,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
