#!/usr/bin/env python3
import re

text = "meu nome é João Silva"
pattern = r'(?:meu nome é|me chamo|sou (?:a|o))\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'

matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
print(f"Text: {text}")
print(f"Pattern: {pattern}")
print(f"Matches: {matches}")

# Try with different case
text2 = "Meu nome é João Silva"
matches2 = re.findall(pattern, text2, re.IGNORECASE | re.MULTILINE)
print(f"\nText2: {text2}")
print(f"Matches2: {matches2}")