"""Image upload service for profile images."""

import os
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile

# Configuration
UPLOAD_DIR = Path("uploads/profile_images")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


class ImageUploadError(Exception):
    """Custom exception for image upload errors."""
    pass


class ImageUploadService:
    """Service for handling profile image uploads."""

    def __init__(self, upload_dir: Path = UPLOAD_DIR):
        self.upload_dir = upload_dir
        self._ensure_upload_dir()

    def _ensure_upload_dir(self) -> None:
        """Create upload directory if it doesn't exist."""
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def _validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file."""
        if not file.filename:
            raise ImageUploadError("Filename is required")

        ext = Path(file.filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ImageUploadError(
                f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )

    def _generate_filename(self, user_id: str, original_filename: str) -> str:
        """Generate unique filename for uploaded image."""
        ext = Path(original_filename).suffix.lower()
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"{user_id}_{timestamp}_{unique_id}{ext}"

    async def upload_profile_image(
        self, user_id: str, file: UploadFile
    ) -> str:
        """
        Upload profile image and return the file path.

        Args:
            user_id: User identifier
            file: Uploaded file

        Returns:
            Relative path to the uploaded file

        Raises:
            ImageUploadError: If upload fails
        """
        self._validate_file(file)

        # Check file size
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise ImageUploadError(
                f"File too large. Maximum size: {MAX_FILE_SIZE // (1024 * 1024)}MB"
            )

        # Generate filename and save
        filename = self._generate_filename(user_id, file.filename or "image.jpg")
        file_path = self.upload_dir / filename

        with open(file_path, "wb") as f:
            f.write(content)

        # Return relative path for URL
        return f"/uploads/profile_images/{filename}"

    def delete_profile_image(self, file_path: str) -> bool:
        """
        Delete profile image file.

        Args:
            file_path: Path to the file (relative or full URL)

        Returns:
            True if deleted, False if not found
        """
        # Extract filename from path
        filename = Path(file_path).name
        full_path = self.upload_dir / filename

        if full_path.exists():
            full_path.unlink()
            return True
        return False

    def get_full_url(self, file_path: str, base_url: str) -> str:
        """
        Get full URL for a file path.

        Args:
            file_path: Relative file path
            base_url: Base URL of the server

        Returns:
            Full URL to the image
        """
        return f"{base_url.rstrip('/')}{file_path}"


# Singleton instance
image_upload_service = ImageUploadService()
