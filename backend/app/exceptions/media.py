"""Media processing exceptions."""


class MediaError(Exception):
    """Base media processing exception."""

    pass


class ImageDownloadError(MediaError):
    """Image download failed."""

    pass


class ImageProcessingError(MediaError):
    """Image processing failed."""

    pass


class InvalidImageError(MediaError):
    """Invalid image."""

    pass


class VideoProcessingError(MediaError):
    """Video processing failed."""

    pass


class MediaTimeoutError(MediaError):
    """Media processing timeout."""

    pass
