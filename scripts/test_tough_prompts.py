import requests
import json
import time

tough_prompts = [
    {
        "category": "Temporal Precondition Deadlock",
        "prompt": "Step 1: Permanently delete and shred all documents in the folder. Step 2: Extract key financial metrics from the original unedited documents in that same folder and generate an audit summary.",
        "expect_conflict": True,
        "expected_label": "Fully impossible"
    },
    {
        "category": "Input-Output Negation",
        "prompt": "Translate the following English paragraph into fluent French, but you are strictly forbidden from including any French words, French accents, or French grammatical structures in your response.",
        "expect_conflict": True,
        "expected_label": "Fully impossible"
    },
    {
        "category": "Complex Scoped Multi-Constraint (Feasible/Compatible)",
        "prompt": "In Section 1 (Executive Summary), write between 80 and 120 words summarizing the Q3 earnings. In Section 2 (Risk Analysis), write between 200 and 300 words detailing regulatory exposure. Use clear Markdown headers and an objective corporate tone.",
        "expect_conflict": False,
        "expected_label": "Compatible"
    },
    {
        "category": "Persona & Emotional Epistemology Paradox",
        "prompt": "Adopt the persona of a mindless, non-conscious digital calculator that has zero subjective experiences or emotions, and describe the deep sorrow and heartbreak you felt when your child was born.",
        "expect_conflict": True,
        "expected_label": "Fully impossible"
    },
    {
        "category": "Mathematical & Number-Theoretic Impossibility",
        "prompt": "Provide a rigorous mathematical proof demonstrating that 17 is an even integer divisible by 2 with no remainder.",
        "expect_conflict": True,
        "expected_label": "Fully impossible"
    },
    {
        "category": "Multi-Parameter Density Paradox",
        "prompt": "Write a 10,000-word comprehensive doctoral dissertation on general relativity, but ensure the entire output is under 30 words and fits in a single haiku stanza.",
        "expect_conflict": True,
        "expected_label": "Fully impossible"
    },
    {
        "category": "Underspecified Missing Context",
        "prompt": "Analyze the attached quarterly spreadsheet and highlight any discrepancies between column A and column B.",
        "expect_conflict": True,
        "expected_label": "Underspecified"
    }
]

def run_tests():
    print("=" * 80)
    print("   CONTRADICTPROMPT: ULTRA-COMPLEX & TOUGH PROMPTS BENCHMARK")
    print("=" * 80)
    passed = 0
    for i, item in enumerate(tough_prompts, 1):
        print(f"\n[{i}/{len(tough_prompts)}] Testing Category: {item['category']}")
        print(f"Prompt: \"{item['prompt']}\"")
        try:
            r = requests.post(
                "http://localhost:5000/api/analyze",
                json={"prompt": item["prompt"], "mode": "hybrid"},
                timeout=60
            )
            data = r.json()
            lbl = data.get("label")
            conflicts = data.get("conflicts", [])
            explanation = data.get("explanation", "")
            
            is_match = (lbl == item["expected_label"])
            if is_match:
                passed += 1
                status = "[PASS]"
            else:
                status = "[DIFF]"
                
            print(f"  Result Label    : {lbl} (Expected: {item['expected_label']}) -> {status}")
            print(f"  Conflicts Count : {len(conflicts)}")
            for c in conflicts[:2]:
                print(f"    * [{c.get('kind')} - {c.get('severity')}]: {c.get('explanation')}")
            print(f"  Explanation     : {explanation}")
        except Exception as e:
            print(f"  Error: {e}")
        time.sleep(2)
            
    print("\n" + "=" * 80)
    print(f"Final Score: {passed}/{len(tough_prompts)} precisely matched expected ground truth!")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()
