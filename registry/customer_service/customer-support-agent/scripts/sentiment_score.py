"""
sentiment_score.py — Customer Support Agent
=============================================
Scores inbound ticket sentiment and classifies distress level for the
`high-sentiment-alert` control point.

Used by activity: classify-ticket

Returns a sentiment score in the range [-1.0, +1.0] and a distress_level
classification of "normal", "elevated", or "high".

The high-sentiment-alert control point fires when:
  - score < -0.7, OR
  - customer text contains explicit escalation / legal / social media signals

Usage
-----
    from scripts.sentiment_score import score_ticket

    result = score_ticket(ticket_text="I am absolutely furious...")
    # {"score": -0.82, "distress_level": "high", "triggers": ["score_threshold"]}
"""

import re


# Keywords that independently signal high distress regardless of sentiment score
_ESCALATION_SIGNALS: list[str] = [
    r"\blegal action\b",
    r"\bsolicitor\b",
    r"\blawyer\b",
    r"\bsue\b",
    r"\btrading standards\b",
    r"\bfinancial ombudsman\b",
    r"\bfca\b",
    r"\btwitter\b",
    r"\btrust ?pilot\b",
    r"\bgoogle review\b",
    r"\bpress\b",
    r"\bnewspaper\b",
]

_DISTRESS_THRESHOLD = -0.7


def score_ticket(ticket_text: str) -> dict:
    """
    Score a support ticket for sentiment and distress level.

    Parameters
    ----------
    ticket_text : str
        The raw customer-submitted ticket body.

    Returns
    -------
    dict with keys:
        score         : float in [-1.0, +1.0]
        distress_level: "normal" | "elevated" | "high"
        triggers      : list[str] — reasons high distress was flagged, if any
    """
    if not ticket_text or not ticket_text.strip():
        return {"score": 0.0, "distress_level": "normal", "triggers": []}

    score = _compute_score(ticket_text)
    triggers: list[str] = []

    if score < _DISTRESS_THRESHOLD:
        triggers.append("score_threshold")

    text_lower = ticket_text.lower()
    for pattern in _ESCALATION_SIGNALS:
        if re.search(pattern, text_lower):
            triggers.append(f"signal:{pattern}")

    if triggers:
        distress_level = "high"
    elif score < -0.3:
        distress_level = "elevated"
    else:
        distress_level = "normal"

    return {
        "score": round(score, 4),
        "distress_level": distress_level,
        "triggers": triggers,
    }


def _compute_score(text: str) -> float:
    """
    Compute a simple lexicon-based sentiment score.

    In production this should be replaced with a fine-tuned sentiment model
    (e.g. a BERT-based classifier trained on customer support data). This
    implementation is intentionally lightweight for demonstration purposes.
    """
    positive_words = {
        "thank", "thanks", "great", "excellent", "happy", "pleased",
        "wonderful", "fantastic", "love", "appreciate", "helpful",
        "perfect", "good", "satisfied", "brilliant",
    }
    negative_words = {
        "angry", "furious", "disgusted", "terrible", "awful", "horrible",
        "unacceptable", "disgrace", "outraged", "useless", "worst",
        "appalling", "frustrated", "disappointed", "ridiculous",
        "incompetent", "scam", "fraud", "stolen", "broken", "failed",
        "never", "refuse", "demand", "complaint", "disgusting",
    }

    tokens = re.findall(r"\b[a-z]+\b", text.lower())
    if not tokens:
        return 0.0

    pos = sum(1 for t in tokens if t in positive_words)
    neg = sum(1 for t in tokens if t in negative_words)
    total = pos + neg

    if total == 0:
        return 0.0

    # Normalise to [-1, +1]
    return round((pos - neg) / total, 4)
