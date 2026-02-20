from __future__ import annotations
import asyncio
import re
from bot.config import get_settings
from bot.db.connection import connect

# Regras: (padrão no título, marca esperada, modelo oficial)
REGRAS = [
    # Brother
    (r"j6955",          "Brother",  "MFC-J6955DW"),
    (r"l6902",          "Brother",  "MFC-L6902DW"),
    (r"l6702",          "Brother",  "MFC-L6702DW"),
    (r"l5912",          "Brother",  "MFC-L5912DW"),
    (r"l5212",          "Brother",  "HL-L5212DW"),
    (r"l6402",          "Brother",  "HL-L6402DW"),
    (r"l6202",          "Brother",  "HL-L6202DW"),
    (r"dcp.?l5652",     "Brother",  "DCP-L5652DN"),
    # Kyocera
    (r"na\s*4000",      "Kyocera",  "MA4000"),   # na4000 → MA4000
    (r"ma\s*4000",      "Kyocera",  "MA4000"),
    (r"pa\s*4000",      "Kyocera",  "PA4000"),
    (r"m6235",          "Kyocera",  "ECOSYS M6235"),
    (r"6235",           "Kyocera",  "ECOSYS M6235"),
    (r"taskalf",        "Kyocera",  "TASKalfa"),
    (r"taskalfa.?3551", "Kyocera",  "TASKalfa 3551ci"),
    (r"taskalfa.?3500", "Kyocera",  "TASKalfa 3500i"),
    # HP
    (r"hp\s*4303|4303\s*fdw", "HP", "HP Color LaserJet 4303fdw"),
    (r"hp\s*43[02]|432\s*fdn","HP", "Laser 432fdn"),
    (r"x585",           "HP",       "HP OfficeJet Color X585"),
    # OKI
    (r"4172",           "OKI",      "ES4172LP MFP"),
    (r"5112",           "OKI",      "ES5112 PN"),
    (r"5162",           "OKI",      "ES5162LP MFP"),
    # Ricoh
    (r"sp.?1130",       "Ricoh",    "SP 1130N"),
    (r"c352",           "Ricoh",    "SP C352DN"),
    # Xerox
    (r"3655",           "Xerox",    "WorkCentre 3655"),
    # Canon
    (r"g.?6010",        "Canon",    "G6010"),
    # Samsung
    (r"c.?4062",        "Samsung",  "SL-C4062FX"),
    (r"c.?4580",        "Samsung",  "ProXpress M4580FX"),
]


async def main() -> None:
    settings = get_settings()
    async with connect(settings.database_path) as conn:
        # Pega todos os itens para verificar correções (inclusive os que já têm modelo)
        cur = await conn.execute(
            "SELECT id, title, marca, modelo FROM items"
        )
        rows = await cur.fetchall()

    atualizados = 0
    async with connect(settings.database_path) as conn:
        for row in rows:
            item_id = row["id"]
            title = (row["title"] or "").lower()
            marca_atual = row["marca"] or ""
            modelo_atual = row["modelo"] or ""

            for padrao, marca_esperada, modelo_oficial in REGRAS:
                # Se a marca atual existir e for diferente da esperada, pula (evita conflitos óbvios)
                if marca_atual and marca_atual.lower() != marca_esperada.lower() and marca_atual.lower() != "none":
                    continue
                
                if re.search(padrao, title, re.IGNORECASE):
                    # Só atualiza se o modelo for diferente ou estiver vazio
                    if modelo_atual != modelo_oficial:
                        await conn.execute(
                            "UPDATE items SET marca = ?, modelo = ? WHERE id = ?",
                            (marca_esperada, modelo_oficial, item_id),
                        )
                        print(f"[{item_id}] {row['title']} → {marca_esperada} {modelo_oficial} (era: {modelo_atual})")
                        atualizados += 1
                    break

        await conn.commit()

    print(f"\nTotal atualizado/corrigido: {atualizados}")


if __name__ == "__main__":
    asyncio.run(main())
