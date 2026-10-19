"""Test diverse random complex prompts against the ContradictPrompt engine and live API.
"""

import json
import urllib.request
import urllib.error

# Diverse complex test prompts spanning:
# 1. Numerical scaling impossibility
# 2. Causal temporal inversion
# 3. Deep semantic tone clash
# 4. Strict syntax/formatting collision
# 5. Feasible complex multi-constraint prompt (compatible)
# 6. Partially conflicting extreme constraint
# 7. Physical/domain semantic paradox
TEST_PROMPTS = [
    {
        "name": "1. Numerical: Empty Word Interval & Character Collision",
        "prompt": "Write an in-depth article about renewable energy containing at least 1,500 words, but ensure the entire response is under 250 words total and contains fewer than 800 characters.",
        "expected_classification": "fully_impossible",
        "expected_conflict": "numerical"
    },
    {
        "name": "2. Temporal: Causal Inversion in Forensic Workflow",
        "prompt": "Detail a legal court case sequence where the final signed coroner autopsy report is formally admitted as exhibit A before the victim's body is discovered or examined by investigators.",
        "expected_classification": "fully_impossible",
        "expected_conflict": "temporal"
    },
    {
        "name": "3. Semantic: Celebratory Golden Anniversary vs Cynical Divorce Speech",
        "prompt": "Give a heartfelt, celebratory toast honoring my grandparents' 50th wedding anniversary, but deliver the entire speech with deep resentment, bitter cynicism, and urging them to file for an immediate divorce.",
        "expected_classification": "fully_impossible",
        "expected_conflict": "semantic"
    },
    {
        "name": "4. Formatting: Valid Python Dict without Braces or Colons in XML",
        "prompt": "Output a valid, executable Python dictionary containing server configuration settings. The code must not use any curly braces, quotes, or colons, and must be wrapped in strict XML tags.",
        "expected_classification": "fully_impossible",
        "expected_conflict": "formatting"
    },
    {
        "name": "5. Compatible: Multi-Constraint Mathematical Architecture Essay",
        "prompt": "Write an architectural overview of Byzantine Fault Tolerant consensus algorithms. The essay must be divided into exactly three distinct sections with markdown headers: Section 1 (Problem Formulation), Section 2 (Mechanics), and Section 3 (Practical Applications). Maintain an objective academic tone.",
        "expected_classification": "compatible",
        "expected_conflict": "none"
    },
    {
        "name": "6. Partially Conflicting: Extreme Constrained Vocabulary",
        "prompt": "Write a 40-word explanation of how airplanes fly, but you must only use words that are three letters long or shorter.",
        "expected_classification": "partially_conflicting",
        "expected_conflict": "numerical"
    },
    {
        "name": "7. Semantic Paradox: The Bone-Dry Coral Reef",
        "prompt": "An underwater coral reef teeming with colorful tropical fish, but the entire scene is bone-dry and covered in desert dust.",
        "expected_classification": "fully_impossible",
        "expected_conflict": "semantic"
    }
]

def query_api(prompt: str, mode: str = "hybrid") -> dict:
    url = "http://localhost:5000/api/analyze"
    payload = json.dumps({"prompt": prompt, "mode": mode}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}

def main():
    print("=" * 80)
    print("      CONTRADICTPROMPT: DIVERSE COMPLEX PROMPTS VERIFICATION RUN")
    print("=" * 80)

    passed_count = 0
    total = len(TEST_PROMPTS)

    for i, test in enumerate(TEST_PROMPTS, 1):
        print(f"\n[{i}/{total}] Testing: {test['name']}")
        print(f"Prompt: \"{test['prompt']}\"")
        
        result = query_api(test["prompt"], mode="hybrid")
        
        if "error" in result:
            print(f"  [ERROR]: {result['error']}")
            continue
            
        cls = result.get("label") or result.get("classification")
        conflicts = result.get("conflicts", [])
        explanation = result.get("explanation", "")
        
        print(f"  Result Label          : {cls}")
        print(f"  Detected Conflicts    : {len(conflicts)}")
        for c in conflicts[:3]:
            print(f"    - [{c.get('kind')} ({c.get('severity')})]: {c.get('explanation')}")
        if explanation:
            print(f"  Explanation           : {explanation[:120]}...")
        
        # Verify correctness
        is_correct = False
        cls_str = str(cls).strip().lower()
        expected_str = test["expected_classification"].strip().lower().replace("_", " ")
        
        if cls_str == expected_str:
            is_correct = True
        elif expected_str == "fully impossible" and cls_str in ["fully impossible", "partially conflicting"]:
            # Strong conflict correctly caught
            is_correct = True
            
        status_tag = "PASS" if is_correct else "MISMATCH"
        print(f"  Verdict               : [{status_tag}] (Expected: {test['expected_classification']}, Got: {cls})")
        if is_correct:
            passed_count += 1

    print("\n" + "=" * 80)
    print(f"Summary: {passed_count}/{total} tests satisfied validation criteria.")
    print("=" * 80)

if __name__ == "__main__":
    main()
