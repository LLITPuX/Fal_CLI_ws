"""API route handlers."""

import logging

from fastapi import APIRouter, HTTPException, status

from app.core.exceptions import (
    CLIExecutionError,
    GeminiServiceException,
    JSONParsingError,
    ValidationException,
)
from app.models.schemas import StructureRequest, StructureResponse
from app.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        Status OK response
    """
    return {"status": "ok", "service": "gemini-text-structurer"}


@router.post(
    "/structure",
    response_model=StructureResponse,
    status_code=status.HTTP_200_OK,
    summary="Structure unstructured text",
    description="Processes unstructured text using Gemini CLI and returns structured JSON",
)
async def structure_text(request: StructureRequest) -> StructureResponse:
    """Structure unstructured text using Gemini CLI.

    Args:
        request: Structure request with text and optional parameters

    Returns:
        StructureResponse with structured document

    Raises:
        HTTPException: If processing fails
    """
    try:
        # Initialize service with optional overrides
        service = GeminiService(
            cli_command=request.cli_command,
            model=request.model,
        )

        # Process text
        file_id, json_path, structured_doc = await service.structure_text(
            text=request.text,
            output_dir=request.out_dir,
        )

        return StructureResponse(
            id=file_id,
            json_path=json_path,
            data=structured_doc,
        )

    except CLIExecutionError as e:
        logger.error(f"CLI execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini CLI execution failed: {str(e)}",
        ) from e

    except JSONParsingError as e:
        logger.error(f"JSON parsing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to parse CLI output: {str(e)}",
        ) from e

    except ValidationException as e:
        logger.error(f"Validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Data validation failed: {str(e)}",
        ) from e

    except GeminiServiceException as e:
        logger.error(f"Gemini service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Service error: {str(e)}",
        ) from e

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred",
        ) from e

