from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pathlib import Path
import os

from app.api.deps import get_current_user
from app.models.user import User
from app.config import settings

router = APIRouter()

@router.get("/{user_id}/{filename}")
async def download_file(
    user_id: str,
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """Download exported file"""
    # Security: Ensure user can only download their own files
    if str(current_user.id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only download your own exports"
        )
    
    # Construct file path
    file_path = os.path.join(settings.UPLOAD_DIR, "exports", user_id, filename)
    
    # Check if file exists
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Determine media type
    ext = Path(filename).suffix.lower()
    media_types = {
        '.pdf': 'application/pdf',
        '.png': 'image/png',
        '.json': 'application/json',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.svg': 'image/svg+xml'
    }
    
    media_type = media_types.get(ext, 'application/octet-stream')
    
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename
    )
