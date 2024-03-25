"""Common utilities."""

from pathlib import Path


def rm_tree(pth: Path) -> None:
    """Remove path tree."""
    for child in pth.iterdir():
        if child.is_file():
            child.unlink()
        else:
            rm_tree(child)
    pth.rmdir()
