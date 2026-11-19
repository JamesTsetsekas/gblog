"""Synthetic vulnerable version. The containment check compares strings, not paths."""
import os

__all__ = ["download", "list_names"]


def _safe_path(base_dir: str, user_path: str) -> str:
    base = os.path.normpath(base_dir)
    candidate = os.path.normpath(os.path.join(base, user_path))
    # BUG: "/srv/public-private" starts with "/srv/public", so a sibling directory
    # whose name merely begins with the base directory's name passes this check.
    if not candidate.startswith(base):
        raise PermissionError("path escapes the shared directory")
    return candidate


def download(base_dir: str, user_path: str) -> bytes:
    """Public entry point: return the bytes of a file under base_dir."""
    with open(_safe_path(base_dir, user_path), "rb") as handle:
        return handle.read()


def list_names(base_dir: str) -> list:
    """Public entry point: names directly inside base_dir."""
    return sorted(os.listdir(base_dir))


def _legacy_read(base_dir: str, user_path: str) -> bytes:
    """Old helper with no containment check at all. Nothing in this module calls it."""
    with open(os.path.join(base_dir, user_path), "rb") as handle:
        return handle.read()
