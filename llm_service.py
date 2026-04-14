import json
import time

import requests

from models import AnalysisRunResult, EmailAnalysis


def normalize_label(raw_label, allowed_labels):
    if not isinstance(raw_label, str):
        return "Uncategorized"

    stripped = raw_label.strip()
    for allowed_label in allowed_labels:
        if stripped.lower() == allowed_label.lower():
            return allowed_label

    return "Uncategorized"


def parse_ollama_json(raw_response):
    ai_text = raw_response.strip()
    if ai_text.startswith("```json"):
        ai_text = ai_text[7:]
    if ai_text.endswith("```"):
        ai_text = ai_text[:-3]
    return json.loads(ai_text.strip())


def build_prompt(subject, body, category_labels):
    allowed_labels_text = ", ".join(f"'{label}'" for label in category_labels)
    return f"""
        Analyze the following email.
        Subject: {subject}
        Body: {body}
        
        Return ONLY a STRICT JSON object with EXACTLY these keys:
        - "important": boolean (true ONLY IF it requires direct human action like bills, personal coordination, account/security action. MUST be false for marketing, discounts, newsletters, or promotions.)
        - "label": string (choose exactly one label from: {allowed_labels_text})
        - "summary": string (very brief one-sentence summary)
        - "tracking_number": string or null (extract package tracking number if present)
        - "courier": string or null (FedEx, UPS, DHL, USPS, Israel Post, etc. if tracking exists)
        
        Shipping detection instruction:
        - Treat shipment updates as package-related even when the email is not in English.
        - If shipping context words appear (for example: משלוח, tracking, pickup, courier, shipping, package, delivery, נקודת איסוף, דואר),
          actively search for a tracking number in subject/body and return it when present.
        - If shipping context exists but courier is unclear, keep "courier" as null.
        - Only return null for "tracking_number" if no plausible tracking identifier appears in the content.
        """


def analyze_email(ollama_url, ollama_model, subject, body, category_labels):
    payload = {
        "model": ollama_model,
        "prompt": build_prompt(subject, body, category_labels),
        "stream": False,
        "format": "json",
    }

    start_time = time.time()
    ollama_http = requests.post(ollama_url, json=payload, timeout=300)
    ollama_http.raise_for_status()
    ollama_res = ollama_http.json()
    elapsed_time = time.time() - start_time

    parsed = parse_ollama_json(ollama_res["response"])
    summary = str(parsed.get("summary", "")).strip() or "No summary returned."
    tracking_number = parsed.get("tracking_number")
    courier = parsed.get("courier")

    if tracking_number is not None:
        tracking_number = str(tracking_number).strip() or None
    if courier is not None:
        courier = str(courier).strip() or None

    analysis = EmailAnalysis(
        important=bool(parsed.get("important")),
        label=normalize_label(parsed.get("label"), category_labels),
        summary=summary,
        tracking_number=tracking_number,
        courier=courier,
    )

    return AnalysisRunResult(analysis=analysis, elapsed_seconds=elapsed_time)
