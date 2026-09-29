import logging
from typing import Optional, List, Tuple
import httpx
from app.config import HINDSIGHT_URL, HINDSIGHT_API_KEY, BANK_ID
from app.models import RecalledMemoryItem, IncidentInput
from app.relevance import rank_and_filter_memories

logger = logging.getLogger(__name__)

class HindsightService:
    """
    Service wrapper for Hindsight Agent Memory (https://github.com/vectorize-io/hindsight).
    Interacts with the Hindsight server bank_id='oncall-memory' via standard HTTP API
    to ensure full async/sync safety without event loop conflicts.
    """
    def __init__(self, base_url: str = HINDSIGHT_URL, api_key: Optional[str] = HINDSIGHT_API_KEY, bank_id: str = BANK_ID):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.bank_id = bank_id

    def _get_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def is_available(self) -> bool:
        """Quick check to see if Hindsight service is reachable."""
        try:
            resp = httpx.get(f"{self.base_url}/health", headers=self._get_headers(), timeout=2.5)
            if resp.status_code < 500:
                return True
        except Exception:
            pass

        try:
            resp = httpx.get(f"{self.base_url}/v1/version", headers=self._get_headers(), timeout=2.5)
            if resp.status_code < 500:
                return True
        except Exception:
            pass
        return False

    def clear_bank(self) -> bool:
        """Deletes the memory bank on Hindsight to clear all retained memories."""
        endpoint = f"{self.base_url}/v1/default/banks/{self.bank_id}"
        try:
            resp = httpx.delete(endpoint, headers=self._get_headers(), timeout=10.0)
            return resp.status_code < 400
        except Exception as e:
            logger.warning(f"Failed to delete bank '{self.bank_id}': {e}")
            return False

    def recall(self, query: str, incident: Optional[IncidentInput] = None) -> Tuple[List[RecalledMemoryItem], bool, Optional[str]]:
        """
        Recall similar past incidents for the given query from Hindsight bank_id="oncall-memory".
        Applies service-aware relevance ranking and filtering when incident is provided.
        Returns: (memories, is_available, status_message)
        """
        endpoint = f"{self.base_url}/v1/default/banks/{self.bank_id}/memories/recall"
        payload = {
            "query": query,
            "max_tokens": 4096,
            "budget": "mid"
        }

        try:
            logger.info(f"Calling Hindsight recall(bank_id='{self.bank_id}', endpoint='{endpoint}')")
            resp = httpx.post(endpoint, json=payload, headers=self._get_headers(), timeout=25.0)
            if resp.status_code >= 400:
                logger.warning(f"Hindsight recall returned HTTP {resp.status_code}: {resp.text}")
                return [], False, f"Hindsight memory error ({resp.status_code})"

            data = resp.json()
            raw_results = data.get("results", [])

            memories: List[RecalledMemoryItem] = []
            for item in raw_results:
                text = item.get("text", "").strip()
                if not text:
                    continue
                # Filter out synthetic consolidation prompts
                if text.startswith("Extract facts from the following chunk") or text.startswith("Event Date:"):
                    continue

                scores = item.get("scores") or {}
                if isinstance(scores, dict):
                    # Hindsight v0.10 returns 'final', 'reranker', 'semantic', 'keyword', or 'fused'
                    raw_score = scores.get("final") or scores.get("reranker") or scores.get("semantic") or scores.get("fused") or 0.0
                else:
                    raw_score = 0.0

                memories.append(
                    RecalledMemoryItem(
                        id=item.get("id"),
                        text=text,
                        type=item.get("type", "experience"),
                        score=float(raw_score),
                        entities=item.get("entities"),
                        metadata=item.get("metadata"),
                        relevance_reason=item.get("context")
                    )
                )

            # If incident context is provided, apply intelligent relevance ranking and filtering
            if incident is not None:
                filtered_mems = rank_and_filter_memories(memories, incident)
                logger.info(
                    f"Hindsight recall returned {len(memories)} raw memories, filtered to {len(filtered_mems)} "
                    f"relevant memories for service '{incident.service}'"
                )
                return filtered_mems, True, None

            # Fallback when incident is not provided: prioritize structured incident memories
            incident_mems = [m for m in memories if "INCIDENT:" in m.text]
            other_mems = [m for m in memories if "INCIDENT:" not in m.text]
            combined = (incident_mems + other_mems)[:5]

            logger.info(f"Hindsight recall returned {len(combined)} memories ({len(incident_mems)} structured incidents)")
            return combined, True, None

        except Exception as e:
            logger.warning(f"Hindsight recall failed: {e}")
            msg = "Hindsight memory temporarily unavailable, continuing without historical context"
            return [], False, msg

    def retain(self, content: str) -> Tuple[bool, Optional[str]]:
        """
        Retain structured incident outcome in Hindsight bank_id="oncall-memory".
        Returns: (success, error_or_success_message)
        """
        # Requirement: Don't retain trivial content (UI clicks, greetings).
        # Only retain real incident summaries with root cause + fix + outcome.
        if "ROOT CAUSE:" not in content or "FIX (" not in content:
            return False, "Refused to retain: memory must contain structured ROOT CAUSE and FIX outcome"

        endpoint = f"{self.base_url}/v1/default/banks/{self.bank_id}/memories"
        payload = {
            "items": [
                {
                    "content": content
                }
            ],
            "var_async": False
        }

        try:
            logger.info(f"Calling Hindsight retain(bank_id='{self.bank_id}', content='{content}')")
            resp = httpx.post(endpoint, json=payload, headers=self._get_headers(), timeout=25.0)
            if resp.status_code >= 400:
                logger.error(f"Hindsight retain HTTP {resp.status_code}: {resp.text}")
                return False, f"Hindsight retain failed: {resp.text}"

            return True, f"Retained experience in '{self.bank_id}' successfully"

        except Exception as e:
            logger.error(f"Hindsight retain failed: {e}")
            return False, f"Hindsight memory temporarily unavailable, could not retain: {str(e)}"

    def reflect(self, query: str) -> Tuple[Optional[str], List[dict], bool, Optional[str]]:
        """
        Calls Hindsight's native reflect API: POST /v1/default/banks/{bank_id}/reflect
        Synthesizes bank identity, world facts, and observations/experiences to form a reflection.
        Returns: (reflection_text, based_on_memories, is_available, status_message)
        """
        endpoint = f"{self.base_url}/v1/default/banks/{self.bank_id}/reflect"
        payload = {
            "query": query,
            "budget": "mid",
            "include": {
                "facts": {}
            }
        }

        try:
            logger.info(f"Calling Hindsight reflect(bank_id='{self.bank_id}', endpoint='{endpoint}')")
            resp = httpx.post(endpoint, json=payload, headers=self._get_headers(), timeout=30.0)
            if resp.status_code >= 400:
                logger.warning(f"Hindsight reflect returned HTTP {resp.status_code}: {resp.text}")
                return None, [], False, f"Hindsight reflect error ({resp.status_code})"

            data = resp.json()
            reflection_text = data.get("text", "")
            based_on = data.get("based_on") or {}
            raw_memories = based_on.get("memories") or []

            clean_memories = []
            for m in raw_memories:
                m_text = m.get("text", "").strip()
                if m_text.startswith("Extract facts from") or m_text.startswith("Event Date:"):
                    continue
                clean_memories.append({
                    "id": m.get("id"),
                    "text": m_text,
                    "type": m.get("type", "observation")
                })

            logger.info(f"Hindsight reflect returned {len(clean_memories)} based_on memories")
            return reflection_text, clean_memories, True, None

        except Exception as e:
            logger.warning(f"Hindsight reflect failed: {e}")
            return None, [], False, f"Hindsight memory temporarily unavailable: {str(e)}"


# Singleton service instance
hindsight_service = HindsightService()
