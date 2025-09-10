#!/usr/bin/env python3
"""
Teste de extração de informações para debug
"""

import re
import sys
sys.path.append('.')
from extract_client_info import ClientInfoExtractor

def test_single_extraction():
    extractor = ClientInfoExtractor()
    
    # Testar casos específicos
    test_cases = [
        "Francisco",
        "Bom dia, aguardando\nFrancisco",
        "Empresa Rio Conect",
        "da empresa Rocket Internet",
        "*SGPFLOW*",
        "meu nome é João Silva"
    ]
    
    for test_text in test_cases:
        print(f"\n--- Testando: '{test_text}' ---")
        result = extractor.analyze_with_patterns(test_text)
        print(f"Nome: {result['name']} (Confiança: {result['confidence_name']:.1%})")
        print(f"Empresa: {result['company']} (Confiança: {result['confidence_company']:.1%})")
        print(f"Razão: {result['reasoning']}")

if __name__ == "__main__":
    test_single_extraction()