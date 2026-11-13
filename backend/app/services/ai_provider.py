import hashlib
import json
import math
import re
from typing import Any, Dict, List
import httpx

from app.config import settings

# Domain vocabulary clusters to ensure high semantic recall in deterministic mock mode
LEGAL_CONCEPT_CLUSTERS = [
    ["heat", "heating", "cold", "temperature", "radiator", "winter", "boiler", "68", "62", "fahrenheit", "27-2029"],
    ["hot", "water", "shower", "bath", "sink", "120", "plumbing", "supply", "27-2031", "pipes"],
    ["leak", "leaks", "mold", "dampness", "roof", "seepage", "moisture", "waterproofing", "mildew", "27-2017"],
    ["habitability", "untenantable", "unsafe", "hazardous", "dangerous", "health", "safety", "235-b", "1941"],
    ["repair", "repairs", "deduct", "neglect", "notice", "reasonable", "dilapidations", "1942", "section 44"],
    ["essential", "withhold", "cut", "electricity", "utility", "shutoff", "lockout", "section 49", "sewage"],
]


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9\-\§]+", text.lower())


def compute_deterministic_embedding(text: str, dim: int = 64) -> List[float]:
    tokens = _tokenize(text)
    vec = [0.0] * dim
    if not tokens:
        return vec

    # First 12 dimensions encode domain concept cluster activations
    for cluster_idx, cluster_words in enumerate(LEGAL_CONCEPT_CLUSTERS):
        hits = sum(1 for t in tokens if any(cw in t for cw in cluster_words))
        if hits > 0:
            vec[cluster_idx * 2] += float(hits) * 2.5
            vec[cluster_idx * 2 + 1] += math.log1p(hits) * 2.0

    # Remaining dimensions encode hashed token n-grams
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        bucket = 12 + (digest[0] % (dim - 12))
        sign = 1.0 if (digest[1] % 2 == 0) else -1.0
        vec[bucket] += sign * 1.0

    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [round(v / norm, 6) for v in vec]
    return vec


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(dot / (norm_a * norm_b))


class AIProvider:
    def get_embedding(self, text: str) -> List[float]:
        if settings.AI_PROVIDER == "openai_compatible" and settings.OPENAI_API_KEY:
            try:
                with httpx.Client(timeout=15.0) as client:
                    resp = client.post(
                        f"{settings.OPENAI_API_BASE.rstrip('/')}/embeddings",
                        headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                        json={"model": settings.EMBEDDING_MODEL, "input": text},
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    return data["data"][0]["embedding"]
            except Exception:
                # Fallback to deterministic embedding if remote API fails
                return compute_deterministic_embedding(text)
        return compute_deterministic_embedding(text)

    def generate_grounded_analysis(
        self,
        complaint_description: str,
        jurisdiction: str,
        prior_notice_given: bool,
        issue_start_date: str,
        retrieved_chunks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Synthesizes a structured legal information response strictly grounded in `retrieved_chunks`.
        Returns a dictionary containing summary_explanation, key_rights, missing_evidence,
        limitations_and_warnings, recommended_next_steps, and cited_chunk_ids.
        """
        if settings.AI_PROVIDER == "openai_compatible" and settings.OPENAI_API_KEY:
            try:
                return self._call_openai_compatible_llm(
                    complaint_description,
                    jurisdiction,
                    prior_notice_given,
                    issue_start_date,
                    retrieved_chunks,
                )
            except Exception:
                pass

        return self._generate_deterministic_synthesis(
            complaint_description,
            jurisdiction,
            prior_notice_given,
            issue_start_date,
            retrieved_chunks,
        )

    def _generate_deterministic_synthesis(
        self,
        complaint_description: str,
        jurisdiction: str,
        prior_notice_given: bool,
        issue_start_date: str,
        retrieved_chunks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        cited_ids = [c["chunk_id"] for c in retrieved_chunks]
        citation_labels = [
            f"{c['citation_label']} ({c['heading']})" for c in retrieved_chunks
        ]

        summary_parts = [
            f"Based on the retrieved housing regulations for {jurisdiction}, your reported issue aligns with statutory landlord maintenance obligations under {', '.join(citation_labels[:3])}."
        ]
        key_rights: List[str] = []
        for chunk in retrieved_chunks:
            status_tag = (
                f"[NOTE: Historical/Superseded by {chunk['superseded_by']}] "
                if not chunk["is_active"]
                else ""
            )
            key_rights.append(
                f"{status_tag}{chunk['citation_label']} — {chunk['heading']}: {chunk['excerpt'][:220]}..."
            )

        missing_evidence: List[str] = []
        if not prior_notice_given:
            missing_evidence.append(
                "Written notice to the landlord or property manager has not yet been documented. Most statutes require written notice and a reasonable opportunity to repair."
            )
        if not issue_start_date:
            missing_evidence.append(
                "Exact start date of the condition is not specified. Documenting dates and duration strengthens repair requests."
            )
        if "photo" not in complaint_description.lower() and "temperature" not in complaint_description.lower():
            missing_evidence.append(
                "Dated photographs, videos, or indoor temperature logs corroborating the condition."
            )

        limitations = [
            "This analysis provides general legal information grounded solely in the retrieved statutory excerpts below and does not constitute formal legal advice or representation.",
            f"Statutory remedies depend on local administrative enforcement and lease terms in {jurisdiction}.",
        ]

        next_steps = [
            "Send a dated, written complaint letter to the landlord citing the specific statutory sections listed below and keep a copy for your records.",
            "Document the condition daily with time-stamped photographs, indoor thermometer readings (if heat/hot water related), and a log of all landlord communications.",
            "If the condition poses an immediate threat to health or safety and the landlord fails to respond, contact your municipal housing code enforcement agency or a local legal aid clinic.",
        ]

        return {
            "summary_explanation": " ".join(summary_parts),
            "key_rights": key_rights,
            "missing_evidence": missing_evidence,
            "limitations_and_warnings": limitations,
            "recommended_next_steps": next_steps,
            "cited_chunk_ids": cited_ids,
        }

    def _call_openai_compatible_llm(
        self,
        complaint_description: str,
        jurisdiction: str,
        prior_notice_given: bool,
        issue_start_date: str,
        retrieved_chunks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        sources_block = json.dumps(
            [
                {
                    "chunk_id": c["chunk_id"],
                    "citation_label": c["citation_label"],
                    "heading": c["heading"],
                    "is_active": c["is_active"],
                    "superseded_by": c["superseded_by"],
                    "excerpt": c["excerpt"],
                }
                for c in retrieved_chunks
            ],
            indent=2,
        )
        system_prompt = (
            "You are TenantGuard, a strict evidence-grounded housing law research assistant. "
            "You provide legal information, NOT legal advice. "
            "Use ONLY the provided retrieved statutory chunks. Never invent laws or citations. "
            "Respond strictly in valid JSON with keys: summary_explanation (string), "
            "key_rights (array of strings), missing_evidence (array of strings), "
            "limitations_and_warnings (array of strings), recommended_next_steps (array of strings), "
            "and cited_chunk_ids (array of integer chunk_ids actually used)."
        )
        user_prompt = (
            f"Jurisdiction: {jurisdiction}\n"
            f"Prior Notice Given: {prior_notice_given}\n"
            f"Issue Start Date: {issue_start_date or 'Unspecified'}\n"
            f"Tenant Problem: {complaint_description}\n\n"
            f"Retrieved Sources:\n{sources_block}"
        )
        with httpx.Client(timeout=25.0) as client:
            resp = client.post(
                f"{settings.OPENAI_API_BASE.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={
                    "model": settings.LLM_MODEL,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.1,
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return json.loads(content)


ai_provider = AIProvider()
