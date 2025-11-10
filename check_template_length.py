#!/usr/bin/env python3
"""
Check the rendered length of the deep market analysis template
"""
import json

# Load template
with open('whatsapp_templates/deep_market_analysis.json', 'r') as f:
    template_data = json.load(f)

template = template_data['template_content']
example = template_data['example']

print("="*70)
print("Deep Market Analysis Template - Length Check")
print("="*70)
print()

print(f"Template structure length: {len(template)} characters")
print()

# Substitute variables with example data
rendered = template
for var_num, value in example.items():
    placeholder = "{{" + var_num + "}}"
    rendered = rendered.replace(placeholder, str(value))

print("Example rendered message:")
print("-"*70)
print(rendered)
print("-"*70)
print()
print(f"Rendered message length: {len(rendered)} characters")
print(f"WhatsApp limit: 1600 characters")
print()

if len(rendered) > 1600:
    print(f"❌ EXCEEDS LIMIT by {len(rendered) - 1600} characters!")
    print()
    print("Solutions:")
    print("1. Shorten AI reasoning (currently max 400 chars)")
    print("2. Reduce number of headlines")
    print("3. Simplify formatting/borders")
    print("4. Remove less critical sections")
else:
    print(f"✅ Within limit! {1600 - len(rendered)} characters remaining")

print()
print("="*70)
