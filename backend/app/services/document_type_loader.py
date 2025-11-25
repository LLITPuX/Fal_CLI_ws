"""Document type loader for initializing default document types on startup."""

import logging
from datetime import datetime

from app.db.falkordb.client import FalkorDBClient
from app.models.archive_schemas import (
    CreateDocumentTypeRequest,
    NodeSchema,
    NodeSchemaField,
    PromptTemplate,
)
from app.services.document_archiver_service import DocumentArchiverService

logger = logging.getLogger(__name__)


async def init_default_document_types(client: FalkorDBClient) -> dict[str, int]:
    """Initialize default document types if they don't exist.

    Args:
        client: FalkorDB client instance

    Returns:
        Dictionary with counts: created, skipped, errors
    """
    created = 0
    skipped = 0
    errors = 0

    try:
        service = DocumentArchiverService(client)

        # Check if document types already exist
        existing_types = await service.get_all_document_types()
        existing_extensions = {dt.file_extension for dt in existing_types.document_types}

        logger.info(f"Found {existing_types.count} existing document types: {existing_extensions}")

        # --- 1. Markdown Rules (.mdc) ---
        if ".mdc" not in existing_extensions:
            try:
                logger.info("Creating Markdown Rules (.mdc)...")
                rule_schema = NodeSchema(
                    id="",
                    label="Rule",
                    description="Schema for parsing rules from markdown documents",
                    fields=[
                        NodeSchemaField(
                            id="field_1", name="title", type="text", label="Назва", required=True
                        ),
                        NodeSchemaField(
                            id="field_2",
                            name="content",
                            type="longtext",
                            label="Контент",
                            required=True,
                        ),
                        NodeSchemaField(
                            id="field_3",
                            name="category",
                            type="text",
                            label="Категорія",
                            required=False,
                        ),
                        NodeSchemaField(
                            id="field_4", name="tags", type="array", label="Теги", required=False
                        ),
                        NodeSchemaField(
                            id="field_5",
                            name="priority",
                            type="enum",
                            label="Пріоритет",
                            required=False,
                            enum_values=["high", "medium", "low"],
                        ),
                    ],
                    version=1,
                    created_at="",
                    updated_at="",
                )

                document_schema = NodeSchema(
                    id="",
                    label="Document",
                    description="Schema for document metadata",
                    fields=[
                        NodeSchemaField(
                            id="field_1",
                            name="title",
                            type="text",
                            label="Назва документа",
                            required=True,
                        ),
                        NodeSchemaField(
                            id="field_2",
                            name="file_path",
                            type="text",
                            label="Шлях до файлу",
                            required=True,
                        ),
                        NodeSchemaField(
                            id="field_3",
                            name="content_preview",
                            type="longtext",
                            label="Попередній перегляд контенту",
                            required=False,
                        ),
                    ],
                    version=1,
                    created_at="",
                    updated_at="",
                )

                default_prompt = PromptTemplate(
                    id="",
                    name="Default Markdown Rules Parser",
                    content="""Проаналізуй наступний документ та витягни з нього структуровані дані.

Документ:
{{content}}

Схема для парсингу:
{{schema}}

Інструкції:
1. Витягни всі правила, принципи та інструкції з документа
2. Структуруй дані відповідно до наданої схеми
3. Визнач зв'язки між правилами та документами
4. Поверни результат у форматі JSON, який відповідає схемі

Важливо:
- Кожне правило має бути окремим об'єктом
- Використовуй точні назви полів зі схеми
- Зберігай оригінальний контент без змін
""",
                    placeholders=["{{content}}", "{{schema}}", "{{file_path}}"],
                    version=1,
                    created_at="",
                    updated_at="",
                )

                request = CreateDocumentTypeRequest(
                    name="Markdown Rules",
                    file_extension=".mdc",
                    description="Markdown documents with rules and guidelines (.mdc files)",
                    node_schemas={"Rule": rule_schema, "Document": document_schema},
                    prompt_template=default_prompt,
                )
                await service.create_document_type(request)
                logger.info("✅ Created .mdc document type")
                created += 1
            except Exception as e:
                logger.error(f"Failed to create .mdc document type: {e}", exc_info=True)
                errors += 1
        else:
            skipped += 1

        # --- 2. Plain Text (.txt) ---
        if ".txt" not in existing_extensions:
            try:
                logger.info("Creating Plain Text (.txt)...")
                text_rule_schema = NodeSchema(
                    id="",
                    label="TextBlock",
                    description="Schema for text blocks",
                    fields=[
                        NodeSchemaField(
                            id="field_1",
                            name="content",
                            type="longtext",
                            label="Контент",
                            required=True,
                        ),
                        NodeSchemaField(
                            id="field_2",
                            name="type",
                            type="text",
                            label="Тип блоку",
                            required=False,
                        ),
                    ],
                    version=1,
                    created_at="",
                    updated_at="",
                )

                text_prompt = PromptTemplate(
                    id="",
                    name="Simple Text Parser",
                    content="""Проаналізуй текст та витягни структуровані дані.

Текст:
{{content}}

Схема:
{{schema}}

Поверни результат у форматі JSON відповідно до схеми.
""",
                    placeholders=["{{content}}", "{{schema}}"],
                    version=1,
                    created_at="",
                    updated_at="",
                )

                text_request = CreateDocumentTypeRequest(
                    name="Plain Text",
                    file_extension=".txt",
                    description="Plain text documents",
                    node_schemas={"TextBlock": text_rule_schema},
                    prompt_template=text_prompt,
                )
                await service.create_document_type(text_request)
                logger.info("✅ Created .txt document type")
                created += 1
            except Exception as e:
                logger.error(f"Failed to create .txt document type: {e}", exc_info=True)
                errors += 1
        else:
            skipped += 1

        # --- 3. Markdown (.md) ---
        if ".md" not in existing_extensions:
            try:
                logger.info("Creating Markdown (.md)...")
                md_schema = NodeSchema(
                    id="",
                    label="Note",
                    description="General markdown note",
                    fields=[
                        NodeSchemaField(
                            id="field_1", name="title", type="text", label="Title", required=True
                        ),
                        NodeSchemaField(
                            id="field_2",
                            name="summary",
                            type="longtext",
                            label="Summary",
                            required=False,
                        ),
                        NodeSchemaField(
                            id="field_3",
                            name="content",
                            type="longtext",
                            label="Content",
                            required=True,
                        ),
                        NodeSchemaField(
                            id="field_4", name="tags", type="array", label="Tags", required=False
                        ),
                    ],
                    version=1,
                    created_at="",
                    updated_at="",
                )

                md_prompt = PromptTemplate(
                    id="",
                    name="General Markdown Parser",
                    content="""Analyze the markdown content and structure it.

Content:
{{content}}

Schema:
{{schema}}

Extract title, summary, main content and tags.
Return JSON matching the schema.
""",
                    placeholders=["{{content}}", "{{schema}}"],
                    version=1,
                    created_at="",
                    updated_at="",
                )

                md_request = CreateDocumentTypeRequest(
                    name="Markdown",
                    file_extension=".md",
                    description="General markdown documents",
                    node_schemas={"Note": md_schema},
                    prompt_template=md_prompt,
                )
                await service.create_document_type(md_request)
                logger.info("✅ Created .md document type")
                created += 1
            except Exception as e:
                logger.error(f"Failed to create .md document type: {e}", exc_info=True)
                errors += 1
        else:
            skipped += 1

        logger.info(
            f"Document types initialization completed: {created} created, "
            f"{skipped} skipped, {errors} errors"
        )

        return {"created": created, "skipped": skipped, "errors": errors}

    except Exception as e:
        logger.error(f"Document types initialization failed: {e}", exc_info=True)
        raise


async def load_default_document_types(client: FalkorDBClient) -> None:
    """Load default document types on startup.

    Args:
        client: FalkorDB client instance
    """
    try:
        logger.info("Initializing default document types...")
        result = await init_default_document_types(client)
        logger.info(
            f"Default document types initialized: {result['created']} new, "
            f"{result['skipped']} existing, {result['errors']} errors"
        )
    except Exception as e:
        logger.error(f"Failed to initialize default document types: {e}", exc_info=True)
        logger.warning("Continuing without default document types")

