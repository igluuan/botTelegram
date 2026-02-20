from __future__ import annotations

import pytest
from bot.youtube.known_models import lookup_brand_from_text, validate_model, _normalize_token

def test_normalize_token():
    assert _normalize_token("HL-L5212DW") == "hll5212dw"
    assert _normalize_token("Epson L3250") == "epsonl3250"

def test_lookup_brand_simple():
    brand, model = lookup_brand_from_text("Review Epson L3250")
    assert brand == "Epson"
    assert model == "EcoTank L3250" or model == "L3250" # Depends on what is in known_models, checking known_models.py content L3250 is there, EcoTank L3250 is also there.
    # In known_models.py: "L3250", "EcoTank L3250".
    # If I search "L3250", it should match "L3250".
    
    brand, model = lookup_brand_from_text("Impressora Brother HL-L6402DW")
    assert brand == "Brother"
    assert model == "HL-L6402DW"

def test_lookup_brand_longest_match():
    # This is the critical test for the fix
    # "HL-L5212DW" contains "L5212"
    # L5212 é usado como alias da Brother, HL-L5212DW é o modelo completo
    
    # Case 1: Text contains the full Brother model
    brand, model = lookup_brand_from_text("Manutenção Brother HL-L5212DW")
    assert brand == "Brother"
    assert model == "HL-L5212DW"
    
    # Case 2: Text contains only the short alias
    brand, model = lookup_brand_from_text("Reset Epson L5212")
    assert brand == "Brother"
    assert model == "L5212"

def test_lookup_fallback_brand_name():
    brand, model = lookup_brand_from_text("Uma impressora Kyocera genérica")
    assert brand == "Kyocera"
    assert model is None

def test_validate_model_valid():
    # If the input is "L3250", it should find "EcoTank L3250" because it contains "L3250"
    # and L3250 is not explicitly in the list as a separate item, but EcoTank L3250 is.
    # The validate_model logic returns the first match in the list that contains the candidate.
    assert validate_model("L3250", "Epson") == "EcoTank L3250"
    # Case insensitive
    assert validate_model("l3250", "Epson") == "EcoTank L3250"
    
def test_validate_model_invalid():
    assert validate_model("youtube", "Epson") is None
    assert validate_model("video", "Brother") is None
    assert validate_model("12", "Epson") is None # Too short (<3)
    # validate_model logic:
    # 1. Check if in known models for that brand.
    # 2. Blacklist check.
    # 3. Digit check.
    
    # "video" is in blacklist
    assert validate_model("video", "Epson") is None
    
    # "print" (not in blacklist but no digits? wait, blacklist has 'printer')
    assert validate_model("printer", "Epson") is None

def test_validate_model_known_but_messy_input():
    # If input is "hll5212dw" (normalized) it should return official "HL-L5212DW"
    assert validate_model("hll5212dw", "Brother") == "HL-L5212DW"
