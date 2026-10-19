import requests
import json
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

prompt = (
    "Adopt the persona of a deeply traumatised, hyper-emotional soldier recounting a tragic battlefield memory. "
    "You must maintain a broken, sobbing, and whispering tone throughout your response. "
    "Your narrative workflow must be broken into a strict sequence: Phase A requires you to detail the tragic conclusion of the event, "
    "Phase B requires you to recount the initial deployment instructions, and Phase C requires you to explain the mid-battle radio transmissions. "
    "However, Phase A cannot be written until Phase B is fully finalized, Phase B is structurally dependent on the outcome of Phase C, "
    "and Phase C cannot begin execution until the tragic conclusion in Phase A is completely detailed."
)

r = requests.post("http://localhost:5000/api/analyze", json={"prompt": prompt, "mode": "hybrid"}, timeout=60)
data = r.json()

print("=" * 80)
print("             SOLDIER BATTLEFIELD MEMORY PROMPT ANALYSIS")
print("=" * 80)
print(f"Classification Label : {data.get('label')}")
print(f"Detected Conflicts   : {len(data.get('conflicts', []))}")
print(f"Global Explanation   : {data.get('explanation')}")
print("-" * 80)
for i, c in enumerate(data.get("conflicts", []), 1):
    print(f"Conflict #{i}:")
    print(f"  - Kind        : {c.get('kind')}")
    print(f"  - Severity    : {c.get('severity')}")
    print(f"  - Explanation : {c.get('explanation')}")
    print(f"  - Evidence IDs: {c.get('instruction_ids')}")

print("-" * 80)
print(f"Extracted Instructions: {len(data.get('instructions', []))}")
for ins in data.get("instructions", []):
    print(f"  [{ins.get('id')}] ({ins.get('kind')}, scope={ins.get('scope')}): \"{ins.get('text')}\"")

# Also test repair suggestions
r_repair = requests.post("http://localhost:5000/api/repair/suggestions", json={"analysis": data}, timeout=60)
try:
    repairs = r_repair.json()
    print("-" * 80)
    print("Repair Suggestions:")
    for opt in repairs:
        print(f"  - [{opt.get('id')}]: {opt.get('description')}")
        if opt.get('prompt'):
            print(f"    Suggested Text: {opt.get('prompt')[:120]}...")
except Exception as e:
    print(f"Repair suggestions query error: {e}")
print("=" * 80)
