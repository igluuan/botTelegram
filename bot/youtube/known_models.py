from __future__ import annotations

import re

KNOWN_BRANDS: dict[str, list[str]] = {
    "Epson": [
        "AM-C5000", "AM-C4000", "WF-C5890", "WF-C5390", "WF-C5310",
        "L5190", "L3150", "L3110", "L6490", "L14150",
        "EcoTank L3250", "EcoTank L5590",
    ],
    "Brother": [
        "MFC-L6902DW", "MFC-L5912DW", "MFC-L6702DW", "MFC-J6955DW",
        "HL-L6402DW", "HL-L6202DW", "HL-L5212DW", "HL-L5912DW",
        "DCP-L5652DN",
        "L5212", "L5912",
    ],
    "Kyocera": [
        "TASKalfa 3551ci", "TASKalfa 3500i", "TASKalfa 4002i",
        "ECOSYS MA4000cix", "ECOSYS PA4000cx", "ECOSYS P3155dn",
        "ECOSYS M2040dn", "ECOSYS M2540dn",
        "MA4000", "PA4000",
        "taskalfa3500", "taskalfa3551",
    ],
    "HP": [
        "LaserJet Managed E42540", "LaserJet Managed E50145",
        "LaserJet Managed E60165", "LaserJet Managed E55040",
        "LaserJet Managed MFP E57540",
        "Laser 432fdn", "Laser 408dn",
        "LaserJet Pro M404dn", "LaserJet Pro MFP M428fdw",
    ],
    "Samsung": [
        "ProXpress M4070FR", "ProXpress SL-M4020ND", "ProXpress M4580FX",
        "SCX-5637", "ML-3710ND", "SL-C4062FX", "CLX-6260FR",
    ],
    "Ricoh": [
        "SP C352DN", "SP C360DNw", "IM C300F", "IM C400F",
        "MP 2555SP", "MP 3055SP",
    ],
    "Xerox": [
        "VersaLink C400", "VersaLink C405", "VersaLink B405",
        "WorkCentre 6515", "WorkCentre 7855",
    ],
    "OKI": [
        "ES4172LP MFP", "ES5162LP MFP", "ES5112 PN",
        "ES6405N", "MC780", "MPS5502MB", "C831N",
    ],
    "Canon": [
        "imageRUNNER 2625i", "imageRUNNER 2630i",
        "i-SENSYS MF745Cdw", "i-SENSYS MF643Cdw",
    ],
    "Lexmark": [
        "MS431dn", "MX431adn", "CS431dw", "CX431adw",
    ],
}

# Lookup invertido: token normalizado → marca e modelo oficial
_MODEL_TO_BRAND: dict[str, str] = {}
_MODEL_VARIANTS: dict[str, str] = {}


def _normalize_token(s: str) -> str:
    return re.sub(r"[\s\-]", "", s).lower()


for _brand, _models in KNOWN_BRANDS.items():
    for _model in _models:
        _key = _normalize_token(_model)
        _MODEL_TO_BRAND[_key] = _brand
        _MODEL_VARIANTS[_key] = _model
        for _part in re.split(r"[\s\-]", _model):
            _part_key = _part.lower()
            if len(_part_key) >= 3 and any(c.isdigit() for c in _part_key):
                if _part_key not in _MODEL_TO_BRAND:
                    _MODEL_TO_BRAND[_part_key] = _brand
                    _MODEL_VARIANTS[_part_key] = _model


def lookup_brand_from_text(text: str) -> tuple[str, str | None]:
    """Retorna (marca, modelo_oficial) a partir de um texto."""
    normalized = _normalize_token(text)

    # 1. Match por modelo conhecido
    # Ordenar por tamanho decrescente para evitar falso positivo (ex: L5212 dentro de HL-L5212DW)
    sorted_keys = sorted(_MODEL_TO_BRAND.keys(), key=len, reverse=True)
    for key in sorted_keys:
        if key in normalized:
            return _MODEL_TO_BRAND[key], _MODEL_VARIANTS.get(key)

    # 2. Fallback: match por nome da marca
    text_lower = text.lower()
    for brand in KNOWN_BRANDS:
        if brand.lower() in text_lower:
            return brand, None

    return "", None


def validate_model(model_candidate: str, brand: str) -> str | None:
    """Valida se o candidato é um modelo real. Retorna nome oficial ou None."""
    if not model_candidate or not brand:
        return None

    if len(model_candidate) < 3:
        return None

    key = _normalize_token(model_candidate)
    for m in KNOWN_BRANDS.get(brand, []):
        normalized_m = _normalize_token(m)
        if normalized_m == key:
            return m
        # Only allow substring match if candidate is long enough to be significant
        if len(key) >= 3 and key in normalized_m:
            return m

    blacklist = {
        "youtube", "video", "manual", "printer", "tutorial", "como",
        "reset", "trocar", "limpar", "gavetas", "cartucho", "toner",
        "bloquear", "configurar", "instalar", "atualizar", "resolver",
        "the", "and", "for", "how", "fix", "with", "from",
    }
    if model_candidate.lower() in blacklist:
        return None

    if not any(c.isdigit() for c in model_candidate):
        return None

    return model_candidate
