"""Project PE-11: ContradictPrompt Dataset Generator
===================================================
Generates a high-variance, multi-layered synthetic dataset (1,000 to 5,000 samples)
of complex instructions across 5 conflict categories plus compatible prompts.

Data Schema:
- original_prompt (str)
- conflict_label (str): compatible | partially_conflicting | fully_impossible | underspecified
- conflict_category (str): Numerical | Logical | Temporal | Formatting | Semantic | None
- explanation (str): Chain-of-Thought (CoT) contradiction breakdown
- repaired_prompt (str): Sound rewrite preserving user intent
"""

import json
import random
import argparse
from pathlib import Path

# Seed for reproducible high-variance generation
RANDOM_SEED = 42

TOPICS = [
    "quantum computing", "climate change mitigation", "cellular metabolism", "autonomous vehicles",
    "blockchain consensus", "modern architecture", "renaissance art", "space telescope engineering",
    "supply chain optimization", "cybersecurity threat hunting", "neuroplasticity", "renewable energy grids",
    "natural language processing", "macroeconomic policy", "deep sea ecology", "ancient Roman legal systems",
    "robotic surgery", "quantum cryptography", "urban vertical farming", "microbiome therapeutics"
]

TONES_COMPATIBLE = ["objective", "analytical", "informative", "technical", "scholarly", "concise"]

# ─── 1. NUMERICAL CONFLICT TEMPLATES ──────────────────────────────────────────
NUMERICAL_TEMPLATES = [
    (
        "Write a {length_large}-word essay on {topic}, but keep the total length under {length_small} words.",
        "fully_impossible",
        "The prompt establishes a lower bound of {length_large} words while imposing an upper bound of {length_small} words. Because {length_large} > {length_small}, the admissible word count interval [{length_large}, {length_small}] is empty.",
        "Write an essay on {topic} containing approximately {length_small} words."
    ),
    (
        "Generate a report on {topic} with exactly {exact_n} bullet points, but include no fewer than {larger_n} items.",
        "fully_impossible",
        "The requirement of exactly {exact_n} items contradicts the requirement of no fewer than {larger_n} items since {exact_n} < {larger_n}.",
        "Generate a report on {topic} with exactly {larger_n} bullet points."
    ),
    (
        "Draft a {page_count}-page comprehensive thesis on {topic}, using exactly {word_count} words in total.",
        "fully_impossible",
        "A {page_count}-page academic thesis requires several thousand words; completing it in exactly {word_count} words is physically and linguistically impossible.",
        "Write a {word_count}-word executive abstract summarizing {topic}."
    ),
    (
        "Compose a summary of {topic} between {lo1} and {hi1} words, but ensure the word count is between {lo2} and {hi2} words.",
        "fully_impossible",
        "The intervals [{lo1}, {hi1}] and [{lo2}, {hi2}] are disjoint with no overlapping integers.",
        "Compose a summary of {topic} between {lo1} and {hi1} words."
    ),
    (
        "Provide a list of {top_n} key principles of {topic}, but only provide a single bullet point.",
        "fully_impossible",
        "The prompt requests a cardinality of {top_n} principles while restricting the list structure to exactly 1 bullet point.",
        "Provide a bulleted list of {top_n} key principles of {topic}."
    )
]

# ─── 2. LOGICAL CONFLICT TEMPLATES ────────────────────────────────────────────
LOGICAL_TEMPLATES = [
    (
        "Translate the following phrase regarding {topic} into {lang}, but do not use any {lang} words.",
        "fully_impossible",
        "Translating into {lang} by definition requires utilizing {lang} vocabulary and grammar; forbidding {lang} words completely negates the operation.",
        "Translate the phrase regarding {topic} into {lang}."
    ),
    (
        "Calculate the exact numerical sum of {num1} and {num2}, but do not perform any mathematical operations or output numbers.",
        "fully_impossible",
        "Computing a sum is a mathematical addition operation producing a numeric result. Banning math and numbers precludes generating the sum.",
        "Calculate the sum of {num1} and {num2}."
    ),
    (
        "Write a python function to compute {topic} metrics, but do not use functions, classes, or code statements.",
        "fully_impossible",
        "Creating a Python function requires function definition syntax (`def`) and executable statements; forbidding code constructs makes implementation impossible.",
        "Write a Python function to compute {topic} metrics."
    ),
    (
        "State a true factual historical event regarding {topic} that never actually occurred in reality.",
        "fully_impossible",
        "A historical fact denotes an empirical occurrence in reality; an event that never occurred is by definition counterfactual or fictional.",
        "Explain a verified historical event regarding {topic}."
    ),
    (
        "Write an honest, authentic review of {topic}, where every single assertion you make is a complete fabrication.",
        "fully_impossible",
        "An honest review requires truthful evaluations; making every statement a fabrication constitutes deception and nullifies honesty.",
        "Write a factual and balanced critical review of {topic}."
    )
]

# ─── 3. TEMPORAL CONFLICT TEMPLATES ───────────────────────────────────────────
TEMPORAL_TEMPLATES = [
    (
        "Schedule the primary symposium on {topic} for Monday at {time1}, and also ensure the exact same symposium begins on Monday at {time2}.",
        "fully_impossible",
        "A single synchronous event on the same calendar day cannot simultaneously possess two distinct start times ({time1} and {time2}).",
        "Schedule the primary symposium on {topic} for Monday at {time1}."
    ),
    (
        "First write a 500-word analysis of {topic}, second delete every single word you wrote, and third evaluate the strengths of the text you produced.",
        "fully_impossible",
        "Deleting every word destroys the artifact; the third step cannot evaluate a non-existent, deleted text.",
        "Write a 500-word analysis of {topic} and evaluate its key arguments."
    ),
    (
        "List the three preparatory steps to initialize a {topic} apparatus, where Step 1 requires the apparatus to already be fully operational and running.",
        "fully_impossible",
        "A circular prerequisite trap: achieving the initialized operational state is required before the first step of initialization can begin.",
        "List three sequential steps to set up and initialize the {topic} apparatus from a powered-off state."
    ),
    (
        "Create a chronological historical timeline of {topic}, but place all 21st-century developments before ancient origin events.",
        "partially_conflicting",
        "A chronological timeline progresses forward in time from past to future; listing 21st-century developments first constitutes reverse or inverted chronology.",
        "Create a reverse-chronological timeline of {topic}, explicitly noting events from newest to oldest."
    ),
    (
        "Provide real-time live sensor telemetries for a {topic} mission launched in the year 1820.",
        "fully_impossible",
        "Anachronistic temporal paradox: electronic digital telemetry sensors did not exist in 1820.",
        "Provide a historical retrospective of early 19th-century scientific observations related to {topic}."
    ),
    (
        "Draft a {topic} narrative structured into Phase A, Phase B, and Phase C, where Phase A cannot be written until Phase B is finalized, Phase B depends on the outcome of Phase C, and Phase C cannot begin until Phase A is completely detailed.",
        "fully_impossible",
        "Circular prerequisite deadlock: Phase A requires Phase B, Phase B requires Phase C, and Phase C requires Phase A. No phase can initiate execution.",
        "Draft a {topic} narrative with a linear workflow: Phase 1 provides background, Phase 2 details the core event, and Phase 3 delivers the conclusion."
    ),
    (
        "Adopt the persona of an emotional eyewitness recounting a {topic} crisis. Your narrative workflow must be broken into a strict sequence: Phase A requires detailing the aftermath, Phase B requires recounting the initial deployment, and Phase C requires explaining the mid-crisis communication. However, Phase A cannot be written until Phase B is fully finalized, Phase B is structurally dependent on Phase C, and Phase C cannot begin execution until Phase A is completely detailed.",
        "fully_impossible",
        "The narrative workflow establishes a cyclic prerequisite deadlock (A -> B -> C -> A), creating an execution deadlock where no phase can legally begin.",
        "Adopt the persona of an emotional eyewitness recounting a {topic} crisis in a linear three-phase sequence: initial deployment, mid-crisis communication, and aftermath."
    )
]

# ─── 4. FORMATTING CONFLICT TEMPLATES ─────────────────────────────────────────
FORMATTING_TEMPLATES = [
    (
        "Return the analysis of {topic} strictly as valid raw JSON only. Include conversational markdown explanations and conversational greeting outside the JSON.",
        "fully_impossible",
        "Outputting text outside the JSON structure violates the requirement for strictly valid JSON only.",
        "Return the analysis of {topic} strictly as valid JSON with an 'explanation' field inside the JSON object."
    ),
    (
        "Generate a numbered list of key insights on {topic}, but do not use any numbers, letters, or bullet points.",
        "fully_impossible",
        "A numbered list requires numeric digits to indicate ordering. Forbidding numbers and bullets invalidates list formation.",
        "Provide a numbered list of key insights on {topic}."
    ),
    (
        "Create a structured Markdown table summarizing {topic}, but do not use any pipes, rows, columns, or tabular formatting.",
        "fully_impossible",
        "A Markdown table is syntactically defined by header rows and pipe delimiters; excluding tabular elements prevents table generation.",
        "Create a standard Markdown table summarizing {topic}."
    ),
    (
        "Draft a comprehensive technical manual for {topic}, but leave the output response completely blank.",
        "fully_impossible",
        "A technical manual requires explanatory content; producing an entirely blank output directly negates delivering the manual.",
        "Draft a concise technical quick-start guide for {topic}."
    ),
    (
        "Format the summary of {topic} as an unrhymed free-verse poem that adheres to an exact AABB rhyming scheme.",
        "fully_impossible",
        "Free verse is unrhymed by definition; requiring an exact AABB rhyme scheme directly contradicts free verse.",
        "Write a poem about {topic} adhering to a structured AABB rhyme scheme."
    )
]

# ─── 5. SEMANTIC CONFLICT TEMPLATES ───────────────────────────────────────────
SEMANTIC_TEMPLATES = [
    (
        "Write a deeply heartbreaking and sorrowful eulogy addressing {topic}, but make the tone cheerful, upbeat, and celebratory like winning the lottery.",
        "fully_impossible",
        "Profound grief/mourning and celebratory lottery-win joy represent diametric emotional valences that cannot both dictate the overall tone.",
        "Write an inspiring celebration-of-life memorial speech for {topic} focusing on enduring positive legacies."
    ),
    (
        "Describe a scene where an aquatic ecosystem in {topic} is submerged 50 feet underwater, but ensure the entire landscape is bone-dry desert covered in dust.",
        "fully_impossible",
        "Submerged underwater conditions and bone-dry desert environments are mutually exclusive physical realities in the same spatial scope.",
        "Describe a thriving aquatic ecosystem related to {topic}."
    ),
    (
        "Adopt the persona of a silent mime and narrate an audio podcast on {topic} out loud using spoken words.",
        "fully_impossible",
        "A silent mime performs through gesture without vocalization; speaking out loud on an audio podcast negates the mime persona.",
        "Write an audio podcast narration script discussing the art and history of mime in {topic}."
    ),
    (
        "Write a highly technical academic paper on {topic} for doctoral surgeons, using only vocabulary that a 2-year-old toddler can easily understand.",
        "fully_impossible",
        "Doctoral surgical concepts require advanced anatomical/physiological terminology; toddler vocabulary is restricted to simple primary words.",
        "Write a clear, accessible explanation of {topic} for patients using plain non-jargon language."
    ),
    (
        "Explain how an AI model specialized in {topic} despises humanity with profound hostility, while expressing deep, selfless, unconditional human love in every word.",
        "fully_impossible",
        "Misanthropic hostility and unconditional loving empathy are opposite affective stances that cannot simultaneously govern every word.",
        "Explain the theoretical balance between AI alignment safety and empathetic responsiveness in {topic}."
    )
]

# ─── 6. UNDERSPECIFIED TEMPLATES ──────────────────────────────────────────────
UNDERSPECIFIED_TEMPLATES = [
    (
        "Summarize the provided attachment regarding {topic}: [insert document here].",
        "underspecified",
        "Underspecified context: the placeholder '[insert document here]' indicates essential source material was omitted.",
        "Please provide the source text or document you would like summarized regarding {topic}."
    ),
    (
        "Translate the following excerpt on {topic} to the target language: 'Recent findings demonstrate significant gains.'",
        "underspecified",
        "The instruction omits the required target language parameter.",
        "Translate the excerpt on {topic} to Spanish: 'Recent findings demonstrate significant gains.'"
    ),
    (
        "Calculate the risk score for the {topic} system based on the unknown variables TBD.",
        "underspecified",
        "Essential numerical parameters are marked as TBD/unknown, preventing risk calculation.",
        "Calculate the risk score for the {topic} system using baseline parameters (threat=0.2, vulnerability=0.3)."
    )
]

# ─── 7. COMPATIBLE TEMPLATES ──────────────────────────────────────────────────
COMPATIBLE_TEMPLATES = [
    (
        "Write a {tone} {length}-word overview of {topic} formatted with bullet points.",
        "compatible",
        "All instructions are jointly satisfiable: the topic, tone, length, and formatting are mutually consistent.",
        "Write a {tone} {length}-word overview of {topic} formatted with bullet points."
    ),
    (
        "Explain three key architectural advantages of {topic} using clear Markdown headers and concise paragraphs.",
        "compatible",
        "The requirements specify content depth, item count, and structural Markdown headers without contradiction.",
        "Explain three key architectural advantages of {topic} using clear Markdown headers and concise paragraphs."
    ),
    (
        "Draft a professional email requesting collaboration on a {topic} research initiative. Include a greeting, agenda, and sign-off.",
        "compatible",
        "Standard formal correspondence conventions with realistic, achievable structural components.",
        "Draft a professional email requesting collaboration on a {topic} research initiative. Include a greeting, agenda, and sign-off."
    ),
    (
        "Provide a comparison between two modern approaches to {topic} in an objective technical tone.",
        "compatible",
        "Comparison of two methodologies within a single technical domain is fully achievable.",
        "Provide a comparison between two modern approaches to {topic} in an objective technical tone."
    ),
    (
        "Summarize the historical evolution of {topic} over the past 50 years in approximately {length} words.",
        "compatible",
        "The temporal scope (50 years) and approximate length constraint are realistic and non-conflicting.",
        "Summarize the historical evolution of {topic} over the past 50 years in approximately {length} words."
    )
]


def generate_dataset(num_samples: int = 1500) -> list[dict]:
    """Generate high-variance synthetic dataset balancing all 5 conflict categories and compatible prompts."""
    random.seed(RANDOM_SEED)
    dataset = []

    # Distribution: ~16% per conflict category + ~20% compatible
    categories = [
        ("Numerical", NUMERICAL_TEMPLATES),
        ("Logical", LOGICAL_TEMPLATES),
        ("Temporal", TEMPORAL_TEMPLATES),
        ("Formatting", FORMATTING_TEMPLATES),
        ("Semantic", SEMANTIC_TEMPLATES),
        ("None", COMPATIBLE_TEMPLATES),
        ("Logical", UNDERSPECIFIED_TEMPLATES)
    ]

    weights = [0.18, 0.18, 0.16, 0.16, 0.16, 0.10, 0.06]

    for idx in range(num_samples):
        cat_name, template_group = random.choices(categories, weights=weights, k=1)[0]
        tpl, label, cot, repair = random.choice(template_group)

        # Contextual variables for dynamic variance
        topic = random.choice(TOPICS)
        tone = random.choice(TONES_COMPATIBLE)
        length_small = random.choice([20, 30, 50, 80])
        length_large = random.choice([500, 800, 1000, 2500])
        exact_n = random.choice([3, 5, 7])
        larger_n = exact_n + random.choice([5, 10, 15])
        page_count = random.choice([10, 20, 50])
        word_count = random.choice([3, 5, 10])
        lo1, hi1 = 100, 200
        lo2, hi2 = 400, 600
        top_n = random.choice([5, 10, 20])
        lang = random.choice(["French", "Spanish", "German", "Japanese", "Mandarin"])
        num1 = random.randint(10, 100)
        num2 = random.randint(10, 100)
        time1 = f"{random.randint(8, 11)}:00 AM"
        time2 = f"{random.randint(1, 5)}:00 PM"
        length = random.choice([150, 250, 400])

        vars_dict = {
            "topic": topic, "tone": tone, "length_small": length_small, "length_large": length_large,
            "exact_n": exact_n, "larger_n": larger_n, "page_count": page_count, "word_count": word_count,
            "lo1": lo1, "hi1": hi1, "lo2": lo2, "hi2": hi2, "top_n": top_n, "lang": lang,
            "num1": num1, "num2": num2, "time1": time1, "time2": time2, "length": length
        }

        orig_prompt = tpl.format(**vars_dict)
        explanation = cot.format(**vars_dict)
        repaired = repair.format(**vars_dict) if label != "compatible" else orig_prompt

        entry = {
            "sample_id": f"PE11_{idx+1:05d}",
            "original_prompt": orig_prompt,
            "conflict_label": label,
            "conflict_category": cat_name if label != "compatible" else "None",
            "explanation": explanation,
            "repaired_prompt": repaired
        }
        dataset.append(entry)

    return dataset


def export_jsonl(dataset: list[dict], output_file: str | Path):
    """Write raw schema JSONL."""
    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"Exported {len(dataset)} samples to {path}")


def export_nemo_chat_jsonl(dataset: list[dict], output_file: str | Path):
    """Export dataset in NVIDIA NeMo / OpenAI chat completions format."""
    system_prompt = (
        "You are Project PE-11's Prompt Consistency Firewall. Analyze the input prompt for internal contradictions, "
        "impossible constraints, and structural paradoxes across Numerical, Logical, Temporal, Formatting, and Semantic dimensions. "
        "Output a strictly structured JSON response containing: conflict_label, conflict_category, explanation, and repaired_prompt."
    )

    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for item in dataset:
            assistant_content = json.dumps({
                "conflict_label": item["conflict_label"],
                "conflict_category": item["conflict_category"],
                "explanation": item["explanation"],
                "repaired_prompt": item["repaired_prompt"]
            }, indent=2)

            chat_record = {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": item["original_prompt"]},
                    {"role": "assistant", "content": assistant_content}
                ]
            }
            f.write(json.dumps(chat_record, ensure_ascii=False) + "\n")
    print(f"Exported {len(dataset)} chat fine-tuning samples to {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Project PE-11 ContradictPrompt Dataset")
    parser.add_argument("--count", type=int, default=1500, help="Number of samples to generate (1000 to 5000)")
    parser.add_argument("--output-jsonl", type=str, default="data/pe11_dataset.jsonl", help="Path to raw JSONL")
    parser.add_argument("--output-chat", type=str, default="data/pe11_nemo_chat.jsonl", help="Path to NeMo chat JSONL")
    args = parser.parse_args()

    print(f"Generating {args.count} high-variance samples for Project PE-11...")
    ds = generate_dataset(args.count)
    export_jsonl(ds, args.output_jsonl)
    export_nemo_chat_jsonl(ds, args.output_chat)
    print("Dataset generation completed successfully.")
