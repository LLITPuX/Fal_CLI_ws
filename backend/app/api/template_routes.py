"""API routes for node templates."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.db.falkordb.client import FalkorDBClient, get_falkordb_client
from app.db.falkordb.schemas import (
    CreateTemplateRequest,
    TemplateExportResponse,
    TemplateImportRequest,
    TemplateImportResponse,
    TemplateListResponse,
    TemplateMigrationRequest,
    TemplateMigrationResponse,
    TemplateResponse,
    UpdateTemplateRequest,
)
from app.services.template_service import TemplateService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/falkordb/templates", tags=["templates"])


def get_template_service(
    client: Annotated[FalkorDBClient, Depends(get_falkordb_client)]
) -> TemplateService:
    """Get Template service instance.

    Args:
        client: FalkorDB client from dependency

    Returns:
        Template service instance
    """
    return TemplateService(client)


TemplateServiceDep = Annotated[TemplateService, Depends(get_template_service)]


@router.post(
    "",
    response_model=TemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a template",
    description="Create a new node template with fields",
)
async def create_template(
    request: CreateTemplateRequest,
    service: TemplateServiceDep,
) -> TemplateResponse:
    """Create a new node template.

    Args:
        request: Template creation request
        service: Template service instance

    Returns:
        Created template information

    Raises:
        HTTPException: If template creation fails
    """
    try:
        template = await service.create_template(request)
        return TemplateResponse(
            success=True,
            template=template,
            message=f"Template '{template.label}' created successfully",
        )
    except Exception as e:
        logger.error(f"Template creation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "",
    response_model=TemplateListResponse,
    summary="List all templates",
    description="Get a list of all available node templates",
)
async def list_templates(
    service: TemplateServiceDep,
) -> TemplateListResponse:
    """List all templates.

    Args:
        service: Template service instance

    Returns:
        List of all templates

    Raises:
        HTTPException: If template listing fails
    """
    try:
        templates = await service.list_templates()
        return TemplateListResponse(
            success=True,
            templates=templates,
            count=len(templates),
            message=f"Retrieved {len(templates)} template(s)",
        )
    except Exception as e:
        logger.error(f"Template listing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/{template_id}",
    response_model=TemplateResponse,
    summary="Get a template",
    description="Get a specific template by ID",
)
async def get_template(
    template_id: str,
    service: TemplateServiceDep,
) -> TemplateResponse:
    """Get a template by ID.

    Args:
        template_id: Template ID
        service: Template service instance

    Returns:
        Template information

    Raises:
        HTTPException: If template not found or retrieval fails
    """
    try:
        template = await service.get_template(template_id)
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template with id '{template_id}' not found",
            )
        return TemplateResponse(
            success=True,
            template=template,
            message="Template retrieved successfully",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Template retrieval failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.put(
    "/{template_id}",
    response_model=TemplateResponse,
    summary="Update a template",
    description="Update an existing template",
)
async def update_template(
    template_id: str,
    request: UpdateTemplateRequest,
    service: TemplateServiceDep,
) -> TemplateResponse:
    """Update a template.

    Args:
        template_id: Template ID
        request: Update request
        service: Template service instance

    Returns:
        Updated template information

    Raises:
        HTTPException: If template not found or update fails
    """
    try:
        template = await service.update_template(template_id, request)
        return TemplateResponse(
            success=True,
            template=template,
            message=f"Template '{template.label}' updated successfully",
        )
    except Exception as e:
        logger.error(f"Template update failed: {e}", exc_info=True)
        status_code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in str(e).lower()
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(
            status_code=status_code,
            detail=str(e),
        )


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a template",
    description="Delete a template (only if no nodes use it)",
)
async def delete_template(
    template_id: str,
    service: TemplateServiceDep,
) -> dict[str, bool | str]:
    """Delete a template.

    Args:
        template_id: Template ID
        service: Template service instance

    Returns:
        Deletion result

    Raises:
        HTTPException: If template not found, has associated nodes, or deletion fails
    """
    try:
        await service.delete_template(template_id)
        return {
            "success": True,
            "message": "Template deleted successfully",
        }
    except Exception as e:
        logger.error(f"Template deletion failed: {e}", exc_info=True)
        status_code = (
            status.HTTP_404_NOT_FOUND
            if "not found" in str(e).lower()
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(
            status_code=status_code,
            detail=str(e),
        )


@router.post(
    "/{template_id}/migrate",
    response_model=TemplateMigrationResponse,
    summary="Migrate nodes",
    description="Add new template fields to existing nodes",
)
async def migrate_nodes(
    template_id: str,
    request: TemplateMigrationRequest,
    service: TemplateServiceDep,
) -> TemplateMigrationResponse:
    """Migrate existing nodes after template update.

    Args:
        template_id: Template ID
        request: Migration request
        service: Template service instance

    Returns:
        Migration results

    Raises:
        HTTPException: If migration fails
    """
    try:
        # Ensure template_id in request matches path parameter
        request.template_id = template_id

        result = await service.migrate_nodes(request)

        return TemplateMigrationResponse(
            success=True,
            nodes_updated=result["nodes_updated"],
            fields_added=result["fields_added"],
            message=(
                f"Migration completed: {result['nodes_updated']} node(s) updated, "
                f"{len(result['fields_added'])} field(s) added"
            ),
        )
    except Exception as e:
        logger.error(f"Node migration failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/export/all",
    response_model=TemplateExportResponse,
    summary="Export templates",
    description="Export all templates as JSON",
)
async def export_templates(
    service: TemplateServiceDep,
) -> TemplateExportResponse:
    """Export all templates.

    Args:
        service: Template service instance

    Returns:
        Exported templates

    Raises:
        HTTPException: If export fails
    """
    try:
        templates_data = await service.export_templates()
        return TemplateExportResponse(
            success=True,
            templates=templates_data,
            count=len(templates_data),
            message=f"Exported {len(templates_data)} template(s)",
        )
    except Exception as e:
        logger.error(f"Template export failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/import",
    response_model=TemplateImportResponse,
    summary="Import templates",
    description="Import templates from JSON data",
)
async def import_templates(
    request: TemplateImportRequest,
    service: TemplateServiceDep,
) -> TemplateImportResponse:
    """Import templates from JSON.

    Args:
        request: Import request with templates data
        service: Template service instance

    Returns:
        Import results

    Raises:
        HTTPException: If import fails
    """
    try:
        result = await service.import_templates(
            request.templates, request.overwrite
        )

        return TemplateImportResponse(
            success=True,
            imported=result["imported"],
            skipped=result["skipped"],
            errors=result["errors"],
            message=(
                f"Import completed: {result['imported']} imported, "
                f"{result['skipped']} skipped"
            ),
        )
    except Exception as e:
        logger.error(f"Template import failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

