import json
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.backend.models.schemas import ErrorResponse

router = APIRouter(prefix="/storage")

# Safe basename only: alphanumeric first character, then alphanumerics, dot, underscore, hyphen.
# Rejects path separators, absolute paths, and leading dots (hidden files / "..").
_SAFE_FILENAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class SaveJsonRequest(BaseModel):
    filename: str
    data: dict


def _validate_filename(filename: str, outputs_dir: Path) -> Path:
    """Validate that filename is a safe basename and resolve it inside outputs_dir."""
    if not _SAFE_FILENAME_RE.match(filename) or ".." in filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename: only alphanumerics, '.', '_' and '-' are allowed (no path separators)",
        )

    file_path = (outputs_dir / filename).resolve()
    if file_path.parent != outputs_dir.resolve():
        raise HTTPException(status_code=400, detail="Invalid filename: path escapes the outputs directory")
    return file_path


@router.post(
    path="/save-json",
    responses={
        200: {"description": "File saved successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request parameters"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def save_json_file(request: SaveJsonRequest):
    """Save JSON data to the project's /outputs directory."""
    # Create outputs directory if it doesn't exist
    project_root = Path(__file__).parent.parent.parent.parent  # Navigate to project root
    outputs_dir = project_root / "outputs"
    outputs_dir.mkdir(exist_ok=True)

    file_path = _validate_filename(request.filename, outputs_dir)

    try:
        # Save JSON data to file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(request.data, f, indent=2, ensure_ascii=False)

        return {"success": True, "message": f"File saved successfully to {file_path}", "filename": request.filename}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
