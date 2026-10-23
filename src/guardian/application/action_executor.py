from __future__ import annotations

from abc import ABC, abstractmethod

from guardian.domain.action import (
    ActionRequest,
    ActionResult,
)


class ActionExecutor(ABC):
    """
    Application-level contract for controlled infrastructure actions.
    """

    @abstractmethod
    def execute(
        self,
        request: ActionRequest,
    ) -> ActionResult:
        """
        Execute one explicitly permitted action.
        """
        raise NotImplementedError