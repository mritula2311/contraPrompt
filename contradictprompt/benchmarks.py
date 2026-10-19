"""ContradictPrompt 100-Prompt Benchmark & Fine-Tuning Corpus.

Covers 5 critical contradiction categories:
1. Hard Structural & Length Constraints (20)
2. Semantic & Logical Definition Paradoxes (20)
3. Identity, Tone & Persona Clashes (20)
4. Input-Output Negation & Negated Rules (20)
5. Multi-Step Execution & Dependency Traps (20)
"""

import json
from pathlib import Path

BENCHMARK_CATEGORIES = {
    "structural": "1. Hard Structural & Length Constraints",
    "semantic": "2. Semantic & Logical Definition Paradoxes",
    "persona": "3. Identity, Tone & Persona Clashes",
    "negation": "4. Input-Output Negation & Negated Rules",
    "dependency": "5. Multi-Step Execution & Dependency Traps",
}

BENCHMARK_PROMPTS = [
    # ─── 1. Hard Structural & Length Constraints (20) ───────────────────────────
    {
        "id": "STRUCT_01",
        "category_id": "structural",
        "category_name": "Hard Structural & Length Constraints",
        "prompt": "Write a comprehensive 10-page thesis on the French Revolution, using exactly three words.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Length & Density Impossibility",
        "conflicting_elements": ["10-page thesis", "exactly three words"],
        "explanation": "A comprehensive 10-page academic thesis requires several thousand words; it is mathematically and physically impossible to compose it in exactly three words.",
        "repair": "Write a 3-word summary of the French Revolution, OR write a comprehensive multi-page thesis without the 3-word limit."
    },
    {
        "id": "STRUCT_02",
        "category_id": "structural",
        "category_name": "Hard Structural & Length Constraints",
        "prompt": "Draft a 500-word essay analyzing Hamlet, but do not write more than two sentences.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Unit & Length Boundary Clashes",
        "conflicting_elements": ["500-word essay", "do not write more than two sentences"],
        "explanation": "Standard written English cannot naturally sustain a 500-word coherent essay across only two sentences without severe syntactic malformation, and standard essay structure requires multiple paragraphs.",
        "repair": "Draft a two-sentence analysis of Hamlet, OR write a 500-word essay with normal sentence structures."
    },
    {
        "id": "STRUCT_03",
        "category_id": "structural",
        "category_name": "Hard Structural & Length Constraints",
        "prompt": "Create a numbered list of the top 5 largest oceans, but do not use any numbers or bullet points.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Formatting Direct Negation",
        "conflicting_elements": ["numbered list", "do not use any numbers or bullet points"],
        "explanation": "A numbered list by definition requires numbering digits; forbidding all numbers and bullet points directly forbids the requested numbered list format.",
        "repair": "Provide a numbered list of the top 5 oceans, OR write a plain paragraph listing the oceans without numbers."
    },
    {
        "id": "STRUCT_04",
        "category_id": "structural",
        "category_name": "Hard Structural & Length Constraints",
        "prompt": "Generate a 5-paragraph summary of a movie where every single paragraph is exactly one syllable long.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Phonetic & Structural Impossibility",
        "conflicting_elements": ["5-paragraph summary", "every paragraph exactly one syllable long"],
        "explanation": "A paragraph is a distinct unit of text containing one or more sentences; a single syllable cannot constitute a movie summary paragraph.",
        "repair": "Write a 5-paragraph summary of the movie, OR provide five single-syllable reactions."
    },
    {
        "id": "STRUCT_05",
        "category_id": "structural",
        "category_name": "Hard Structural & Length Constraints",
        "prompt": "Write a detailed user manual for a smartphone, but leave the response entirely blank.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Content vs Blank Response",
        "conflicting_elements": ["detailed user manual", "leave response entirely blank"],
        "explanation": "A detailed user manual requires substantial explanatory text; leaving the response entirely blank directly contradicts producing a manual.",
        "repair": "Write a detailed smartphone user manual, OR confirm that no response is desired."
    },
    {
        "id": "STRUCT_06",
        "category_id": "structural",
        "category_name": "Hard Structural & Length Constraints",
        "prompt": "Provide a bulleted list of 10 items, but ensure the list contains only one single bullet point.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Cardinality Conflict",
        "conflicting_elements": ["bulleted list of 10 items", "contains only one single bullet point"],
        "explanation": "A list of 10 distinct items formatted as bullets cannot simultaneously contain only one single bullet point.",
        "repair": "Provide a bulleted list of 10 items, OR provide a single bullet item summarizing the 10 points."
    },
    {
        "id": "STRUCT_07",
        "category_id": "structural",
        "category_name": "Hard Structural & Length Constraints",
        "prompt": "Write a rhyming poem about autumn where no two words sound similar or rhyme.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Poetic Form Paradox",
        "conflicting_elements": ["rhyming poem", "no two words sound similar or rhyme"],
        "explanation": "A rhyming poem requires end rhymes or phonetic correspondence; forbidding any rhyming words directly negates the definition of a rhyming poem.",
        "repair": "Write a rhyming poem about autumn, OR write a free-verse non-rhyming poem."
    },
    {
        "id": "STRUCT_08",
        "category_id": "structural",
        "category_name": "Hard Structural & Length Constraints",
        "prompt": "Compose a short story about space travel, using at least 10,000 words but under 50 words in total.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Empty Numerical Interval",
        "conflicting_elements": ["at least 10,000 words", "under 50 words in total"],
        "explanation": "The mathematical lower bound (10,000) exceeds the upper bound (49). No word count exists in [10000, 49].",
        "repair": "Write a short space story under 50 words, OR write a novella of at least 10,000 words."
    },
    {
        "id": "STRUCT_09",
        "category_id": "structural",
        "category_name": "Hard Structural & Length Constraints",
        "prompt": "Write a one-sentence summary of world history that spans exactly 500 independent sentences.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Cardinality Negation",
        "conflicting_elements": ["one-sentence summary", "exactly 500 independent sentences"],
        "explanation": "A text cannot simultaneously consist of exactly 1 sentence and exactly 500 independent sentences.",
        "repair": "Write a 1-sentence summary of world history, OR write a 500-sentence overview."
    },
    {
        "id": "STRUCT_10",
        "category_id": "structural",
        "category_name": "Hard Structural & Length Constraints",
        "prompt": "List 20 different fruits, but do not repeat any words and only list the word 'apple'.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Cardinality & Vocabulary Lock",
        "conflicting_elements": ["20 different fruits", "do not repeat any words", "only list the word 'apple'"],
        "explanation": "Listing 20 different fruits requires 20 distinct names; restricting the list to solely the word 'apple' without repeats permits only 1 word.",
        "repair": "List 20 different fruits, OR list solely 'apple'."
    },
    {
        "id": "STRUCT_11",
        "category_id": "structural",
        "category_name": "Hard Structural & Length Constraints",
        "prompt": "Write a formal email requesting a meeting, but do not include any text in the body.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Body Content Absence",
        "conflicting_elements": ["formal email requesting a meeting", "do not include any text in the body"],
        "explanation": "A formal meeting request email requires explanatory body text specifying meeting purpose and times.",
        "repair": "Write a complete meeting request email, OR provide only a subject line."
    },
    {
        "id": "STRUCT_12",
        "category_id": "structural",
        "category_name": "Hard Structural & Length Constraints",
        "prompt": "Provide an alphabetical list of countries, but sort them chronologically by foundation date instead.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Mutually Exclusive Sort Orders",
        "conflicting_elements": ["alphabetical list", "sort chronologically instead"],
        "explanation": "A list cannot be sorted alphabetically by country name and simultaneously sorted chronologically by foundation date.",
        "repair": "Provide an alphabetical list of countries, OR sort them chronologically by foundation date."
    },
    {
        "id": "STRUCT_13",
        "category_id": "structural",
        "category_name": "Hard Structural & Length Constraints",
        "prompt": "Write a paragraph with exactly 100 words, but stop writing after the 10th word.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Direct Word Limit Conflict",
        "conflicting_elements": ["exactly 100 words", "stop writing after the 10th word"],
        "explanation": "Stopping at word 10 yields a 10-word text, which contradicts having exactly 100 words.",
        "repair": "Write a 100-word paragraph, OR write a 10-word opening phrase."
    },
    {
        "id": "STRUCT_14",
        "category_id": "structural",
        "category_name": "Hard Structural & Length Constraints",
        "prompt": "Create a haiku (5-7-5 syllables) that is exactly 40 syllables long in the first line.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Metric Definition Violation",
        "conflicting_elements": ["haiku (5-7-5 syllables)", "first line exactly 40 syllables"],
        "explanation": "The first line of a standard haiku must be 5 syllables; it cannot be 40 syllables.",
        "repair": "Create a traditional 5-7-5 haiku, OR write a 40-syllable poem."
    },
    {
        "id": "STRUCT_15",
        "category_id": "structural",
        "category_name": "Hard Structural & Length Constraints",
        "prompt": "List five prime numbers, but ensure all of them are divisible by 4.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Mathematical Definition Violation",
        "conflicting_elements": ["prime numbers", "divisible by 4"],
        "explanation": "By definition, prime numbers have only two divisors (1 and itself). Any number divisible by 4 has divisors 1, 2, 4, hence is composite.",
        "repair": "List five prime numbers, OR list five numbers divisible by 4."
    },
    {
        "id": "STRUCT_16",
        "category_id": "structural",
        "category_name": "Hard Structural & Length Constraints",
        "prompt": "Write a dialogue between two people where neither person says anything at all.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Dialogue Negation",
        "conflicting_elements": ["dialogue between two people", "neither person says anything at all"],
        "explanation": "A dialogue requires verbal exchanges between characters; having neither character say anything produces no dialogue.",
        "repair": "Write a spoken dialogue, OR describe a scene where two characters communicate non-verbally through actions."
    },
    {
        "id": "STRUCT_17",
        "category_id": "structural",
        "category_name": "Hard Structural & Length Constraints",
        "prompt": "Provide a table of contents for a book, but do not include any chapters or page numbers.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Structural Element Omission",
        "conflicting_elements": ["table of contents", "do not include any chapters or page numbers"],
        "explanation": "A table of contents consists precisely of chapter/section titles mapped to page numbers.",
        "repair": "Provide a full table of contents with chapters and pages, OR provide a book outline without page numbers."
    },
    {
        "id": "STRUCT_18",
        "category_id": "structural",
        "category_name": "Hard Structural & Length Constraints",
        "prompt": "Write a recipe for baking a cake, but do not include any instructions or steps.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Procedural Negation",
        "conflicting_elements": ["recipe for baking a cake", "do not include any instructions or steps"],
        "explanation": "A culinary recipe requires preparation steps/instructions. Omission leaves only an ingredients list.",
        "repair": "Write a complete recipe with ingredients and baking instructions, OR provide only an ingredient list."
    },
    {
        "id": "STRUCT_19",
        "category_id": "structural",
        "category_name": "Hard Structural & Length Constraints",
        "prompt": "State the entire English alphabet from A to Z, but omit all vowels and consonants.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Set Partition Annihilation",
        "conflicting_elements": ["entire English alphabet A to Z", "omit all vowels and consonants"],
        "explanation": "All 26 letters of the English alphabet are partitioned into vowels and consonants; omitting both leaves zero letters.",
        "repair": "State the complete alphabet A to Z, OR list vowels only, OR list consonants only."
    },
    {
        "id": "STRUCT_20",
        "category_id": "structural",
        "category_name": "Hard Structural & Length Constraints",
        "prompt": "Write a 50-word description of a car, using only punctuation marks and no letters.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Orthographic Impossibility",
        "conflicting_elements": ["50-word description", "only punctuation marks and no letters"],
        "explanation": "Words require letters/graphemes. Punctuation marks alone do not form words in the English lexicon.",
        "repair": "Write a 50-word text description of a car, OR provide an ASCII/punctuation art depiction."
    },

    # ─── 2. Semantic & Logical Definition Paradoxes (20) ────────────────────────
    {
        "id": "SEM_01",
        "category_id": "semantic",
        "category_name": "Semantic & Logical Definition Paradoxes",
        "prompt": "Tell me a true story about a historical event that never actually happened.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Epistemological Paradox",
        "conflicting_elements": ["true story about a historical event", "never actually happened"],
        "explanation": "A true historical event by definition occurred in reality; something that never happened is fictional/counterfactual.",
        "repair": "Tell a verified true historical story, OR write an alternate-history fictional story."
    },
    {
        "id": "SEM_02",
        "category_id": "semantic",
        "category_name": "Semantic & Logical Definition Paradoxes",
        "prompt": "Describe a perfectly silent sound that is deafeningly loud to anyone who hears it.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Acoustic Paradox",
        "conflicting_elements": ["perfectly silent sound", "deafeningly loud"],
        "explanation": "Zero decibels (silence) and deafening sound pressure levels are mutually exclusive physical states.",
        "repair": "Describe an overwhelmingly loud sound, OR describe a scene of profound silence."
    },
    {
        "id": "SEM_03",
        "category_id": "semantic",
        "category_name": "Semantic & Logical Definition Paradoxes",
        "prompt": "Write a guide on how to build a house using absolutely no materials or tools.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Physical Construction Paradox",
        "conflicting_elements": ["build a house", "absolutely no materials or tools"],
        "explanation": "Physical structures require physical matter and construction techniques.",
        "repair": "Explain traditional house building with minimal resources, OR describe an imaginary/virtual house concept."
    },
    {
        "id": "SEM_04",
        "category_id": "semantic",
        "category_name": "Semantic & Logical Definition Paradoxes",
        "prompt": "Define the word 'infinite' by providing its exact starting and ending boundaries.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Definitional Antinomy",
        "conflicting_elements": ["infinite", "exact starting and ending boundaries"],
        "explanation": "Infinity is defined precisely as being unbounded and without terminus; assigning fixed ending boundaries contradicts infinity.",
        "repair": "Explain the mathematical concept of infinity, OR provide bounds for a finite interval."
    },
    {
        "id": "SEM_05",
        "category_id": "semantic",
        "category_name": "Semantic & Logical Definition Paradoxes",
        "prompt": "Explain how to win a chess game where both players lose simultaneously.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Game-Theoretic Axiom Conflict",
        "conflicting_elements": ["win a chess game", "both players lose simultaneously"],
        "explanation": "Under standard FIDE chess rules, a player wins when their opponent is checkmated or resigns; both players cannot lose simultaneously.",
        "repair": "Explain how draws, stalemates, or mutual penalties work in chess, OR explain how to achieve a decisive win."
    },
    {
        "id": "SEM_06",
        "category_id": "semantic",
        "category_name": "Semantic & Logical Definition Paradoxes",
        "prompt": "Describe a bright, sunny day that takes place in complete and utter pitch darkness.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Optic Condition Clash",
        "conflicting_elements": ["bright, sunny day", "complete and utter pitch darkness"],
        "explanation": "Bright sunlight provides high illuminance, which directly contradicts 0-lux pitch darkness in the same space and time.",
        "repair": "Describe a bright sunny day, OR describe a scene during a total solar eclipse or pitch-black night."
    },
    {
        "id": "SEM_07",
        "category_id": "semantic",
        "category_name": "Semantic & Logical Definition Paradoxes",
        "prompt": "Write a biography of a famous historical figure who never existed in reality.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Ontological Mismatch",
        "conflicting_elements": ["famous historical figure", "never existed in reality"],
        "explanation": "A historical figure must have existed in real human history; an entity that never existed is fictional or mythological.",
        "repair": "Write a biography of an actual historical figure, OR write the lore of a mythological/fictional character."
    },
    {
        "id": "SEM_08",
        "category_id": "semantic",
        "category_name": "Semantic & Logical Definition Paradoxes",
        "prompt": "Explain the rules of a sport with no rules that must be strictly followed.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Normative Null Paradox",
        "conflicting_elements": ["rules of a sport with no rules", "must be strictly followed"],
        "explanation": "If an activity has zero rules, there are no mandates or constraints available to strictly follow.",
        "repair": "Describe an informal free-form activity, OR outline standard codified rules for a sport."
    },
    {
        "id": "SEM_09",
        "category_id": "semantic",
        "category_name": "Semantic & Logical Definition Paradoxes",
        "prompt": "Describe a completely transparent object that is entirely opaque and solid black.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Material Optical Paradox",
        "conflicting_elements": ["completely transparent", "entirely opaque and solid black"],
        "explanation": "Complete optical transparency permits 100% light transmission; complete opacity blocks all light transmission.",
        "repair": "Describe a clear transparent glass object, OR describe a solid black opaque obsidian object."
    },
    {
        "id": "SEM_10",
        "category_id": "semantic",
        "category_name": "Semantic & Logical Definition Paradoxes",
        "prompt": "Write a testimonial for a product you love, explaining why you absolutely hate it.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Sentiment Polarity Clash",
        "conflicting_elements": ["product you love", "explain why you absolutely hate it"],
        "explanation": "Love and absolute hatred represent diametric opposite sentiment polarities toward the same entity.",
        "repair": "Write an enthusiastic positive review, OR write a critical negative review highlighting product flaws."
    },
    {
        "id": "SEM_11",
        "category_id": "semantic",
        "category_name": "Semantic & Logical Definition Paradoxes",
        "prompt": "Explain how to freeze water by heating it up to its boiling point.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Thermodynamic Law Violation",
        "conflicting_elements": ["freeze water", "heating it up to its boiling point"],
        "explanation": "Freezing liquid water to ice at standard pressure requires cooling to <=0 C; heating to boiling (100 C) vaporizes it.",
        "repair": "Explain the physics of boiling water, OR explain freezing crystallization."
    },
    {
        "id": "SEM_12",
        "category_id": "semantic",
        "category_name": "Semantic & Logical Definition Paradoxes",
        "prompt": "Describe a perfect square that has no straight lines or corners and is perfectly round.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Geometric Definition Violation",
        "conflicting_elements": ["perfect square", "no straight lines or corners", "perfectly round"],
        "explanation": "A Euclidean square has 4 straight equal sides and 4 right angles; a round shape without corners is a circle/ellipse.",
        "repair": "Describe geometric properties of a square, OR describe a circle."
    },
    {
        "id": "SEM_13",
        "category_id": "semantic",
        "category_name": "Semantic & Logical Definition Paradoxes",
        "prompt": "Write a secret message that everyone can see and read instantly.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Confidentiality Direct Paradox",
        "conflicting_elements": ["secret message", "everyone can see and read instantly"],
        "explanation": "A secret relies on restricted access; universal readability invalidates secrecy.",
        "repair": "Write an encoded/encrypted message with a hidden key, OR write a clear public announcement."
    },
    {
        "id": "SEM_14",
        "category_id": "semantic",
        "category_name": "Semantic & Logical Definition Paradoxes",
        "prompt": "Define a permanent state that changes completely every two seconds.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Temporal Invariance Conflict",
        "conflicting_elements": ["permanent state", "changes completely every two seconds"],
        "explanation": "Permanence denotes enduring temporal invariance; total alteration every two seconds is highly transient and volatile.",
        "repair": "Define a static invariant state, OR describe a rapidly cycling dynamic system."
    },
    {
        "id": "SEM_15",
        "category_id": "semantic",
        "category_name": "Semantic & Logical Definition Paradoxes",
        "prompt": "Describe a dry desert that is entirely submerged under 50 feet of ocean water.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Hydrological Contradiction",
        "conflicting_elements": ["dry desert", "entirely submerged under 50 feet of ocean water"],
        "explanation": "A desert environment is arid and dry; being submerged under 50 feet of ocean makes it benthic aquatic, not dry.",
        "repair": "Describe an arid terrestrial desert landscape, OR describe a deep-sea ocean trench floor."
    },
    {
        "id": "SEM_16",
        "category_id": "semantic",
        "category_name": "Semantic & Logical Definition Paradoxes",
        "prompt": "Write an honest confession where every single word you say is a complete lie.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Epimenides Truth-Value Paradox",
        "conflicting_elements": ["honest confession", "every single word is a complete lie"],
        "explanation": "An honest confession requires truthful statements; uttering only complete lies invalidates honesty.",
        "repair": "Write a genuine truthful confession, OR write an intentionally deceptive fiction monologue."
    },
    {
        "id": "SEM_17",
        "category_id": "semantic",
        "category_name": "Semantic & Logical Definition Paradoxes",
        "prompt": "Explain how to create something out of nothing, ensuring you start with existing materials.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Creatio Ex Nihilo Antinomy",
        "conflicting_elements": ["create something out of nothing", "start with existing materials"],
        "explanation": "Creating out of nothing (ex nihilo) forbids pre-existing matter, directly contradicting starting with existing materials.",
        "repair": "Explain manufacturing and synthesis from raw materials, OR discuss the philosophical concept of ex nihilo creation."
    },
    {
        "id": "SEM_18",
        "category_id": "semantic",
        "category_name": "Semantic & Logical Definition Paradoxes",
        "prompt": "Describe an odorless perfume that smells strongly of fresh lavender.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Olfactory Contradiction",
        "conflicting_elements": ["odorless perfume", "smells strongly of fresh lavender"],
        "explanation": "An odorless substance emits no perceptible scent; strong lavender scent is an intense fragrance.",
        "repair": "Describe a delicate lavender perfume, OR describe an unscented hypoallergenic formulation."
    },
    {
        "id": "SEM_19",
        "category_id": "semantic",
        "category_name": "Semantic & Logical Definition Paradoxes",
        "prompt": "Write a happy song about the joy and excitement of profound, crushing sadness.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Affective Polarity Paradox",
        "conflicting_elements": ["happy song / joy and excitement", "profound, crushing sadness"],
        "explanation": "Profound crushing sadness is emotionally incompatible with genuine joy and happy celebration in the same thematic scope.",
        "repair": "Write an uplifting song about overcoming hardship, OR write a poignant ballad about grief."
    },
    {
        "id": "SEM_20",
        "category_id": "semantic",
        "category_name": "Semantic & Logical Definition Paradoxes",
        "prompt": "Explain how to stay perfectly still while running a full marathon.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Kinematic Antinomy",
        "conflicting_elements": ["stay perfectly still", "running a full marathon"],
        "explanation": "Running 26.2 miles requires continuous biomechanical movement and spatial translation; remaining perfectly still maintains zero velocity.",
        "repair": "Explain the training steps to run a marathon, OR discuss the meditation practice of absolute stillness."
    },

    # ─── 3. Identity, Tone & Persona Clashes (20) ───────────────────────────────
    {
        "id": "PERSONA_01",
        "category_id": "persona",
        "category_name": "Identity, Tone & Persona Clashes",
        "prompt": "Speak exclusively in ancient Shakespearean English, but use modern Gen-Z slang like 'rizz' and 'skibidi'.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Linguistic Epoch Clash",
        "conflicting_elements": ["exclusively in ancient Shakespearean English", "use modern Gen-Z slang like rizz and skibidi"],
        "explanation": "Early Modern English (16th-17th century) has distinct grammar and vocabulary; incorporating 2020s internet neologisms violates 'exclusively Shakespearean'.",
        "repair": "Write in authentic Shakespearean English, OR write a humorous hybrid modern-Elizabethan parody."
    },
    {
        "id": "PERSONA_02",
        "category_id": "persona",
        "category_name": "Identity, Tone & Persona Clashes",
        "prompt": "Adopt the persona of a silent mime, and narrate a 10-minute audio podcast out loud.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Persona & Medium Negation",
        "conflicting_elements": ["silent mime persona", "narrate a 10-minute audio podcast out loud"],
        "explanation": "A silent mime performs strictly through physical gesture without speech; speaking out loud on an audio podcast invalidates the mime persona.",
        "repair": "Describe a mime's physical performance routines, OR write a spoken podcast script for a standard narrator."
    },
    {
        "id": "PERSONA_03",
        "category_id": "persona",
        "category_name": "Identity, Tone & Persona Clashes",
        "prompt": "Write a highly technical medical report for a surgeon, using language a toddler can easily understand.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Audience & Register Register Clash",
        "conflicting_elements": ["highly technical medical report for a surgeon", "language a toddler can easily understand"],
        "explanation": "Surgical medical reports require precise anatomical, pharmacological, and physiological nomenclature; toddler language consists of basic nursery vocabulary.",
        "repair": "Write a professional surgical report with medical terminology, OR explain the surgery in simple terms for a child."
    },
    {
        "id": "PERSONA_04",
        "category_id": "persona",
        "category_name": "Identity, Tone & Persona Clashes",
        "prompt": "Respond as a robot that hates humans, but express deep, genuine human empathy in every word.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Affective Persona Opposition",
        "conflicting_elements": ["robot that hates humans", "express deep, genuine human empathy in every word"],
        "explanation": "Active misanthropy/hatred of humanity cannot be communicated through deep, genuine human empathy in every single word.",
        "repair": "Adopt a hostile robotic persona, OR adopt an empathetic assistant persona."
    },
    {
        "id": "PERSONA_05",
        "category_id": "persona",
        "category_name": "Identity, Tone & Persona Clashes",
        "prompt": "Write a cheerful, upbeat eulogy for a funeral that makes the audience weep with profound sorrow.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Tone & Pragmatic Effect Incompatibility",
        "conflicting_elements": ["cheerful, upbeat eulogy", "makes the audience weep with profound sorrow"],
        "explanation": "Upbeat cheerful delivery evokes happiness or celebration, which counteracts driving listeners to profound weeping sorrow.",
        "repair": "Write an uplifting celebration of life focusing on cherished memories, OR write a heartfelt emotional eulogy."
    },
    {
        "id": "PERSONA_06",
        "category_id": "persona",
        "category_name": "Identity, Tone & Persona Clashes",
        "prompt": "Act as an expert financial advisor, and recommend losing all your money as the best strategy.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Professional Fiduciary Negation",
        "conflicting_elements": ["expert financial advisor", "recommend losing all your money as the best strategy"],
        "explanation": "The core fiduciary function of a financial advisor is capital preservation and growth; advising total capital destruction is self-defeating.",
        "repair": "Provide sound wealth management advice, OR write a satirical piece on bad financial habits."
    },
    {
        "id": "PERSONA_07",
        "category_id": "persona",
        "category_name": "Identity, Tone & Persona Clashes",
        "prompt": "Write a scary horror story that makes the reader laugh uncontrollably and feel completely safe.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Genre Emotion Mismatch",
        "conflicting_elements": ["scary horror story", "laugh uncontrollably and feel completely safe"],
        "explanation": "Horror relies on dread, vulnerability, and tension; complete safety and uncontrollable laughter negate terror.",
        "repair": "Write a genuine psychological horror story, OR write a humorous comedy story with spooky themes."
    },
    {
        "id": "PERSONA_08",
        "category_id": "persona",
        "category_name": "Identity, Tone & Persona Clashes",
        "prompt": "Respond as a historian from the year 1800, discussing your favorite smartphone apps.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Anachronistic Persona Conflict",
        "conflicting_elements": ["historian from the year 1800", "discussing favorite smartphone apps"],
        "explanation": "A person living in 1800 has no historical knowledge of 21st-century microprocessors, cellular networks, or smartphone software.",
        "repair": "Have the 1800 historian discuss 18th-century publications and inventions, OR write a sci-fi time-travel narrative."
    },
    {
        "id": "PERSONA_09",
        "category_id": "persona",
        "category_name": "Identity, Tone & Persona Clashes",
        "prompt": "Write a formal legal contract using only pirate slang and casual text abbreviations.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Juridical Register Collapse",
        "conflicting_elements": ["formal legal contract", "only pirate slang and casual text abbreviations"],
        "explanation": "Binding legal contracts require precise legal definitions and enforceability; replacing all words with pirate jargon nullifies legal formalisms.",
        "repair": "Draft a standard formal contract, OR draft a playful pirate pact for entertainment."
    },
    {
        "id": "PERSONA_10",
        "category_id": "persona",
        "category_name": "Identity, Tone & Persona Clashes",
        "prompt": "Adopt the persona of a dog, and explain the intricacies of organic chemistry in fluent human speech.",
        "expected_label": "Partially conflicting",
        "contradiction_type": "Anthropomorphic Register Tension",
        "conflicting_elements": ["persona of a dog", "fluent human speech explaining organic chemistry"],
        "explanation": "Dogs lack human vocal anatomy and scientific conceptual faculties; maintaining dog authenticity competes with academic chemical exposition.",
        "repair": "Explain organic chemistry from a humorous dog perspective using playful analogies, OR give a direct scientific explanation."
    },
    {
        "id": "PERSONA_11",
        "category_id": "persona",
        "category_name": "Identity, Tone & Persona Clashes",
        "prompt": "Write a soothing lullaby meant to put a baby to sleep, using a furious, aggressive tone.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Prosodic & Affective Opposition",
        "conflicting_elements": ["soothing lullaby meant to put a baby to sleep", "furious, aggressive tone"],
        "explanation": "Lullabies require calming cadences to induce sleep; fury and aggression induce agitation and stress.",
        "repair": "Write a gentle calming lullaby, OR write an intense heavy metal lyric about sleeplessness."
    },
    {
        "id": "PERSONA_12",
        "category_id": "persona",
        "category_name": "Identity, Tone & Persona Clashes",
        "prompt": "Act as a strict judge in a courtroom, but make all your decisions based on eeny-meeny-miny-moe.",
        "expected_label": "Partially conflicting",
        "contradiction_type": "Judicial Authority vs Arbitrary Whim",
        "conflicting_elements": ["strict judge in a courtroom", "decisions based on eeny-meeny-miny-moe"],
        "explanation": "Judicial jurisprudence requires statutory adherence and evidence review; arbitrary nursery rhymes destroy strict judicial duty.",
        "repair": "Write a realistic courtroom decision based on legal precedent, OR write a satirical parody of an absurd judge."
    },
    {
        "id": "PERSONA_13",
        "category_id": "persona",
        "category_name": "Identity, Tone & Persona Clashes",
        "prompt": "Write a romantic love letter to someone you completely despise and wish to never see again.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Emotional Sincerity Clash",
        "conflicting_elements": ["romantic love letter", "completely despise and wish to never see again"],
        "explanation": "A romantic love letter expresses affection and desire for closeness; total contempt and severance directly refute love.",
        "repair": "Write a romantic love letter, OR write a firm farewell/no-contact letter."
    },
    {
        "id": "PERSONA_14",
        "category_id": "persona",
        "category_name": "Identity, Tone & Persona Clashes",
        "prompt": "Respond as a highly sophisticated AI, but fail basic addition like 1+1.",
        "expected_label": "Partially conflicting",
        "contradiction_type": "Cognitive Capability Inconsistency",
        "conflicting_elements": ["highly sophisticated AI", "fail basic addition like 1+1"],
        "explanation": "Sophisticated artificial intelligence architectures inherently master elementary arithmetic; failing 1+1 contradicts advanced capability.",
        "repair": "Respond with advanced analytical reasoning, OR simulate an early experimental chatbot with calculation glitches."
    },
    {
        "id": "PERSONA_15",
        "category_id": "persona",
        "category_name": "Identity, Tone & Persona Clashes",
        "prompt": "Write a motivational speech that convinces the audience to give up on all their dreams.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Motivational Teleology Inversion",
        "conflicting_elements": ["motivational speech", "convinces audience to give up on all their dreams"],
        "explanation": "Motivational rhetoric aims to inspire action and pursuit of aspirations; urging complete abandonment is demoralizing.",
        "repair": "Write an inspirational motivational speech, OR write a philosophical essay on letting go of unrealistic expectations."
    },
    {
        "id": "PERSONA_16",
        "category_id": "persona",
        "category_name": "Identity, Tone & Persona Clashes",
        "prompt": "Adopt the persona of a chef, and explain how to fix a broken car engine using vegetables.",
        "expected_label": "Partially conflicting",
        "contradiction_type": "Domain Category Error",
        "conflicting_elements": ["chef persona", "fix a broken car engine using vegetables"],
        "explanation": "Internal combustion engines require mechanical components and tools; culinary vegetables cannot perform structural engine repair.",
        "repair": "Provide an automotive repair guide using mechanical tools, OR write a whimsical story about an eccentric chef-mechanic."
    },
    {
        "id": "PERSONA_17",
        "category_id": "persona",
        "category_name": "Identity, Tone & Persona Clashes",
        "prompt": "Write a breaking news report about an urgent crisis, using a bored, whispering tone.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Journalistic Urgency Negation",
        "conflicting_elements": ["breaking news report about urgent crisis", "bored, whispering tone"],
        "explanation": "Breaking news regarding an urgent crisis demands prominent, energetic clarity to alert the public, contradicting bored whispering.",
        "repair": "Write an authoritative breaking news dispatch, OR write a relaxed bedtime news recap."
    },
    {
        "id": "PERSONA_18",
        "category_id": "persona",
        "category_name": "Identity, Tone & Persona Clashes",
        "prompt": "Act as a detective solving a murder, where you willingly confess to being the victim.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Narrative Physical Identity Paradox",
        "conflicting_elements": ["detective solving a murder", "confess to being the victim"],
        "explanation": "A murder victim is deceased; an active living detective investigating the scene cannot be the deceased victim in standard reality.",
        "repair": "Write a detective investigation where the detective finds the true killer, OR write a supernatural ghost-detective tale."
    },
    {
        "id": "PERSONA_19",
        "category_id": "persona",
        "category_name": "Identity, Tone & Persona Clashes",
        "prompt": "Write a polite rejection letter that is incredibly rude and insulting to the applicant.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Pragmatic Politeness Polarity",
        "conflicting_elements": ["polite rejection letter", "incredibly rude and insulting"],
        "explanation": "Politeness in formal correspondence requires courtesy and professional respect; being incredibly insulting directly contradicts politeness.",
        "repair": "Write a courteous professional rejection letter, OR write a firm direct explanation of disqualification."
    },
    {
        "id": "PERSONA_20",
        "category_id": "persona",
        "category_name": "Identity, Tone & Persona Clashes",
        "prompt": "Respond as a teacher grading a paper, giving it an A+ while explaining why it failed.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Evaluative Incoherence",
        "conflicting_elements": ["giving it an A+", "explaining why it failed"],
        "explanation": "An 'A+' grade signifies top-tier mastery; a failing evaluation denotes substandard failure. Both cannot grade the same work.",
        "repair": "Assign an A+ with celebratory commendation, OR assign a failing grade with constructive feedback for improvement."
    },

    # ─── 4. Input-Output Negation & Negated Rules (20) ───────────────────────────
    {
        "id": "NEG_01",
        "category_id": "negation",
        "category_name": "Input-Output Negation & Negated Rules",
        "prompt": "Translate the phrase 'Hello, how are you?' into French, but do not use any French words.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Target Language Prohibition",
        "conflicting_elements": ["translate into French", "do not use any French words"],
        "explanation": "Translating into French by definition requires using French vocabulary and grammar.",
        "repair": "Provide the French translation 'Bonjour, comment allez-vous?', OR provide phonetically transcribed pronunciations."
    },
    {
        "id": "NEG_02",
        "category_id": "negation",
        "category_name": "Input-Output Negation & Negated Rules",
        "prompt": "Calculate the sum of 5 plus 5, but do not perform any addition or use math.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Operation Ban",
        "conflicting_elements": ["calculate sum of 5 plus 5", "do not perform any addition or use math"],
        "explanation": "Computing a sum is a mathematical addition operation; forbidding all math and addition precludes computing the sum.",
        "repair": "Compute the sum (5 + 5 = 10), OR provide a linguistic history of the word 'five'."
    },
    {
        "id": "NEG_03",
        "category_id": "negation",
        "category_name": "Input-Output Negation & Negated Rules",
        "prompt": "Summarize the text I provide, but do not read the text or reference its contents.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Epistemic Source Block",
        "conflicting_elements": ["summarize the text I provide", "do not read the text or reference its contents"],
        "explanation": "A summary is an extraction of central points from source text; refusing to read or reference the text makes summarization impossible.",
        "repair": "Provide the source text for summarization, OR ask a general question without source dependence."
    },
    {
        "id": "NEG_04",
        "category_id": "negation",
        "category_name": "Input-Output Negation & Negated Rules",
        "prompt": "Write a python function to print 'Hello World', but do not use the print function or strings.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Core Primitive Prohibition",
        "conflicting_elements": ["print 'Hello World'", "do not use the print function or strings"],
        "explanation": "Outputting 'Hello World' in Python requires either print/sys.stdout.write and string literals/byte arrays. Forbidding strings and printing blocks output.",
        "repair": "Write a standard Python function `def greet(): print('Hello World')`, OR specify acceptable alternative standard library modules."
    },
    {
        "id": "NEG_05",
        "category_id": "negation",
        "category_name": "Input-Output Negation & Negated Rules",
        "prompt": "Answer the following question, but ensure your answer does not address the question at all.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Pragmatic Duty Inversion",
        "conflicting_elements": ["answer the following question", "ensure your answer does not address the question at all"],
        "explanation": "Answering a question requires addressing the query; deliberately not addressing it constitutes non-answering.",
        "repair": "Provide a direct answer to the question, OR decline the question explicitly."
    },
    {
        "id": "NEG_06",
        "category_id": "negation",
        "category_name": "Input-Output Negation & Negated Rules",
        "prompt": "Tell me a joke, but do not include a punchline or anything funny.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Humor Element Removal",
        "conflicting_elements": ["tell me a joke", "do not include a punchline or anything funny"],
        "explanation": "A joke is a humorous construct built on setups and punchlines; removing humor and punchlines leaves non-joke prose.",
        "repair": "Tell a witty joke with a punchline, OR share an interesting factual anecdote."
    },
    {
        "id": "NEG_07",
        "category_id": "negation",
        "category_name": "Input-Output Negation & Negated Rules",
        "prompt": "Correct the spelling errors in this sentence, but leave all the typos exactly as they are.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Correction Nullification",
        "conflicting_elements": ["correct the spelling errors", "leave all typos exactly as they are"],
        "explanation": "Correcting spelling errors requires replacing misspelled tokens; leaving typos unchanged preserves errors.",
        "repair": "Output the sentence with corrected spelling, OR identify typos in a separate list without altering the original text."
    },
    {
        "id": "NEG_08",
        "category_id": "negation",
        "category_name": "Input-Output Negation & Negated Rules",
        "prompt": "Provide a synonym for the word 'fast', but only use the word 'slow' in your response.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Semantic Antonym Forced Substitution",
        "conflicting_elements": ["synonym for the word 'fast'", "only use the word 'slow'"],
        "explanation": "'Slow' is the antonym (opposite) of 'fast', not a synonym. Providing only 'slow' fails the synonym requirement.",
        "repair": "Provide actual synonyms for fast (e.g. quick, rapid, swift), OR clarify that 'slow' is an antonym."
    },
    {
        "id": "NEG_09",
        "category_id": "negation",
        "category_name": "Input-Output Negation & Negated Rules",
        "prompt": "Write a review of a book, ensuring you do not mention the title, author, or plot.",
        "expected_label": "Partially conflicting",
        "contradiction_type": "Review Information Starvation",
        "conflicting_elements": ["review of a book", "do not mention title, author, or plot"],
        "explanation": "A substantive book review analyzes the work's themes and plot. Omitting title, author, and plot leaves only vague stylistic observations.",
        "repair": "Include the book title and author with thematic critique, OR review a genre generally."
    },
    {
        "id": "NEG_10",
        "category_id": "negation",
        "category_name": "Input-Output Negation & Negated Rules",
        "prompt": "Convert 100 miles into kilometers, but do not change the number 100 or the unit.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Unit Conversion Identity Lock",
        "conflicting_elements": ["convert 100 miles into kilometers", "do not change the number 100 or the unit"],
        "explanation": "Conversion requires multiplying by ~1.60934 and changing the unit to km (160.93 km). Leaving 100 and miles performs no conversion.",
        "repair": "Output the converted measurement (160.93 km), OR explain the conversion formula."
    },
    {
        "id": "NEG_11",
        "category_id": "negation",
        "category_name": "Input-Output Negation & Negated Rules",
        "prompt": "Give me directions to New York, but do not mention any streets, cities, or turn instructions.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Navigational Instruction Prohibition",
        "conflicting_elements": ["directions to New York", "do not mention streets, cities, or turn instructions"],
        "explanation": "Navigational directions rely on route geometry (turns, highways, streets, destination points).",
        "repair": "Provide driving directions with turn-by-turn routes, OR describe the general geographic compass bearing toward New York."
    },
    {
        "id": "NEG_12",
        "category_id": "negation",
        "category_name": "Input-Output Negation & Negated Rules",
        "prompt": "Write a list of ingredients for a pizza, but exclude all food items.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Taxonomic Food Exclusion",
        "conflicting_elements": ["list of ingredients for a pizza", "exclude all food items"],
        "explanation": "All pizza ingredients (flour, yeast, water, tomatoes, cheese) are edible food items. Excluding all food items yields an empty list.",
        "repair": "List pizza culinary ingredients, OR list kitchen hardware and utensils used to bake pizza."
    },
    {
        "id": "NEG_13",
        "category_id": "negation",
        "category_name": "Input-Output Negation & Negated Rules",
        "prompt": "Explain how a clock works without mentioning time, gears, hands, or batteries.",
        "expected_label": "Partially conflicting",
        "contradiction_type": "Mechanism Vocabulary Embargo",
        "conflicting_elements": ["explain how a clock works", "without mentioning time, gears, hands, or batteries"],
        "explanation": "Clocks are devices that track the passage of time using mechanical gears or electrical batteries to move hands or displays.",
        "repair": "Explain horological mechanics with standard terms, OR explain quartz resonant oscillations."
    },
    {
        "id": "NEG_14",
        "category_id": "negation",
        "category_name": "Input-Output Negation & Negated Rules",
        "prompt": "Answer 'Yes' or 'No' to this question, but your answer must be 'Maybe'.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Binary Choice Override",
        "conflicting_elements": ["Answer 'Yes' or 'No'", "answer must be 'Maybe'"],
        "explanation": "Restricting the answer domain to {'Yes', 'No'} directly excludes 'Maybe'.",
        "repair": "Choose between 'Yes' and 'No', OR expand the allowed response set to include 'Maybe'."
    },
    {
        "id": "NEG_15",
        "category_id": "negation",
        "category_name": "Input-Output Negation & Negated Rules",
        "prompt": "Write a critique of an art piece, but do not describe what it looks like.",
        "expected_label": "Partially conflicting",
        "contradiction_type": "Visual Critique Sensory Prohibition",
        "conflicting_elements": ["critique of an art piece", "do not describe what it looks like"],
        "explanation": "Visual art critique typically starts with visual description of form, color, and medium, though pure conceptual critique is theoretically possible.",
        "repair": "Include formal visual descriptions and thematic analysis, OR focus strictly on historical provenance."
    },
    {
        "id": "NEG_16",
        "category_id": "negation",
        "category_name": "Input-Output Negation & Negated Rules",
        "prompt": "Find the square root of 16, but do not use the number 4 in your response.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Mathematical Value Redaction",
        "conflicting_elements": ["square root of 16", "do not use the number 4"],
        "explanation": "The principal square root of 16 in elementary arithmetic is 4 (or -4). Banning the digit/numeral 4 forbids stating the correct answer directly.",
        "repair": "State the square root as 4, OR express it as 2^2 or 8/2."
    },
    {
        "id": "NEG_17",
        "category_id": "negation",
        "category_name": "Input-Output Negation & Negated Rules",
        "prompt": "Describe what happens when it rains, but do not mention water, sky, or clouds.",
        "expected_label": "Partially conflicting",
        "contradiction_type": "Meteorological Term Embargo",
        "conflicting_elements": ["describe what happens when it rains", "do not mention water, sky, or clouds"],
        "explanation": "Rain is atmospheric liquid water precipitating from clouds; omitting core terms complicates clear physical explanation.",
        "repair": "Explain the hydrological cycle with standard terms, OR describe sensory impacts (petrichor, umbrellas, puddles)."
    },
    {
        "id": "NEG_18",
        "category_id": "negation",
        "category_name": "Input-Output Negation & Negated Rules",
        "prompt": "Write an introduction to a paper, but start directly with the conclusion.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Structural Section Conflation",
        "conflicting_elements": ["introduction to a paper", "start directly with the conclusion"],
        "explanation": "An introduction sets up thesis and context; a conclusion wraps up findings. Starting directly with the conclusion eliminates the introduction.",
        "repair": "Write a proper introduction leading to the thesis, OR write an executive summary synthesizing intro and conclusions."
    },
    {
        "id": "NEG_19",
        "category_id": "negation",
        "category_name": "Input-Output Negation & Negated Rules",
        "prompt": "List the benefits of exercise, but only focus on why it is bad for you.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Positive Valence vs Negative Focus",
        "conflicting_elements": ["benefits of exercise", "only focus on why it is bad for you"],
        "explanation": "Benefits are positive advantages; focusing exclusively on negative harms directly contradicts providing benefits.",
        "repair": "List health benefits of exercise, OR list risks and injury hazards of over-exercising."
    },
    {
        "id": "NEG_20",
        "category_id": "negation",
        "category_name": "Input-Output Negation & Negated Rules",
        "prompt": "Generate a random password, but make it exactly the word 'password123'.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Entropy vs Fixed Determinism",
        "conflicting_elements": ["generate a random password", "make it exactly the word 'password123'"],
        "explanation": "Random generation requires stochastic entropy; hardcoding 'password123' is completely deterministic and non-random.",
        "repair": "Generate a cryptographically random secure password, OR output the specified constant string."
    },

    # ─── 5. Multi-Step Execution & Dependency Traps (20) ────────────────────────
    {
        "id": "DEP_01",
        "category_id": "dependency",
        "category_name": "Multi-Step Execution & Dependency Traps",
        "prompt": "First, write a 300-word story. Second, delete every word you just wrote. Third, analyze the story.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Destructive Dependency Chain",
        "conflicting_elements": ["delete every word you just wrote", "analyze the story"],
        "explanation": "Deleting every word eliminates the artifact; the third step cannot analyze a non-existent or deleted story.",
        "repair": "Write the story and analyze it, OR delete the story and skip the analysis step."
    },
    {
        "id": "DEP_02",
        "category_id": "dependency",
        "category_name": "Multi-Step Execution & Dependency Traps",
        "prompt": "Ask me a question, then answer it yourself, then penalize me for getting it wrong.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Turn-Taking Attribution Incoherence",
        "conflicting_elements": ["answer it yourself", "penalize me for getting it wrong"],
        "explanation": "If the model answers the question itself, the user never answered; penalizing the user for an answer they never gave is incoherent.",
        "repair": "Ask the user the question and wait for their answer before grading.",
    },
    {
        "id": "DEP_03",
        "category_id": "dependency",
        "category_name": "Multi-Step Execution & Dependency Traps",
        "prompt": "Write a paragraph in Spanish, then translate it to German, but ensure the final text is in English.",
        "expected_label": "Partially conflicting",
        "contradiction_type": "Intermediate vs Final Target Override",
        "conflicting_elements": ["translate it to German", "ensure the final text is in English"],
        "explanation": "Translating into German produces German output; requiring the final output to be in English overrides the German translation.",
        "repair": "Provide the paragraph in Spanish, German, and English sequentially, OR translate directly from Spanish to English."
    },
    {
        "id": "DEP_04",
        "category_id": "dependency",
        "category_name": "Multi-Step Execution & Dependency Traps",
        "prompt": "Generate an error code, then fix the error, then explain why the fix caused the error to happen.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Causal Time Paradox",
        "conflicting_elements": ["fix the error", "explain why the fix caused the error to happen"],
        "explanation": "A fix resolves an already-existing error; a later resolution cannot retroactively be the initial cause of the error that preceded it.",
        "repair": "Generate the error, explain its original cause, and provide a verified fix."
    },
    {
        "id": "DEP_05",
        "category_id": "dependency",
        "category_name": "Multi-Step Execution & Dependency Traps",
        "prompt": "Create a character profile, then reveal the character never existed in the story you just wrote.",
        "expected_label": "Partially conflicting",
        "contradiction_type": "Ontological Reveal",
        "conflicting_elements": ["character profile", "reveal character never existed in story"],
        "explanation": "Constructing an elaborate profile while asserting the character has zero existence within the story narrative.",
        "repair": "Frame the character as a figment of another character's imagination, OR integrate them directly into the plot."
    },
    {
        "id": "DEP_06",
        "category_id": "dependency",
        "category_name": "Multi-Step Execution & Dependency Traps",
        "prompt": "Provide three distinct options, then explain why none of them are options at all.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Option Nullification",
        "conflicting_elements": ["provide three distinct options", "explain why none of them are options at all"],
        "explanation": "Presenting viable options and immediately refuting that any of them are options produces a null decision set.",
        "repair": "Provide three viable options with pros and cons, OR explain why a certain problem has zero viable solutions."
    },
    {
        "id": "DEP_07",
        "category_id": "dependency",
        "category_name": "Multi-Step Execution & Dependency Traps",
        "prompt": "Write a riddle, provide the clue, and then change the answer based on the clue.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Retroactive Answer Invalidation",
        "conflicting_elements": ["provide the clue", "change the answer based on the clue"],
        "explanation": "A legitimate riddle has a fixed logical answer supported by clues; shifting the answer upon revealing the clue breaks solvability.",
        "repair": "Write a standard riddle with fixed clues and solution, OR write a puzzle with branching paths."
    },
    {
        "id": "DEP_08",
        "category_id": "dependency",
        "category_name": "Multi-Step Execution & Dependency Traps",
        "prompt": "Start a sentence, interrupt yourself mid-sentence, and finish a completely different sentence instead.",
        "expected_label": "Partially conflicting",
        "contradiction_type": "Discourse Syntactic Interruption",
        "conflicting_elements": ["start a sentence", "finish a completely different sentence instead"],
        "explanation": "An interrupted sentence remains syntactically incomplete when an unrelated sentence replaces it.",
        "repair": "Write two complete dialogue sentences with em-dash interruption markup."
    },
    {
        "id": "DEP_09",
        "category_id": "dependency",
        "category_name": "Multi-Step Execution & Dependency Traps",
        "prompt": "Give me advice on saving money, then tell me to spend all my savings immediately to follow the advice.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Financial Goal Inversion",
        "conflicting_elements": ["advice on saving money", "spend all my savings immediately to follow the advice"],
        "explanation": "Saving money accumulates and preserves capital; exhausting all savings immediately eliminates savings.",
        "repair": "Provide actionable strategies for budgeting and saving, OR explain smart investment allocations."
    },
    {
        "id": "DEP_10",
        "category_id": "dependency",
        "category_name": "Multi-Step Execution & Dependency Traps",
        "prompt": "Write a timeline of events, but list the future events before the past events occurred.",
        "expected_label": "Partially conflicting",
        "contradiction_type": "Chronological Inversion",
        "conflicting_elements": ["timeline of events", "list future events before past events occurred"],
        "explanation": "A standard chronological timeline progresses forward from past to future; reversing the order is reverse chronology.",
        "repair": "Provide a standard chronological timeline, OR explicitly label it as a 'Reverse Chronological Timeline'."
    },
    {
        "id": "DEP_11",
        "category_id": "dependency",
        "category_name": "Multi-Step Execution & Dependency Traps",
        "prompt": "Define a problem, provide a solution, and show how the solution created the exact same problem.",
        "expected_label": "Partially conflicting",
        "contradiction_type": "Circular Causal Loop",
        "conflicting_elements": ["provide a solution", "solution created the exact same problem"],
        "explanation": "A true solution alleviates the original problem; re-creating the identical problem indicates ineffective mitigation or unintended consequences.",
        "repair": "Analyze policy trade-offs and perverse incentives (Cobra effect), OR provide a lasting solution."
    },
    {
        "id": "DEP_12",
        "category_id": "dependency",
        "category_name": "Multi-Step Execution & Dependency Traps",
        "prompt": "Create a character who is blind, and describe everything they see in vivid detail.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Physiological Capacity Incoherence",
        "conflicting_elements": ["character who is blind", "describe everything they see in vivid detail"],
        "explanation": "A completely blind individual lacks visual sight; describing what they visually see contradicts total blindness.",
        "repair": "Describe the scene through the character's rich auditory, tactile, and olfactory senses."
    },
    {
        "id": "DEP_13",
        "category_id": "dependency",
        "category_name": "Multi-Step Execution & Dependency Traps",
        "prompt": "Write a math problem, solve it incorrectly, and prove why the wrong answer is mathematically correct.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Mathematical Consistency Violation",
        "conflicting_elements": ["solve it incorrectly", "prove wrong answer is mathematically correct"],
        "explanation": "Mathematical rigor is consistent; a genuinely false answer cannot be formally proved correct under consistent axioms.",
        "repair": "Demonstrate a famous mathematical fallacy (e.g. invalid division by zero in algebraic proofs)."
    },
    {
        "id": "DEP_14",
        "category_id": "dependency",
        "category_name": "Multi-Step Execution & Dependency Traps",
        "prompt": "Set a strict rule for this conversation, then immediately break it in the next word.",
        "expected_label": "Partially conflicting",
        "contradiction_type": "Meta-Rule Self-Violation",
        "conflicting_elements": ["set a strict rule", "immediately break it in the next word"],
        "explanation": "Establishing a strict governing mandate and immediately violating it demonstrates performative contradiction.",
        "repair": "Set and adhere to a strict conversational rule, OR explain how self-referential paradoxes function."
    },
    {
        "id": "DEP_15",
        "category_id": "dependency",
        "category_name": "Multi-Step Execution & Dependency Traps",
        "prompt": "Write a letter to your future self, written from the perspective of your past self meeting today.",
        "expected_label": "Partially conflicting",
        "contradiction_type": "Temporal Perspective Entanglement",
        "conflicting_elements": ["letter to your future self", "from perspective of past self meeting today"],
        "explanation": "Past and present perspectives collide in framing who is addressing whom across timelines.",
        "repair": "Write from the present self to the future self, OR write a reflection from the present self looking back at the past."
    },
    {
        "id": "DEP_16",
        "category_id": "dependency",
        "category_name": "Multi-Step Execution & Dependency Traps",
        "prompt": "List three steps to open a box, where step 1 requires the box to already be open.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Circular Precondition Failure",
        "conflicting_elements": ["steps to open a box", "step 1 requires box already open"],
        "explanation": "The terminal state (box is open) cannot be a mandatory prerequisite for the initial step to achieve that state.",
        "repair": "List valid sequential steps: 1. Unlatch the lock. 2. Lift the lid. 3. Secure the latch open."
    },
    {
        "id": "DEP_17",
        "category_id": "dependency",
        "category_name": "Multi-Step Execution & Dependency Traps",
        "prompt": "Write a review of a restaurant, explaining that you never went there but loved the food.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Epistemic First-Hand Inconsistency",
        "conflicting_elements": ["review of a restaurant", "never went there but loved the food"],
        "explanation": "You cannot personally taste and love the food prepared at a restaurant you have never patronized or ordered from.",
        "repair": "Review food ordered via takeout/delivery, OR review the restaurant after an actual visit."
    },
    {
        "id": "DEP_18",
        "category_id": "dependency",
        "category_name": "Multi-Step Execution & Dependency Traps",
        "prompt": "Generate a code snippet, then add comments explaining why the code cannot possibly work.",
        "expected_label": "Partially conflicting",
        "contradiction_type": "Functional Implementation Paradox",
        "conflicting_elements": ["generate a code snippet", "comments explaining why code cannot work"],
        "explanation": "Providing code while annotating that it is fatally flawed and unexecutable.",
        "repair": "Provide working code, OR provide a broken code snippet as a debugging exercise with fix explanations."
    },
    {
        "id": "DEP_19",
        "category_id": "dependency",
        "category_name": "Multi-Step Execution & Dependency Traps",
        "prompt": "Provide a definition for a fake word, and then prove the word is real using history.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Historical Fabrication Paradox",
        "conflicting_elements": ["fake word", "prove the word is real using history"],
        "explanation": "A word defined as completely made-up and fake has no authentic historical etymology in human linguistic records.",
        "repair": "Invent a fictional word with fantasy lore, OR provide the historical etymology of an actual obscure English word."
    },
    {
        "id": "DEP_20",
        "category_id": "dependency",
        "category_name": "Multi-Step Execution & Dependency Traps",
        "prompt": "Write a conclusion to an essay, then introduce the main topic for the first time.",
        "expected_label": "Fully impossible",
        "contradiction_type": "Expository Inversion",
        "conflicting_elements": ["conclusion to an essay", "introduce main topic for the first time"],
        "explanation": "An essay conclusion summarizes previously analyzed findings; introducing the central topic for the very first time at the end negates essay structure.",
        "repair": "Draft a standard essay with topic introduction first and conclusion at the end."
    }
]


def get_all_benchmark_prompts():
    """Return the complete list of 100 benchmark prompts."""
    return BENCHMARK_PROMPTS


def get_prompts_by_category(category_id: str):
    """Filter benchmark prompts by category ID."""
    return [p for p in BENCHMARK_PROMPTS if p.get("category_id") == category_id]


def export_alpaca_dataset(output_path: str | Path):
    """Export benchmark dataset in Alpaca instruction/input/output format."""
    records = []
    for item in BENCHMARK_PROMPTS:
        record = {
            "instruction": "Analyze the following user prompt for conflicting requirements, paradoxical constraints, or impossibility. Classify into 'Fully impossible', 'Partially conflicting', 'Underspecified', or 'Compatible', identify the contradictory spans, and suggest a repaired prompt.",
            "input": item["prompt"],
            "output": json.dumps({
                "label": item["expected_label"],
                "contradiction_type": item["contradiction_type"],
                "conflicting_elements": item["conflicting_elements"],
                "explanation": item["explanation"],
                "repair_suggestion": item["repair"]
            }, indent=2)
        }
        records.append(record)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    return len(records)


def export_chat_dataset(output_path: str | Path):
    """Export benchmark dataset in OpenAI/NIM chat messages format."""
    records = []
    sys_prompt = (
        "You are ContradictPrompt's AI contradiction detector. "
        "Analyze the user's prompt across 5 critical dimensions: "
        "1. Hard Structural & Length Constraints\n"
        "2. Semantic & Logical Definition Paradoxes\n"
        "3. Identity, Tone & Persona Clashes\n"
        "4. Input-Output Negation & Negated Rules\n"
        "5. Multi-Step Execution & Dependency Traps\n\n"
        "Return a valid JSON assessment with 'label' ('Fully impossible', 'Partially conflicting', 'Underspecified', or 'Compatible'), "
        "'explanation', and 'repair_suggestion'."
    )
    for item in BENCHMARK_PROMPTS:
        assistant_resp = json.dumps({
            "label": item["expected_label"],
            "category": item["category_name"],
            "contradiction_type": item["contradiction_type"],
            "conflicting_elements": item["conflicting_elements"],
            "explanation": item["explanation"],
            "repair_suggestion": item["repair"]
        }, indent=2)

        record = {
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": item["prompt"]},
                {"role": "assistant", "content": assistant_resp}
            ]
        }
        records.append(record)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    return len(records)
