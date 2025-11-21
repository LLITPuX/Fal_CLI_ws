"""Service for archiving documents with dynamic schemas and versioning."""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.exceptions import ValidationError
from app.db.falkordb.client import FalkorDBClient
from app.models.archive_schemas import (
    ArchiveRequest,
    ArchiveResponse,
    ArchiveStats,
    CreateDocumentTypeRequest,
    CreatePromptVersionRequest,
    CreateSchemaVersionRequest,
    DocumentTypeSchema,
    DocumentTypeListResponse,
    NodeSchema,
    NodeSchemaField,
    PreviewNode,
    PreviewRelationship,
    PreviewRequest,
    PreviewResponse,
    PromptTemplate,
    PromptVersion,
    PromptVersionsResponse,
    RollbackPromptRequest,
    RollbackSchemaRequest,
    SchemaResponse,
    SchemaVersion,
    SchemaVersionsResponse,
)
from app.models.rule_schemas import RuleSchema
from app.services.falkordb_service import FalkorDBService
from app.services.gemini_service import GeminiService
from app.services.rule_parser_service import RuleParserService

logger = logging.getLogger(__name__)


class DocumentArchiverService:
    """Service for archiving documents with dynamic schemas and versioning."""

    def __init__(self, client: FalkorDBClient):
        """Initialize document archiver service.

        Args:
            client: FalkorDB client instance
        """
        self._client = client
        self._falkordb_service = FalkorDBService(client)
        self._rule_parser = RuleParserService()
        self._gemini_service = GeminiService()

    async def get_document_type(self, type_id: str) -> DocumentTypeSchema:
        """Get document type by ID.

        Args:
            type_id: Document type identifier

        Returns:
            Document type schema

        Raises:
            ValidationError: If document type not found
        """
        cypher = """
        MATCH (dt:DocumentType {id: $type_id})
        RETURN dt.id as id, dt.name as name, dt.file_extension as file_extension,
               dt.description as description, dt.node_schemas as node_schemas,
               dt.prompt_id as prompt_id, dt.created_at as created_at,
               dt.updated_at as updated_at
        """

        try:
            results, _ = await self._client.query(cypher, {"type_id": type_id})

            if not results:
                raise ValidationError(f"Document type not found: {type_id}")

            data = results[0]

            return DocumentTypeSchema(
                id=data["id"],
                name=data["name"],
                file_extension=data["file_extension"],
                description=data["description"],
                node_schemas=json.loads(data["node_schemas"]) if isinstance(data["node_schemas"], str) else data["node_schemas"],
                prompt_id=data["prompt_id"],
                created_at=data["created_at"],
                updated_at=data["updated_at"],
            )
        except Exception as e:
            logger.error(f"Failed to get document type: {e}", exc_info=True)
            raise ValidationError(f"Failed to get document type: {str(e)}")

    async def get_all_document_types(self) -> DocumentTypeListResponse:
        """Get all document types.

        Returns:
            List of document types
        """
        cypher = """
        MATCH (dt:DocumentType)
        RETURN dt.id as id, dt.name as name, dt.file_extension as file_extension,
               dt.description as description, dt.node_schemas as node_schemas,
               dt.prompt_id as prompt_id, dt.created_at as created_at,
               dt.updated_at as updated_at
        ORDER BY dt.name
        """

        try:
            results, _ = await self._client.query(cypher, {})

            document_types = []
            for row in results:
                document_types.append(
                    DocumentTypeSchema(
                        id=row["id"],
                        name=row["name"],
                        file_extension=row["file_extension"],
                        description=row["description"],
                        node_schemas=json.loads(row["node_schemas"]) if isinstance(row["node_schemas"], str) else row["node_schemas"],
                        prompt_id=row["prompt_id"],
                        created_at=row["created_at"],
                        updated_at=row["updated_at"],
                    )
                )

            return DocumentTypeListResponse(
                success=True,
                document_types=document_types,
                count=len(document_types),
            )
        except Exception as e:
            logger.error(f"Failed to get document types: {e}", exc_info=True)
            raise ValidationError(f"Failed to get document types: {str(e)}")

    async def create_document_type(
        self, request: CreateDocumentTypeRequest
    ) -> DocumentTypeSchema:
        """Create a new document type with schemas and prompt.

        Args:
            request: Document type creation request

        Returns:
            Created document type

        Raises:
            ValidationError: If creation fails
        """
        type_id = f"doctype_{hashlib.sha256(request.name.encode()).hexdigest()[:16]}"
        timestamp = datetime.now().isoformat()

        try:
            # Save schemas and create schema versions
            schema_ids = {}
            for label, schema in request.node_schemas.items():
                schema.id = f"schema_{hashlib.sha256(f'{type_id}_{label}'.encode()).hexdigest()[:16]}"
                schema.created_at = timestamp
                schema.updated_at = timestamp

                # Save schema as node
                await self._save_schema_to_db(schema)

                # Create initial version
                await self._create_schema_version(schema.id, schema.version, schema.model_dump())

                schema_ids[label] = schema.id

            # Save prompt template
            prompt_id = f"prompt_{hashlib.sha256(f'{type_id}_prompt'.encode()).hexdigest()[:16]}"
            request.prompt_template.id = prompt_id
            request.prompt_template.created_at = timestamp
            request.prompt_template.updated_at = timestamp

            await self._save_prompt_to_db(request.prompt_template)

            # Create initial prompt version
            await self._create_prompt_version(
                prompt_id, request.prompt_template.version, request.prompt_template.content
            )

            # Create document type node
            cypher = """
            CREATE (dt:DocumentType {
              id: $id,
              name: $name,
              file_extension: $file_extension,
              description: $description,
              node_schemas: $node_schemas,
              prompt_id: $prompt_id,
              created_at: $created_at,
              updated_at: $updated_at
            })
            RETURN dt.id as id
            """

            params = {
                "id": type_id,
                "name": request.name,
                "file_extension": request.file_extension,
                "description": request.description,
                "node_schemas": json.dumps(schema_ids),
                "prompt_id": prompt_id,
                "created_at": timestamp,
                "updated_at": timestamp,
            }

            await self._client.query(cypher, params)

            logger.info(f"Created document type: {type_id}")

            return DocumentTypeSchema(
                id=type_id,
                name=request.name,
                file_extension=request.file_extension,
                description=request.description,
                node_schemas=schema_ids,
                prompt_id=prompt_id,
                created_at=timestamp,
                updated_at=timestamp,
            )
        except Exception as e:
            logger.error(f"Failed to create document type: {e}", exc_info=True)
            raise ValidationError(f"Failed to create document type: {str(e)}")

    async def _save_schema_to_db(self, schema: NodeSchema) -> None:
        """Save node schema to database.

        Args:
            schema: Node schema to save
        """
        cypher = """
        MERGE (s:NodeSchema {id: $id})
        ON CREATE SET
          s.label = $label,
          s.description = $description,
          s.fields = $fields,
          s.version = $version,
          s.created_at = $created_at,
          s.updated_at = $updated_at
        ON MATCH SET
          s.label = $label,
          s.description = $description,
          s.fields = $fields,
          s.version = $version,
          s.updated_at = $updated_at
        RETURN s.id as id
        """

        params = {
            "id": schema.id,
            "label": schema.label,
            "description": schema.description,
            "fields": json.dumps([f.model_dump() for f in schema.fields]),
            "version": schema.version,
            "created_at": schema.created_at,
            "updated_at": schema.updated_at,
        }

        await self._client.query(cypher, params)

    async def _save_prompt_to_db(self, prompt: PromptTemplate) -> None:
        """Save prompt template to database.

        Args:
            prompt: Prompt template to save
        """
        cypher = """
        MERGE (p:PromptTemplate {id: $id})
        ON CREATE SET
          p.name = $name,
          p.content = $content,
          p.placeholders = $placeholders,
          p.version = $version,
          p.created_at = $created_at,
          p.updated_at = $updated_at
        ON MATCH SET
          p.name = $name,
          p.content = $content,
          p.placeholders = $placeholders,
          p.version = $version,
          p.updated_at = $updated_at
        RETURN p.id as id
        """

        params = {
            "id": prompt.id,
            "name": prompt.name,
            "content": prompt.content,
            "placeholders": json.dumps(prompt.placeholders),
            "version": prompt.version,
            "created_at": prompt.created_at,
            "updated_at": prompt.updated_at,
        }

        await self._client.query(cypher, params)

    async def _create_schema_version(
        self, schema_id: str, version: int, content: dict[str, Any]
    ) -> None:
        """Create a new schema version.

        Args:
            schema_id: Schema identifier
            version: Version number
            content: Schema content as dict
        """
        version_id = f"schema_ver_{schema_id}_{version}"

        cypher = """
        MATCH (s:NodeSchema {id: $schema_id})
        CREATE (sv:SchemaVersion {
          id: $version_id,
          schema_id: $schema_id,
          version: $version,
          content: $content,
          created_at: $created_at
        })
        CREATE (s)-[:HAS_VERSION]->(sv)
        RETURN sv.id as id
        """

        params = {
            "version_id": version_id,
            "schema_id": schema_id,
            "version": version,
            "content": json.dumps(content),
            "created_at": datetime.now().isoformat(),
        }

        await self._client.query(cypher, params)

    async def _create_prompt_version(
        self, prompt_id: str, version: int, content: str
    ) -> None:
        """Create a new prompt version.

        Args:
            prompt_id: Prompt identifier
            version: Version number
            content: Prompt content
        """
        version_id = f"prompt_ver_{prompt_id}_{version}"

        cypher = """
        MATCH (p:PromptTemplate {id: $prompt_id})
        CREATE (pv:PromptVersion {
          id: $version_id,
          prompt_id: $prompt_id,
          version: $version,
          content: $content,
          created_at: $created_at
        })
        CREATE (p)-[:HAS_VERSION]->(pv)
        RETURN pv.id as id
        """

        params = {
            "version_id": version_id,
            "prompt_id": prompt_id,
            "version": version,
            "content": content,
            "created_at": datetime.now().isoformat(),
        }

        await self._client.query(cypher, params)

    async def get_schema(self, schema_id: str) -> NodeSchema:
        """Get node schema by ID.

        Args:
            schema_id: Schema identifier

        Returns:
            Node schema

        Raises:
            ValidationError: If schema not found
        """
        cypher = """
        MATCH (s:NodeSchema {id: $schema_id})
        RETURN s.id as id, s.label as label, s.description as description,
               s.fields as fields, s.version as version,
               s.created_at as created_at, s.updated_at as updated_at
        """

        try:
            results, _ = await self._client.query(cypher, {"schema_id": schema_id})

            if not results:
                raise ValidationError(f"Schema not found: {schema_id}")

            data = results[0]

            # Parse fields
            fields_data = json.loads(data["fields"]) if isinstance(data["fields"], str) else data["fields"]
            fields = [NodeSchemaField(**f) for f in fields_data]

            return NodeSchema(
                id=data["id"],
                label=data["label"],
                description=data["description"],
                fields=fields,
                version=data["version"],
                created_at=data["created_at"],
                updated_at=data["updated_at"],
            )
        except Exception as e:
            logger.error(f"Failed to get schema: {e}", exc_info=True)
            raise ValidationError(f"Failed to get schema: {str(e)}")

    async def get_schema_versions(self, schema_id: str) -> SchemaVersionsResponse:
        """Get all versions of a schema.

        Args:
            schema_id: Schema identifier

        Returns:
            List of schema versions
        """
        # Get current schema to find current version
        current_schema = await self.get_schema(schema_id)
        current_version = current_schema.version

        # Get all versions
        cypher = """
        MATCH (s:NodeSchema {id: $schema_id})-[:HAS_VERSION]->(sv:SchemaVersion)
        RETURN sv.id as id, sv.schema_id as schema_id, sv.version as version,
               sv.content as content, sv.created_at as created_at
        ORDER BY sv.version DESC
        """

        try:
            results, _ = await self._client.query(cypher, {"schema_id": schema_id})

            versions = []
            for row in results:
                content = json.loads(row["content"]) if isinstance(row["content"], str) else row["content"]
                versions.append(
                    SchemaVersion(
                        id=row["id"],
                        schema_id=row["schema_id"],
                        version=row["version"],
                        content=content,
                        created_at=row["created_at"],
                    )
                )

            return SchemaVersionsResponse(
                success=True,
                versions=versions,
                current_version=current_version,
            )
        except Exception as e:
            logger.error(f"Failed to get schema versions: {e}", exc_info=True)
            raise ValidationError(f"Failed to get schema versions: {str(e)}")

    async def rollback_schema(self, request: RollbackSchemaRequest) -> SchemaResponse:
        """Rollback schema to a previous version.

        Args:
            request: Rollback request

        Returns:
            Rolled back schema

        Raises:
            ValidationError: If rollback fails
        """
        # Get the version to rollback to
        cypher = """
        MATCH (s:NodeSchema {id: $schema_id})-[:HAS_VERSION]->(sv:SchemaVersion {version: $version})
        RETURN sv.content as content
        """

        try:
            results, _ = await self._client.query(
                cypher, {"schema_id": request.schema_id, "version": request.version}
            )

            if not results:
                raise ValidationError(
                    f"Schema version {request.version} not found for schema {request.schema_id}"
                )

            content = json.loads(results[0]["content"]) if isinstance(results[0]["content"], str) else results[0]["content"]

            # Create new schema from version content
            schema = NodeSchema(**content)
            schema.version = request.version + 1  # Increment version
            schema.updated_at = datetime.now().isoformat()

            # Save updated schema
            await self._save_schema_to_db(schema)

            # Create new version
            await self._create_schema_version(schema.id, schema.version, schema.model_dump())

            logger.info(
                f"Rolled back schema {request.schema_id} to version {request.version}"
            )

            return SchemaResponse(success=True, schema=schema)
        except Exception as e:
            logger.error(f"Failed to rollback schema: {e}", exc_info=True)
            raise ValidationError(f"Failed to rollback schema: {str(e)}")

    async def create_schema_version(
        self, request: CreateSchemaVersionRequest
    ) -> SchemaResponse:
        """Create a new schema version.

        Args:
            request: Schema version creation request

        Returns:
            Created schema version
        """
        schema = request.node_schema
        schema.version = schema.version + 1  # Increment version
        schema.updated_at = datetime.now().isoformat()

        await self._save_schema_to_db(schema)
        await self._create_schema_version(schema.id, schema.version, schema.model_dump())

        logger.info(f"Created new version {schema.version} for schema {schema.id}")

        return SchemaResponse(success=True, schema=schema)

    async def get_prompt(self, prompt_id: str) -> PromptTemplate:
        """Get prompt template by ID.

        Args:
            prompt_id: Prompt identifier

        Returns:
            Prompt template

        Raises:
            ValidationError: If prompt not found
        """
        cypher = """
        MATCH (p:PromptTemplate {id: $prompt_id})
        RETURN p.id as id, p.name as name, p.content as content,
               p.placeholders as placeholders, p.version as version,
               p.created_at as created_at, p.updated_at as updated_at
        """

        try:
            results, _ = await self._client.query(cypher, {"prompt_id": prompt_id})

            if not results:
                raise ValidationError(f"Prompt not found: {prompt_id}")

            data = results[0]

            placeholders = json.loads(data["placeholders"]) if isinstance(data["placeholders"], str) else data["placeholders"]

            return PromptTemplate(
                id=data["id"],
                name=data["name"],
                content=data["content"],
                placeholders=placeholders,
                version=data["version"],
                created_at=data["created_at"],
                updated_at=data["updated_at"],
            )
        except Exception as e:
            logger.error(f"Failed to get prompt: {e}", exc_info=True)
            raise ValidationError(f"Failed to get prompt: {str(e)}")

    async def get_prompt_versions(self, prompt_id: str) -> PromptVersionsResponse:
        """Get all versions of a prompt.

        Args:
            prompt_id: Prompt identifier

        Returns:
            List of prompt versions
        """
        # Get current prompt to find current version
        current_prompt = await self.get_prompt(prompt_id)
        current_version = current_prompt.version

        # Get all versions
        cypher = """
        MATCH (p:PromptTemplate {id: $prompt_id})-[:HAS_VERSION]->(pv:PromptVersion)
        RETURN pv.id as id, pv.prompt_id as prompt_id, pv.version as version,
               pv.content as content, pv.created_at as created_at
        ORDER BY pv.version DESC
        """

        try:
            results, _ = await self._client.query(cypher, {"prompt_id": prompt_id})

            versions = []
            for row in results:
                versions.append(
                    PromptVersion(
                        id=row["id"],
                        prompt_id=row["prompt_id"],
                        version=row["version"],
                        content=row["content"],
                        created_at=row["created_at"],
                    )
                )

            return PromptVersionsResponse(
                success=True,
                versions=versions,
                current_version=current_version,
            )
        except Exception as e:
            logger.error(f"Failed to get prompt versions: {e}", exc_info=True)
            raise ValidationError(f"Failed to get prompt versions: {str(e)}")

    async def rollback_prompt(self, request: RollbackPromptRequest) -> PromptTemplate:
        """Rollback prompt to a previous version.

        Args:
            request: Rollback request

        Returns:
            Rolled back prompt

        Raises:
            ValidationError: If rollback fails
        """
        # Get the version to rollback to
        cypher = """
        MATCH (p:PromptTemplate {id: $prompt_id})-[:HAS_VERSION]->(pv:PromptVersion {version: $version})
        RETURN pv.content as content
        """

        try:
            results, _ = await self._client.query(
                cypher, {"prompt_id": request.prompt_id, "version": request.version}
            )

            if not results:
                raise ValidationError(
                    f"Prompt version {request.version} not found for prompt {request.prompt_id}"
                )

            content = results[0]["content"]

            # Get current prompt to preserve metadata
            current_prompt = await self.get_prompt(request.prompt_id)

            # Update prompt with old content
            current_prompt.content = content
            current_prompt.version = request.version + 1  # Increment version
            current_prompt.updated_at = datetime.now().isoformat()

            # Save updated prompt
            await self._save_prompt_to_db(current_prompt)

            # Create new version
            await self._create_prompt_version(
                current_prompt.id, current_prompt.version, current_prompt.content
            )

            logger.info(
                f"Rolled back prompt {request.prompt_id} to version {request.version}"
            )

            return current_prompt
        except Exception as e:
            logger.error(f"Failed to rollback prompt: {e}", exc_info=True)
            raise ValidationError(f"Failed to rollback prompt: {str(e)}")

    async def create_prompt_version(
        self, request: CreatePromptVersionRequest
    ) -> PromptTemplate:
        """Create a new prompt version.

        Args:
            request: Prompt version creation request

        Returns:
            Created prompt version
        """
        prompt = request.prompt
        prompt.version = prompt.version + 1  # Increment version
        prompt.updated_at = datetime.now().isoformat()

        await self._save_prompt_to_db(prompt)
        await self._create_prompt_version(prompt.id, prompt.version, prompt.content)

        logger.info(f"Created new version {prompt.version} for prompt {prompt.id}")

        return prompt

    def _replace_placeholders(self, template: str, values: dict[str, str]) -> str:
        """Replace placeholders in template with values.

        Args:
            template: Template string with placeholders
            values: Dictionary of placeholder -> value mappings

        Returns:
            Template with placeholders replaced
        """
        result = template
        for placeholder, value in values.items():
            # Use .format() approach to avoid f-string syntax issues with curly braces
            placeholder_pattern = "{{" + placeholder + "}}"
            result = result.replace(placeholder_pattern, value)
        return result

    async def preview_archive(self, request: PreviewRequest) -> PreviewResponse:
        """Preview document archiving without saving.

        Args:
            request: Preview request

        Returns:
            Preview response with nodes and relationships

        Raises:
            ValidationError: If preview fails
        """
        try:
            # Get document type
            doc_type = await self.get_document_type(request.document_type)

            # Determine which schema and prompt to use
            schema_id = request.schema_id
            prompt_id = request.prompt_id

            if not schema_id:
                # Use default schema for Rule nodes (first one in node_schemas)
                rule_label = "Rule"
                if rule_label in doc_type.node_schemas:
                    schema_id = doc_type.node_schemas[rule_label]
                else:
                    raise ValidationError(
                        f"No Rule schema found for document type {request.document_type}"
                    )

            if not prompt_id:
                prompt_id = doc_type.prompt_id

            # Get schema and prompt
            schema = await self.get_schema(schema_id)
            prompt_template = await self.get_prompt(prompt_id)

            # Build prompt with placeholders
            schema_json = json.dumps(
                {f.name: {"type": f.type, "required": f.required} for f in schema.fields},
                indent=2,
            )

            prompt_content = self._replace_placeholders(
                prompt_template.content,
                {
                    "content": request.content,
                    "schema": schema_json,
                    "file_path": "",  # Not available in preview
                    "document_type": doc_type.name,
                },
            )

            # Parse document using RuleParserService (temporary override of prompt)
            # We'll need to modify RuleParserService to accept custom prompt
            # For now, let's use the default parsing
            rules = await self._rule_parser.parse_document_to_rules(
                request.content, ""
            )

            # Build preview nodes and relationships
            preview_nodes = []
            preview_relationships = []

            # Document node preview
            content_hash = hashlib.sha256(request.content.encode()).hexdigest()
            doc_id = f"doc_{content_hash[:16]}"

            doc_properties = {
                "id": doc_id,
                "path": "",  # Not available in preview
                "relative_path": "",
                "type": "rules",
                "category": "preview",
                "content_hash": content_hash,
                "size_bytes": len(request.content.encode()),
            }

            preview_nodes.append(PreviewNode(label="Document", properties=doc_properties))

            # Rule nodes preview
            for rule in rules:
                rule_properties = self._build_node_properties(rule, schema)
                preview_nodes.append(PreviewNode(label="Rule", properties=rule_properties))

                # Document -> Rule relationship
                preview_relationships.append(
                    PreviewRelationship(
                        from_label="Document",
                        to_label="Rule",
                        relationship_type="CONTAINS",
                        properties={},
                    )
                )

                # Entity nodes and relationships
                for entity_name in rule.entities:
                    entity_id = f"entity_{hashlib.sha256(entity_name.lower().encode()).hexdigest()[:16]}"
                    entity_properties = {
                        "id": entity_id,
                        "canonical_name": entity_name.lower(),
                        "name": entity_name,
                        "type": "CONCEPT",
                    }

                    preview_nodes.append(
                        PreviewNode(label="Entity", properties=entity_properties)
                    )

                    # Entity -> Rule relationship
                    for context in rule.contexts:
                        preview_relationships.append(
                            PreviewRelationship(
                                from_label="Entity",
                                to_label="Rule",
                                relationship_type="HAS_RULE",
                                properties={"context": context, "priority": rule.priority},
                            )
                        )

            # Build JSON preview
            json_preview = {
                "document": doc_properties,
                "rules": [self._build_node_properties(r, schema) for r in rules],
                "entities": [
                    {
                        "id": f"entity_{hashlib.sha256(e.lower().encode()).hexdigest()[:16]}",
                        "canonical_name": e.lower(),
                        "name": e,
                        "type": "CONCEPT",
                    }
                    for rule in rules
                    for e in rule.entities
                ],
                "relationships": [
                    {"from": "Document", "to": "Rule", "type": "CONTAINS"}
                    for _ in rules
                ]
                + [
                    {
                        "from": "Entity",
                        "to": "Rule",
                        "type": "HAS_RULE",
                        "properties": {"context": ctx, "priority": rule.priority},
                    }
                    for rule in rules
                    for ctx in rule.contexts
                ],
            }

            return PreviewResponse(
                success=True,
                nodes=preview_nodes,
                relationships=preview_relationships,
                json_preview=json_preview,
            )
        except Exception as e:
            logger.error(f"Failed to preview archive: {e}", exc_info=True)
            raise ValidationError(f"Failed to preview archive: {str(e)}")

    def _build_node_properties(
        self, rule: RuleSchema, schema: NodeSchema
    ) -> dict[str, Any]:
        """Build node properties from rule using schema.

        Args:
            rule: Rule schema instance
            schema: Node schema definition

        Returns:
            Dictionary of node properties
        """
        properties: dict[str, Any] = {}

        # Map rule fields to schema fields
        rule_data = rule.model_dump()

        for field in schema.fields:
            if field.name in rule_data:
                properties[field.name] = rule_data[field.name]
            elif field.default_value is not None:
                properties[field.name] = field.default_value
            elif not field.required:
                # Optional field without default - skip
                continue

        return properties

    async def archive_document(self, request: ArchiveRequest) -> ArchiveResponse:
        """Archive a document to FalkorDB.

        Args:
            request: Archive request

        Returns:
            Archive response with statistics

        Raises:
            ValidationError: If archiving fails
        """
        try:
            # Get document type
            doc_type = await self.get_document_type(request.document_type)

            # Determine which schema and prompt to use
            schema_id = request.schema_id
            prompt_id = request.prompt_id

            if not schema_id:
                rule_label = "Rule"
                if rule_label in doc_type.node_schemas:
                    schema_id = doc_type.node_schemas[rule_label]
                else:
                    raise ValidationError(
                        f"No Rule schema found for document type {request.document_type}"
                    )

            if not prompt_id:
                prompt_id = doc_type.prompt_id

            # Get schema and prompt
            schema = await self.get_schema(schema_id)
            prompt_template = await self.get_prompt(prompt_id)

            # Build prompt with placeholders
            schema_json = json.dumps(
                {f.name: {"type": f.type, "required": f.required} for f in schema.fields},
                indent=2,
            )

            prompt_content = self._replace_placeholders(
                prompt_template.content,
                {
                    "content": request.content,
                    "schema": schema_json,
                    "file_path": request.file_path,
                    "document_type": doc_type.name,
                },
            )

            # Parse document
            rules = await self._rule_parser.parse_document_to_rules(
                request.content, request.file_path
            )

            # Calculate content hash
            content_hash = hashlib.sha256(request.content.encode()).hexdigest()
            doc_id = f"doc_{content_hash[:16]}"

            # Create Document node
            file_path_obj = Path(request.file_path) if request.file_path else Path("")
            relative_path = str(file_path_obj.relative_to(file_path_obj.parent))
            if request.file_path and "/" in request.file_path:
                relative_path = "/".join(request.file_path.split("/")[-2:])

            doc_properties = {
                "id": doc_id,
                "path": request.file_path,
                "relative_path": relative_path,
                "type": "rules",
                "category": "archived",
                "content_hash": content_hash,
                "version": "1.0.0",
                "size_bytes": len(request.content.encode()),
                "lines": len(request.content.splitlines()),
                "loaded_at": datetime.now().isoformat(),
                "status": "active",
                "chunk_count": 0,
            }

            # Create Document node
            from app.db.falkordb.schemas import CreateNodeRequest

            doc_node_request = CreateNodeRequest(
                label="Document", properties=doc_properties
            )
            await self._falkordb_service.create_node(doc_node_request)

            # Link to Knowledge Base (if exists)
            kb_id = "cursor_rules_v3"
            cypher = """
            MATCH (kb:KnowledgeBase {id: $kb_id})
            MATCH (d:Document {id: $doc_id})
            MERGE (d)-[:IN_BASE]->(kb)
            RETURN d.id as id
            """
            await self._client.query(cypher, {"kb_id": kb_id, "doc_id": doc_id})

            # Create Rule nodes
            rules_created = 0
            entities_created = 0
            relationships_created = 0

            for rule in rules:
                # Build rule properties using schema
                rule_properties = self._build_node_properties(rule, schema)
                rule_properties["id"] = rule.id

                # Create Rule node
                rule_node_request = CreateNodeRequest(
                    label="Rule", properties=rule_properties
                )
                await self._falkordb_service.create_node(rule_node_request)
                rules_created += 1

                # Create Document -> Rule relationship
                from app.db.falkordb.schemas import CreateRelationshipRequest

                rel_request = CreateRelationshipRequest(
                    from_label="Document",
                    from_properties={"id": doc_id},
                    to_label="Rule",
                    to_properties={"id": rule.id},
                    relationship_type="CONTAINS",
                    relationship_properties={},
                )
                await self._falkordb_service.create_relationship(rel_request)
                relationships_created += 1

                # Create Entity nodes and relationships
                for entity_name in rule.entities:
                    canonical_name = entity_name.lower().strip()
                    entity_id = f"entity_{hashlib.sha256(canonical_name.encode()).hexdigest()[:16]}"

                    # Check if entity exists
                    entity_check = """
                    MATCH (e:Entity {canonical_name: $canonical})
                    RETURN e.id as id, e.mention_count as count
                    """
                    entity_results, _ = await self._client.query(
                        entity_check, {"canonical": canonical_name}
                    )

                    if not entity_results:
                        # Create new entity
                        entity_properties = {
                            "id": entity_id,
                            "canonical_name": canonical_name,
                            "name": entity_name,
                            "type": "CONCEPT",
                            "mention_count": 1,
                            "first_seen": datetime.now().isoformat(),
                            "last_seen": datetime.now().isoformat(),
                            "status": "active",
                        }

                        entity_node_request = CreateNodeRequest(
                            label="Entity", properties=entity_properties
                        )
                        await self._falkordb_service.create_node(entity_node_request)
                        entities_created += 1
                    else:
                        # Update existing entity
                        entity_id = entity_results[0]["id"]
                        update_entity = """
                        MATCH (e:Entity {id: $entity_id})
                        SET e.mention_count = e.mention_count + 1,
                            e.last_seen = $timestamp
                        RETURN e.id as id
                        """
                        await self._client.query(
                            update_entity,
                            {"entity_id": entity_id, "timestamp": datetime.now().isoformat()},
                        )

                    # Create Entity -> Rule relationships for each context
                    for context in rule.contexts:
                        entity_rule_rel = CreateRelationshipRequest(
                            from_label="Entity",
                            from_properties={"id": entity_id},
                            to_label="Rule",
                            to_properties={"id": rule.id},
                            relationship_type="HAS_RULE",
                            relationship_properties={
                                "context": context,
                                "priority": rule.priority,
                                "relevance": (
                                    0.9
                                    if rule.priority == "high"
                                    else 0.7
                                    if rule.priority == "medium"
                                    else 0.5
                                ),
                                "created_at": datetime.now().isoformat(),
                            },
                        )

                        # Use MERGE to avoid duplicates
                        try:
                            await self._falkordb_service.create_relationship(entity_rule_rel)
                            relationships_created += 1
                        except Exception as e:
                            # Relationship might already exist, that's ok
                            logger.debug(f"Relationship might already exist: {e}")

            stats = ArchiveStats(
                document_id=doc_id,
                rules_created=rules_created,
                entities_created=entities_created,
                relationships_created=relationships_created,
            )

            logger.info(
                f"Archived document {doc_id}: {rules_created} rules, "
                f"{entities_created} entities, {relationships_created} relationships"
            )

            return ArchiveResponse(success=True, stats=stats)
        except Exception as e:
            logger.error(f"Failed to archive document: {e}", exc_info=True)
            raise ValidationError(f"Failed to archive document: {str(e)}")

