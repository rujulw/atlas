"""Documentation assertions for Atlas auth and deployment direction."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def _read_repo_file(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_readme_mentions_private_identity_platform_direction() -> None:
    readme = _read_repo_file("README.md")

    assert "tailnet-only platform shape" in readme
    assert "private identity core" in readme
    assert "future private apps" in readme


def test_architecture_mentions_tailnet_and_media_service_trust_model() -> None:
    architecture = _read_repo_file("docs/architecture.md")

    assert "tailnet-accessible private network boundary" in architecture
    assert "private identity core" in architecture
    assert "media service" in architecture
    assert "Atlas terminates end-user authentication" in architecture


def test_roadmap_mentions_tailnet_only_identity_direction() -> None:
    roadmap = _read_repo_file("docs/roadmap.md")

    assert "tailnet-only personal-cloud direction" in roadmap
    assert "canonical identity layer" in roadmap
    assert "media-service integration built on Atlas-issued identity" in roadmap
    assert "trust anchor for future apps" in roadmap
