
import pytest

from guardian.application.cost_storage import CostStorage


def test_cost_storage_is_abstract() -> None:
    assert CostStorage.__abstractmethods__


def test_cost_storage_requires_implementation() -> None:
    with pytest.raises(TypeError):
        CostStorage()  # type: ignore[abstract]