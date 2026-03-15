import uuid
from pathlib import Path

from fastapi import UploadFile


async def save_file(
    upload_file: UploadFile, upload_dir: str
) -> tuple[str, str]:
    unique_name = f"{uuid.uuid4().hex}_{upload_file.filename}"
    file_path = Path(upload_dir) / unique_name
    content = await upload_file.read()
    file_path.write_bytes(content)
    return str(file_path), unique_name
