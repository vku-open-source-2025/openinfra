"""Best-effort retrieval of AG05 vector corpus context via SOSConn llm-service."""

import json
import logging
import re
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class AG05ContextService:
    """Retrieve short ranked snippets from AG05 corpus for prompt enrichment."""

    CHAT_ENDPOINT = "/api/v1/chat/ask-latest-chatbot"

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
    ):
        configured_url = base_url if base_url is not None else settings.SOSCONN_LLM_BASE_URL
        self.base_url = (configured_url or "").rstrip("/")
        if timeout_seconds is None:
            timeout_seconds = settings.SOSCONN_LLM_TIMEOUT_SECONDS
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _extract_first_json_payload(raw_text: str) -> Optional[Any]:
        """Extract first JSON object/array from model output text."""
        if not raw_text:
            return None

        raw_text = raw_text.strip()
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            pass

        object_match = re.search(r"\{[\s\S]*\}", raw_text)
        if object_match:
            try:
                return json.loads(object_match.group(0))
            except json.JSONDecodeError:
                pass

        array_match = re.search(r"\[[\s\S]*\]", raw_text)
        if array_match:
            try:
                return json.loads(array_match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    @staticmethod
    def _extract_answer_text(payload: Any) -> str:
        """Unify llm-service response content to a single answer text."""
        if isinstance(payload, str):
            return payload

        if isinstance(payload, dict):
            answer = payload.get("answer")
            if isinstance(answer, str):
                return answer
            if isinstance(payload.get("content"), str):
                return payload["content"]
            return json.dumps(payload, ensure_ascii=False)

        return str(payload)

    @staticmethod
    def _build_retrieval_prompt(query: str, max_snippets: int) -> str:
        """Build strict prompt asking for structured retrieval snippets only."""
        return (
            "Return only JSON. Use AG05 vector corpus as the only source. "
            "Find the top relevant snippets for the question below and respond with this exact schema: "
            '{"snippets":[{"source_id":"AG05-1","text":"..."}]}. '
            f"Include at most {max_snippets} snippets. "
            "source_id must be unique per snippet. "
            "If nothing relevant is found, return {\"snippets\":[]}. "
            f"Question: {query}"
        )

    @staticmethod
    def _normalize_snippets(raw_payload: Any, max_snippets: int) -> List[Dict[str, str]]:
        """Normalize arbitrary JSON payloads into a fixed snippet list shape."""
        candidates: List[Any] = []

        if isinstance(raw_payload, dict):
            if isinstance(raw_payload.get("snippets"), list):
                candidates = raw_payload.get("snippets", [])
            elif isinstance(raw_payload.get("sources"), list):
                candidates = raw_payload.get("sources", [])
        elif isinstance(raw_payload, list):
            candidates = raw_payload

        normalized: List[Dict[str, str]] = []
        for idx, item in enumerate(candidates, start=1):
            if len(normalized) >= max_snippets:
                break

            if isinstance(item, dict):
                source_id = str(item.get("source_id") or item.get("id") or f"AG05-{idx}").strip()
                text = str(
                    item.get("text")
                    or item.get("snippet")
                    or item.get("content")
                    or item.get("quote")
                    or ""
                ).strip()
            else:
                source_id = f"AG05-{idx}"
                text = str(item).strip()

            if not text:
                continue

            normalized.append(
                {
                    "source_id": source_id or f"AG05-{idx}",
                    "text": text[:500],
                }
            )

        return normalized

    async def retrieve_snippets(
        self,
        query: str,
        max_snippets: int = 3,
    ) -> List[Dict[str, str]]:
        """Retrieve best-effort AG05 snippets; never raises upstream errors."""
        if not self.base_url:
            return []

        query = (query or "").strip()
        if not query:
            return []

        url = f"{self.base_url}{self.CHAT_ENDPOINT}"
        payload = {"question": self._build_retrieval_prompt(query, max_snippets=max_snippets)}

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                body = response.json() if response.content else {}
        except Exception as exc:
            logger.warning("AG05 retrieval unavailable (%s): %s", url, exc)
            return []

        answer_text = self._extract_answer_text(body)
        parsed = self._extract_first_json_payload(answer_text)
        snippets = self._normalize_snippets(parsed, max_snippets=max_snippets)
        if snippets:
            return snippets

        # Last-resort fallback when answer is plain text but still potentially relevant.
        lowered = answer_text.lower()
        if answer_text.strip() and "khong co du du lieu" not in lowered and "không có đủ dữ liệu" not in lowered:
            return [{"source_id": "AG05-1", "text": answer_text.strip()[:500]}]

        return []

    @staticmethod
    def format_snippets(snippets: List[Dict[str, str]]) -> str:
        """Render snippets into prompt-friendly lines with source IDs."""
        lines = []
        for snippet in snippets:
            source_id = str(snippet.get("source_id") or "AG05").strip()
            text = str(snippet.get("text") or "").strip()
            if text:
                lines.append(f"[{source_id}] {text}")
        return "\n".join(lines)
