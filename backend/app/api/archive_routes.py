"""Archive API routes for document archiving with dynamic schemas."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.db.falkordb.client import FalkorDBClient, get_falkordb_client
from app.models.archive_schemas import (
    ArchiveRequest,
    ArchiveResponse,
    CreateDocumentTypeRequest,
    CreatePromptVersionRequest,
    CreateSchemaVersionRequest,
    DocumentTypeListResponse,
    DocumentTypeResponse,
    PreviewRequest,
    PreviewResponse,
    PromptResponse,
    PromptVersionsResponse,
    RollbackPromptRequest,
    RollbackSchemaRequest,
    SchemaResponse,
    SchemaVersionsResponse,
)
from app.services.document_archiver_service import DocumentArchiverService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/archive", tags=["archive"])


def get_archiver_service(
    client: Annotated[FalkorDBClient, Depends(get_falkordb_client)]
) -> DocumentArchiverService:
    """Get DocumentArchiverService instance.

    Args:
        client: FalkorDB client from dependency

    Returns:
        DocumentArchiverService instance
    """
    return DocumentArchiverService(client)


DocumentArchiverServiceDep = Annotated[
    DocumentArchiverService, Depends(get_archiver_service)
]


@router.post(
    "/document",
    response_model=ArchiveResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Archive a document",
    description="Archive a document to FalkorDB with specified schema and prompt",
)
async def archive_document(
    request: ArchiveRequest,
    service: DocumentArchiverServiceDep,
) -> ArchiveResponse:
    """Archive a document to FalkorDB.

    Args:
        request: Archive request with document content, type, schema, and prompt
        service: DocumentArchiverService instance

    Returns:
        Archive response with statistics

    Raises:
        HTTPException: If archiving fails
    """
    try:
        return await service.archive_document(request)
    except Exception as e:
        logger.error(f"Document archiving failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/preview",
    response_model=PreviewResponse,
    summary="Preview document archiving",
    description="Preview document archiving without saving to database",
)
async def preview_archive(
    request: PreviewRequest,
    service: DocumentArchiverServiceDep,
) -> PreviewResponse:
    """Preview document archiving without saving.

    Args:
        request: Preview request with document content, type, schema, and prompt
        service: DocumentArchiverService instance

    Returns:
        Preview response with nodes, relationships, and JSON preview

    Raises:
        HTTPException: If preview fails
    """
    try:
        return await service.preview_archive(request)
    except Exception as e:
        logger.error(f"Preview failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/document-types",
    response_model=DocumentTypeListResponse,
    summary="Get all document types",
    description="Retrieve list of all document types with their schemas and prompts",
)
async def get_document_types(
    service: DocumentArchiverServiceDep,
) -> DocumentTypeListResponse:
    """Get all document types.

    Args:
        service: DocumentArchiverService instance

    Returns:
        List of document types

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        return await service.get_all_document_types()
    except Exception as e:
        logger.error(f"Failed to get document types: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/document-types",
    response_model=DocumentTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create document type",
    description="Create a new document type with associated schemas and prompt",
)
async def create_document_type(
    request: CreateDocumentTypeRequest,
    service: DocumentArchiverServiceDep,
) -> DocumentTypeResponse:
    """Create a new document type.

    Args:
        request: Document type creation request
        service: DocumentArchiverService instance

    Returns:
        Created document type

    Raises:
        HTTPException: If creation fails
    """
    try:
        doc_type = await service.create_document_type(request)
        return DocumentTypeResponse(success=True, document_type=doc_type)
    except Exception as e:
        logger.error(f"Failed to create document type: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/document-types/{type_id}/schemas",
    response_model=SchemaResponse,
    summary="Get schemas for document type",
    description="Retrieve node schemas associated with a document type",
)
async def get_schemas_for_type(
    type_id: str,
    service: DocumentArchiverServiceDep,
    label: str | None = None,
) -> SchemaResponse:
    """Get schemas for document type.

    Args:
        type_id: Document type identifier
        label: Optional node label to get specific schema (e.g., 'Rule', 'Document')
        service: DocumentArchiverService instance

    Returns:
        Schema response

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        doc_type = await service.get_document_type(type_id)

        if label:
            if label not in doc_type.node_schemas:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Schema for label '{label}' not found in document type {type_id}",
                )
            schema_id = doc_type.node_schemas[label]
            schema = await service.get_schema(schema_id)
            return SchemaResponse(success=True, schema=schema)
        else:
            # Return first schema as example (typically Rule)
            if doc_type.node_schemas:
                first_label = list(doc_type.node_schemas.keys())[0]
                schema_id = doc_type.node_schemas[first_label]
                schema = await service.get_schema(schema_id)
                return SchemaResponse(success=True, schema=schema)
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No schemas found for document type {type_id}",
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get schemas: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/document-types/{type_id}/schemas",
    response_model=SchemaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create schema version",
    description="Create a new version of a schema for a document type",
)
async def create_schema_version(
    type_id: str,
    request: CreateSchemaVersionRequest,
    service: DocumentArchiverServiceDep,
) -> SchemaResponse:
    """Create a new schema version.

    Args:
        type_id: Document type identifier
        request: Schema version creation request
        service: DocumentArchiverService instance

    Returns:
        Created schema version

    Raises:
        HTTPException: If creation fails
    """
    try:
        return await service.create_schema_version(request)
    except Exception as e:
        logger.error(f"Failed to create schema version: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/schemas/{schema_id}/versions",
    response_model=SchemaVersionsResponse,
    summary="Get schema versions",
    description="Retrieve all versions of a schema",
)
async def get_schema_versions(
    schema_id: str,
    service: DocumentArchiverServiceDep,
) -> SchemaVersionsResponse:
    """Get all versions of a schema.

    Args:
        schema_id: Schema identifier
        service: DocumentArchiverService instance

    Returns:
        List of schema versions

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        return await service.get_schema_versions(schema_id)
    except Exception as e:
        logger.error(f"Failed to get schema versions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/schemas/{schema_id}/rollback",
    response_model=SchemaResponse,
    summary="Rollback schema",
    description="Rollback schema to a previous version",
)
async def rollback_schema(
    schema_id: str,
    request: RollbackSchemaRequest,
    service: DocumentArchiverServiceDep,
) -> SchemaResponse:
    """Rollback schema to a previous version.

    Args:
        schema_id: Schema identifier (must match request.schema_id)
        request: Rollback request with version number
        service: DocumentArchiverService instance

    Returns:
        Rolled back schema

    Raises:
        HTTPException: If rollback fails
    """
    if request.schema_id != schema_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Schema ID in path must match request body",
        )

    try:
        return await service.rollback_schema(request)
    except Exception as e:
        logger.error(f"Failed to rollback schema: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get(
    "/prompts/{prompt_id}",
    response_model=PromptResponse,
    summary="Get prompt",
    description="Retrieve a prompt template by ID",
)
async def get_prompt(
    prompt_id: str,
    service: DocumentArchiverServiceDep,
) -> PromptResponse:
    """Get prompt template by ID.

    Args:
        prompt_id: Prompt identifier
        service: DocumentArchiverService instance

    Returns:
        Prompt template

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        prompt = await service.get_prompt(prompt_id)
        return PromptResponse(success=True, prompt=prompt)
    except Exception as e:
        logger.error(f"Failed to get prompt: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get(
    "/prompts/{prompt_id}/versions",
    response_model=PromptVersionsResponse,
    summary="Get prompt versions",
    description="Retrieve all versions of a prompt template",
)
async def get_prompt_versions(
    prompt_id: str,
    service: DocumentArchiverServiceDep,
) -> PromptVersionsResponse:
    """Get all versions of a prompt.

    Args:
        prompt_id: Prompt identifier
        service: DocumentArchiverService instance

    Returns:
        List of prompt versions

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        return await service.get_prompt_versions(prompt_id)
    except Exception as e:
        logger.error(f"Failed to get prompt versions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/prompts/{prompt_id}/rollback",
    response_model=PromptResponse,
    summary="Rollback prompt",
    description="Rollback prompt template to a previous version",
)
async def rollback_prompt(
    prompt_id: str,
    request: RollbackPromptRequest,
    service: DocumentArchiverServiceDep,
) -> PromptResponse:
    """Rollback prompt to a previous version.

    Args:
        prompt_id: Prompt identifier (must match request.prompt_id)
        request: Rollback request with version number
        service: DocumentArchiverService instance

    Returns:
        Rolled back prompt

    Raises:
        HTTPException: If rollback fails
    """
    if request.prompt_id != prompt_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt ID in path must match request body",
        )

    try:
        prompt = await service.rollback_prompt(request)
        return PromptResponse(success=True, prompt=prompt)
    except Exception as e:
        logger.error(f"Failed to rollback prompt: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/prompts/{prompt_id}/versions",
    response_model=PromptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create prompt version",
    description="Create a new version of a prompt template",
)
async def create_prompt_version(
    prompt_id: str,
    request: CreatePromptVersionRequest,
    service: DocumentArchiverServiceDep,
) -> PromptResponse:
    """Create a new prompt version.

    Args:
        prompt_id: Prompt identifier (must match request.prompt_id)
        request: Prompt version creation request
        service: DocumentArchiverService instance

    Returns:
        Created prompt version

    Raises:
        HTTPException: If creation fails
    """
    if request.prompt_id != prompt_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Prompt ID in path must match request body",
        )

    try:
        prompt = await service.create_prompt_version(request)
        return PromptResponse(success=True, prompt=prompt)
    except Exception as e:
        logger.error(f"Failed to create prompt version: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

