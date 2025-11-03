"""API route handlers."""

import logging
import time

from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.core.exceptions import (
    CLIExecutionError,
    GeminiServiceException,
    JSONParsingError,
    ValidationException,
)
from app.models.schemas import ModelResult, MultiModelResponse, StructureRequest
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
    response_model=MultiModelResponse,
    status_code=status.HTTP_200_OK,
    summary="Structure text with Gemini",
    description="Processes unstructured text using configured Gemini models and returns structured results with metrics",
)
async def structure_text(request: StructureRequest) -> MultiModelResponse:
    """Structure unstructured text using the configured Gemini models sequentially.

    Args:
        request: Structure request with text and optional parameters

    Returns:
        MultiModelResponse with results from all models

    Raises:
        HTTPException: If processing fails
    """
    start_time = time.time()
    results: list[ModelResult] = []

    if not settings.gemini_models:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No Gemini models configured on the server",
        )

    # Determine which models to run
    if request.model:
        if request.model not in settings.gemini_models:
            available = ", ".join(settings.gemini_models)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Model '{request.model}' is not allowed. "
                    f"Available models: {available}"
                ),
            )
        models_to_run = [request.model]
    else:
        models_to_run = settings.gemini_models

    # Process with each model sequentially
    for model in models_to_run:
        logger.info(f"Processing with model: {model}")
        
        try:
            # Initialize service for this model
            service = GeminiService(
                cli_command=request.cli_command,
                model=model,
            )

            # Process text with optional custom schema
            file_id, json_path, structured_doc, metrics = await service.structure_text(
                text=request.text,
                output_dir=request.out_dir,
                custom_schema=request.custom_schema,
            )

            # Add successful result
            results.append(
                ModelResult(
                    id=file_id,
                    json_path=json_path,
                    data=structured_doc,
                    metrics=metrics,
                    error=None,
                )
            )
            logger.info(f"Model {model} completed successfully")

        except (CLIExecutionError, JSONParsingError, ValidationException) as e:
            # Log error but continue with next model
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.warning(f"Model {model} failed: {error_msg}")
            
            # Add failed result with error
            results.append(
                ModelResult(
                    id="",
                    json_path="",
                    data=None,  # type: ignore
                    metrics=None,  # type: ignore
                    error=error_msg,
                )
            )

        except Exception as e:
            # Log unexpected error but continue
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Model {model} failed unexpectedly: {e}", exc_info=True)
            
            results.append(
                ModelResult(
                    id="",
                    json_path="",
                    data=None,  # type: ignore
                    metrics=None,  # type: ignore
                    error=error_msg,
                )
            )

    total_time = time.time() - start_time

    # Check if all models failed
    if all(r.error is not None for r in results):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="All models failed to process the text",
        )

    return MultiModelResponse(
        results=results,
        total_processing_time_seconds=round(total_time, 2),
    )

