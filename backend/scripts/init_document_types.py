"""Initialize default document types for the archiver system."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.falkordb.client import FalkorDBClient
from app.models.archive_schemas import (
    CreateDocumentTypeRequest,
    NodeSchema,
    NodeSchemaField,
    PromptTemplate,
)
from app.services.document_archiver_service import DocumentArchiverService
from app.core.config import settings


async def init_default_document_types():
    """Initialize default document types."""
    client = FalkorDBClient(
        host=settings.falkordb_host,
        port=settings.falkordb_port,
        graph_name=settings.falkordb_graph_name,
        max_query_time=60,
    )

    try:
        await client.connect()
        service = DocumentArchiverService(client)

        # Check if document types already exist
        existing_types = await service.get_all_document_types()
        existing_extensions = {dt.file_extension for dt in existing_types.document_types}
        
        print(f"📊 Found {existing_types.count} existing document types: {existing_extensions}")

        # --- 1. Markdown Rules (.mdc) ---
        if ".mdc" not in existing_extensions:
            print("📝 Creating Markdown Rules (.mdc)...")
            rule_schema = NodeSchema(
                id="",  # Will be generated
                label="Rule",
                description="Schema for parsing rules from markdown documents",
                fields=[
                    NodeSchemaField(id="field_1", name="title", type="text", label="Назва", required=True),
                    NodeSchemaField(id="field_2", name="content", type="longtext", label="Контент", required=True),
                    NodeSchemaField(id="field_3", name="category", type="text", label="Категорія", required=False),
                    NodeSchemaField(id="field_4", name="tags", type="array", label="Теги", required=False),
                    NodeSchemaField(id="field_5", name="priority", type="enum", label="Пріоритет", required=False, enum_values=["high", "medium", "low"]),
                ],
                version=1, created_at="", updated_at=""
            )

            document_schema = NodeSchema(
                id="", label="Document", description="Schema for document metadata",
                fields=[
                    NodeSchemaField(id="field_1", name="title", type="text", label="Назва документа", required=True),
                    NodeSchemaField(id="field_2", name="file_path", type="text", label="Шлях до файлу", required=True),
                    NodeSchemaField(id="field_3", name="content_preview", type="longtext", label="Попередній перегляд контенту", required=False),
                ],
                version=1, created_at="", updated_at=""
            )

            default_prompt = PromptTemplate(
                id="", name="Default Markdown Rules Parser",
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
                version=1, created_at="", updated_at=""
            )

            request = CreateDocumentTypeRequest(
                name="Markdown Rules",
                file_extension=".mdc",
                description="Markdown documents with rules and guidelines (.mdc files)",
                node_schemas={"Rule": rule_schema, "Document": document_schema},
                prompt_template=default_prompt,
            )
            await service.create_document_type(request)
            print("✅ Created .mdc")

        # --- 2. Plain Text (.txt) ---
        if ".txt" not in existing_extensions:
            print("📝 Creating Plain Text (.txt)...")
            text_rule_schema = NodeSchema(
                id="", label="TextBlock", description="Schema for text blocks",
                fields=[
                    NodeSchemaField(id="field_1", name="content", type="longtext", label="Контент", required=True),
                    NodeSchemaField(id="field_2", name="type", type="text", label="Тип блоку", required=False),
                ],
                version=1, created_at="", updated_at=""
            )

            text_prompt = PromptTemplate(
                id="", name="Simple Text Parser",
                content="""Проаналізуй текст та витягни структуровані дані.

Текст:
{{content}}

Схема:
{{schema}}

Поверни результат у форматі JSON відповідно до схеми.
""",
                placeholders=["{{content}}", "{{schema}}"],
                version=1, created_at="", updated_at=""
            )

            text_request = CreateDocumentTypeRequest(
                name="Plain Text",
                file_extension=".txt",
                description="Plain text documents",
                node_schemas={"TextBlock": text_rule_schema},
                prompt_template=text_prompt,
            )
            await service.create_document_type(text_request)
            print("✅ Created .txt")

        # --- 3. Markdown (.md) ---
        if ".md" not in existing_extensions:
            print("📝 Creating Markdown (.md)...")
            md_schema = NodeSchema(
                id="", label="Note", description="General markdown note",
                fields=[
                    NodeSchemaField(id="field_1", name="title", type="text", label="Title", required=True),
                    NodeSchemaField(id="field_2", name="summary", type="longtext", label="Summary", required=False),
                    NodeSchemaField(id="field_3", name="content", type="longtext", label="Content", required=True),
                    NodeSchemaField(id="field_4", name="tags", type="array", label="Tags", required=False),
                ],
                version=1, created_at="", updated_at=""
            )

            md_prompt = PromptTemplate(
                id="", name="General Markdown Parser",
                content="""Analyze the markdown content and structure it.

Content:
{{content}}

Schema:
{{schema}}

Extract title, summary, main content and tags.
Return JSON matching the schema.
""",
                placeholders=["{{content}}", "{{schema}}"],
                version=1, created_at="", updated_at=""
            )

            md_request = CreateDocumentTypeRequest(
                name="Markdown",
                file_extension=".md",
                description="General markdown documents",
                node_schemas={"Note": md_schema},
                prompt_template=md_prompt,
            )
            await service.create_document_type(md_request)
            print("✅ Created .md")

        print("\n✅ Document types check/init complete!")

    except Exception as e:
        print(f"❌ Error initializing document types: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(init_default_document_types())