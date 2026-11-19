"""Toy regression fix for a trusted, immutable directory tree.

Resolved path components block the demonstrated prefix bypass and existing
symlink escapes. Resolve/check and open are separate operations: this does not
protect against an attacker mutating the directory tree between those steps.
It is not a general file-serving security boundary.
"""
from pathlib import Path

__all__ = ["download", "list_names"]


def _safe_path(base_dir: str, user_path: str) -> Path:
    base = Path(base_dir).resolve()
    candidate = (base / user_path).resolve()
    if not candidate.is_relative_to(base):
        raise PermissionError("path escapes the shared directory")
    return candidate


def download(base_dir: str, user_path: str) -> bytes:
    """Public entry point: return the bytes of a file under base_dir."""
    return _safe_path(base_dir, user_path).read_bytes()


def list_names(base_dir: str) -> list:
    """Public entry point: names directly inside base_dir."""
    return sorted(p.name for p in Path(base_dir).iterdir())

# The unreferenced _legacy_read helper was deleted as part of the patch.
