SUBCATEGORIAS: dict[str, list[str]] = {
    "Rede":        ["rede", "wi-fi", "wifi", "ip", "cabo", "driver", "instalação", "porta"],
    "Toner":       ["toner", "cartucho", "suprimento", "trocar", "destravar", "reset cartucho"],
    "Manutenção":  ["manutenção", "lubrificação", "fusão", "barulho", "erro", "falha", "gaveta"],
    "Firmware":    ["firmware", "atualização", "fw", "update"],
    "Scanner":     ["scanner", "digitalizar", "scan", "adf"],
    "Configuração":["configuração", "configurar", "painel", "idioma", "linguagem", "cota", "usuário"],
    "Contador":    ["contador", "uso", "relatório", "consumo"],
    "Outros":      [],  # fallback
}

def detectar_subcategoria(titulo: str, tags: str = "") -> str:
    texto = f"{titulo} {tags}".lower()
    for subcategoria, palavras in SUBCATEGORIAS.items():
        if subcategoria == "Outros":
            continue
        if any(p in texto for p in palavras):
            return subcategoria
    return "Outros"
