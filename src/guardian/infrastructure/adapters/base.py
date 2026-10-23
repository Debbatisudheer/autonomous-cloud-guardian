from __future__ import annotations

from abc import ABC, abstractmethod

from guardian.domain.resource import Resource


class InfrastructureAdapter(ABC):
    """
    Contract for infrastructure-provider adapters.

    An adapter exposes infrastructure resources to the control plane
    without exposing provider-specific implementation details.
    """

    @abstractmethod
    def discover_resources(self) -> list[Resource]:
        """
        Discover resources from the infrastructure provider.
        """
        raise NotImplementedError