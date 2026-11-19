"""Builds a throwaway directory tree with synthetic marker files.

tmp/
  public/                 <- the shared directory handed to the library
    readme.txt
    docs/guide.txt
    ..hidden              <- a legitimate file whose name starts with two dots
  public-private/secret.txt   <- sibling whose name starts with "public"
  outside/secret.txt          <- unrelated directory
"""
import os

SIBLING_SECRET = b"synthetic-sibling-secret"
OUTSIDE_SECRET = b"synthetic-outside-secret"


def build(root: str) -> dict:
    layout = {
        "public/readme.txt": b"public readme",
        "public/docs/guide.txt": b"public guide",
        "public/..hidden": b"dots are legal in file names",
        "public-private/secret.txt": SIBLING_SECRET,
        "outside/secret.txt": OUTSIDE_SECRET,
    }
    for rel, data in layout.items():
        path = os.path.join(root, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as handle:
            handle.write(data)
    return {
        "base": os.path.join(root, "public"),
        "sibling_secret": os.path.join(root, "public-private", "secret.txt"),
        "outside_secret": os.path.join(root, "outside", "secret.txt"),
    }
