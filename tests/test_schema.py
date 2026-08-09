from pathlib import Path

import pytest

from portfolio_core import validate_data_workspace


def test_workspace_marker_is_required_and_versioned(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="marker is missing"):
        validate_data_workspace(tmp_path)

    marker = tmp_path / "portfolio.toml"
    marker.write_text("schema_version = 2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="expected 1"):
        validate_data_workspace(tmp_path)

    marker.write_text("schema_version = 1\n", encoding="utf-8")
    validate_data_workspace(tmp_path)
