import uuid
from pathlib import Path


def make_unique_filename(filename: str, upload_dir: str) -> str:
    path = Path(upload_dir) / filename
    if not path.exists():
        return filename
    stem = path.stem
    suffix = path.suffix
    unique = uuid.uuid4().hex[:8]
    return f"{stem}_{unique}{suffix}"
