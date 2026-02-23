"""Abstract base adapter for skill format exports."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseAdapter(ABC):
    """Base class for all skill export adapters.

    Subclasses transform a validated skill data dict into framework-specific
    configuration artefacts.
    """

    @abstractmethod
    def export(self, skill_data: dict[str, Any]) -> Any:
        """Export skill_data into the adapter's target format.

        Args:
            skill_data: Validated skill dict as returned by SkillRegistry.get_skill()

        Returns:
            Adapter-specific output (str, dict, etc.)
        """
