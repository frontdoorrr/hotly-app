"""Content extraction API endpoints."""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.schemas.content import ContentExtractionRequest, ContentExtractionResponse
from app.services.content_extractor import ContentExtractor
from app.exceptions.external import UnsupportedPlatformError
from app.db.deps import get_db

router = APIRouter()


@router.post("/extract", response_model=ContentExtractionResponse)
async def extract_content(
    request: ContentExtractionRequest,
    db: Session = Depends(get_db)
) -> ContentExtractionResponse:
    """Extract content from SNS URL."""
    extractor = ContentExtractor()
    
    try:
        content = await extractor.extract_content(str(request.url))
        
        return ContentExtractionResponse(
            success=True,
            content=content,
            cached=False  # TODO: Implement caching in next task
        )
        
    except UnsupportedPlatformError as e:
        raise HTTPException(
            status_code=422, 
            detail=f"Unsupported platform: {str(e)}"
        )
    except TimeoutError:
        raise HTTPException(
            status_code=408,
            detail="Content extraction timed out. Please try again."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during content extraction: {str(e)}"
        )