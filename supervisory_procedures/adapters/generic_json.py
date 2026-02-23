"""Platform-agnostic JSON export adapter."""

from __future__ import annotations

import json
from typing import Any

from .base import BaseAdapter

_ENVELOPE_FORMAT = "supervisory-skill-v1"


class GenericJsonAdapter(BaseAdapter):
    """Export a skill as a JSON string with a versioned envelope.

    The envelope wraps the full skill dict and adds metadata to help consuming
    systems identify the document format.

    Output structure:
        {
            "export_format": "supervisory-skill-v1",
            "skill_id": "<id>",
            "skill": { ... full skill dict ... }
        }
    """

    def export(self, skill_data: dict[str, Any]) -> str:
        skill_id = skill_data.get("metadata", {}).get("id", "unknown")
        envelope = {
            "export_format": _ENVELOPE_FORMAT,
            "skill_id": skill_id,
            "skill": skill_data,
        }
        return json.dumps(envelope, indent=2, ensure_ascii=False, default=str)
