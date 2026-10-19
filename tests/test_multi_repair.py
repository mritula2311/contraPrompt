import sys, os
sys.path.insert(0, os.path.abspath('.'))
import requests
from tests.test_cybersecurity_regression import CYBERSECURITY_FAILING_PROMPT

r = requests.post('http://127.0.0.1:5000/api/analyze', json={'prompt': CYBERSECURITY_FAILING_PROMPT, 'mode': 'rules'})
asm = r.json()
print("Initial label:", asm.get("label"))
print("Initial conflicts:", len(asm.get("conflicts", [])))

r_grp = requests.post('http://127.0.0.1:5000/api/repair/groups', json={'analysis': asm})
groups = r_grp.json()
print(f"Repair groups generated: {len(groups)}")
selected = []
for g in groups:
    cid = g["conflict_id"]
    ctype = g["conflict_type"]
    opts = g["options"]
    print(f"  [{cid}] {ctype} ({len(opts)} options): {g['explanation'][:60]}...")
    if opts:
        first_opt = opts[0]
        selected.append({"conflict_id": cid, "repair_id": first_opt["repair_id"]})
        print(f"       -> Selecting option: {first_opt['repair_id']}: {first_opt['description'][:60]}...")

print(f"\nTotal selected repairs for batch: {len(selected)}")
r_prev = requests.post('http://127.0.0.1:5000/api/repair/batch-preview', json={'analysis': asm, 'selected_repairs': selected})
prev = r_prev.json()
print("Preview compatibility:", prev.get("is_compatible"))
print("Compatibility issues:", prev.get("compatibility_issues"))
print("Predicted resolved conflicts:", prev.get("predicted_resolved_conflicts"))

r_apply = requests.post('http://127.0.0.1:5000/api/repair/batch-apply', json={
    'analysis': asm,
    'selected_repairs': selected,
    'approved': True,
    'mode': 'rules'
})
res = r_apply.json()
print("\nBatch Apply Result:")
print("  Success:", res.get("success"))
print("  Previous Label:", res.get("previous_label"))
print("  Revalidated Label:", res.get("revalidated_label"))
print("  Resolved Conflicts:", res.get("resolved_conflicts"))
print("  Remaining Conflicts:", res.get("remaining_conflicts"))
print("  Preserved Instructions:", res.get("preserved_instructions_count"))
