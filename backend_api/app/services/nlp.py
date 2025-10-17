import re
from typing import Dict


# PUBLIC_INTERFACE
def score_answer(answer: str, expected_keywords: str = "") -> Dict:
    """Compute heuristic scores for an interview answer.
    Returns component scores, overall score, and suggestions.
    """
    text = (answer or "").strip()
    words = len(re.findall(r"\w+", text))
    sentences = max(1, len(re.findall(r"[.!?]", text)))
    avg_len = words / sentences if sentences else words

    # Communication: penalize very short or overly long sentences
    communication = 50
    if 10 <= avg_len <= 25:
        communication += 35
    elif 6 <= avg_len < 10 or 25 < avg_len <= 35:
        communication += 20
    else:
        communication += 10

    # Correctness: keyword presence
    kw_list = [k.strip().lower() for k in (expected_keywords or "").split(",") if k.strip()]
    found = 0
    for k in kw_list:
        if re.search(r"\b" + re.escape(k) + r"\b", text.lower()):
            found += 1
    correctness = 50 + int(50 * (found / max(1, len(kw_list)))) if kw_list else 60

    # Completeness: length and structure
    completeness = 40
    if words >= 80:
        completeness += 40
    elif words >= 40:
        completeness += 30
    elif words >= 20:
        completeness += 20
    else:
        completeness += 10

    overall = int(0.35 * communication + 0.35 * correctness + 0.30 * completeness)

    suggestions = []
    if avg_len < 10:
        suggestions.append("Provide more detailed explanations with examples.")
    if found < len(kw_list):
        suggestions.append("Incorporate key technical terms and concepts relevant to the question.")
    if words < 40:
        suggestions.append("Expand your answer to cover reasoning, steps, and edge cases.")
    if not suggestions:
        suggestions.append("Great structure and coverage. Consider highlighting trade-offs and time/space complexity if applicable.")

    return {
        "communication": min(100, communication),
        "correctness": min(100, correctness),
        "completeness": min(100, completeness),
        "overall": min(100, overall),
        "suggestions": suggestions,
    }
