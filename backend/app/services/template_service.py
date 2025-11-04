"""Template service for managing node templates."""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.exceptions import ValidationError
from app.db.falkordb.client import FalkorDBClient
from app.db.falkordb.schemas import (
    CreateTemplateRequest,
    NodeTemplate,
    TemplateField,
    TemplateMigrationRequest,
    UpdateTemplateRequest,
)

logger = logging.getLogger(__name__)


class TemplateService:
    """Service for node template operations."""

    def __init__(self, client: FalkorDBClient):
        """Initialize service with FalkorDB client.

        Args:
            client: FalkorDB client instance
        """
        self._client = client

    async def create_template(self, request: CreateTemplateRequest) -> NodeTemplate:
        """Create a new node template.

        Args:
            request: Template creation request

        Returns:
            Created node template

        Raises:
            ValidationError: If template creation fails or label already exists
        """
        try:
            # Check if template with this label already exists
            existing = await self.get_template_by_label(request.label)
            if existing:
                raise ValidationError(
                    f"Template with label '{request.label}' already exists"
                )

            # Generate template ID and timestamps
            template_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc).isoformat()

            # Build template data
            template_data = {
                "id": template_id,
                "label": request.label,
                "icon": request.icon,
                "description": request.description,
                "fields": [field.model_dump() for field in request.fields],
                "created_at": now,
                "updated_at": now,
            }

            # Store template as a node in FalkorDB
            cypher = """
            CREATE (t:NodeTemplate {
                id: $id,
                label: $label,
                template_data: $template_data
            })
            RETURN t
            """

            params = {
                "id": template_id,
                "label": request.label,
                "template_data": json.dumps(template_data),
            }

            await self._client.query(cypher, params)

            logger.info(f"Created template '{request.label}' with id: {template_id}")

            return NodeTemplate(**template_data)

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to create template: {e}", exc_info=True)
            raise ValidationError(f"Template creation failed: {str(e)}")

    async def get_template(self, template_id: str) -> NodeTemplate | None:
        """Get a template by ID.

        Args:
            template_id: Template ID

        Returns:
            Template if found, None otherwise

        Raises:
            ValidationError: If template retrieval fails
        """
        try:
            cypher = """
            MATCH (t:NodeTemplate {id: $id})
            RETURN t.template_data as data
            """

            results, _ = await self._client.query(cypher, {"id": template_id})

            if not results:
                return None

            template_data = json.loads(results[0]["data"])
            return NodeTemplate(**template_data)

        except Exception as e:
            logger.error(f"Failed to get template: {e}", exc_info=True)
            raise ValidationError(f"Template retrieval failed: {str(e)}")

    async def get_template_by_label(self, label: str) -> NodeTemplate | None:
        """Get a template by label.

        Args:
            label: Template label

        Returns:
            Template if found, None otherwise

        Raises:
            ValidationError: If template retrieval fails
        """
        try:
            cypher = """
            MATCH (t:NodeTemplate {label: $label})
            RETURN t.template_data as data
            """

            results, _ = await self._client.query(cypher, {"label": label})

            if not results:
                return None

            template_data = json.loads(results[0]["data"])
            return NodeTemplate(**template_data)

        except Exception as e:
            logger.error(f"Failed to get template by label: {e}", exc_info=True)
            raise ValidationError(f"Template retrieval failed: {str(e)}")

    async def list_templates(self) -> list[NodeTemplate]:
        """List all templates.

        Returns:
            List of all templates

        Raises:
            ValidationError: If template listing fails
        """
        try:
            cypher = """
            MATCH (t:NodeTemplate)
            RETURN t.template_data as data
            ORDER BY t.label
            """

            results, _ = await self._client.query(cypher, {})

            templates = []
            for row in results:
                template_data = json.loads(row["data"])
                templates.append(NodeTemplate(**template_data))

            logger.info(f"Retrieved {len(templates)} templates")
            return templates

        except Exception as e:
            logger.error(f"Failed to list templates: {e}", exc_info=True)
            raise ValidationError(f"Template listing failed: {str(e)}")

    async def update_template(
        self, template_id: str, request: UpdateTemplateRequest
    ) -> NodeTemplate:
        """Update an existing template.

        Args:
            template_id: Template ID
            request: Update request

        Returns:
            Updated template

        Raises:
            ValidationError: If template not found or update fails
        """
        try:
            # Get existing template
            existing = await self.get_template(template_id)
            if not existing:
                raise ValidationError(f"Template with id '{template_id}' not found")

            # Update fields
            updated_data = existing.model_dump()
            if request.icon is not None:
                updated_data["icon"] = request.icon
            if request.description is not None:
                updated_data["description"] = request.description
            if request.fields is not None:
                updated_data["fields"] = [field.model_dump() for field in request.fields]

            updated_data["updated_at"] = datetime.now(timezone.utc).isoformat()

            # Update in database
            cypher = """
            MATCH (t:NodeTemplate {id: $id})
            SET t.template_data = $template_data
            RETURN t
            """

            params = {
                "id": template_id,
                "template_data": json.dumps(updated_data),
            }

            await self._client.query(cypher, params)

            logger.info(f"Updated template '{template_id}'")

            return NodeTemplate(**updated_data)

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to update template: {e}", exc_info=True)
            raise ValidationError(f"Template update failed: {str(e)}")

    async def delete_template(self, template_id: str) -> bool:
        """Delete a template.

        Args:
            template_id: Template ID

        Returns:
            True if deleted successfully

        Raises:
            ValidationError: If template has associated nodes or deletion fails
        """
        try:
            # Check if template exists
            template = await self.get_template(template_id)
            if not template:
                raise ValidationError(f"Template with id '{template_id}' not found")

            # Check if any nodes use this template
            node_count_query = """
            MATCH (n {_template_id: $template_id})
            RETURN count(n) as count
            """

            results, _ = await self._client.query(
                node_count_query, {"template_id": template_id}
            )

            node_count = results[0]["count"] if results else 0

            if node_count > 0:
                raise ValidationError(
                    f"Cannot delete template '{template.label}' - "
                    f"it is used by {node_count} node(s)"
                )

            # Delete template
            cypher = """
            MATCH (t:NodeTemplate {id: $id})
            DELETE t
            """

            await self._client.query(cypher, {"id": template_id})

            logger.info(f"Deleted template '{template_id}'")
            return True

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete template: {e}", exc_info=True)
            raise ValidationError(f"Template deletion failed: {str(e)}")

    async def migrate_nodes(
        self, request: TemplateMigrationRequest
    ) -> dict[str, Any]:
        """Migrate existing nodes after template update.

        This adds new fields from the template to existing nodes.

        Args:
            request: Migration request

        Returns:
            Migration results with node count and added fields

        Raises:
            ValidationError: If migration fails
        """
        try:
            # Get template
            template = await self.get_template(request.template_id)
            if not template:
                raise ValidationError(
                    f"Template with id '{request.template_id}' not found"
                )

            # Find all nodes with this template
            nodes_query = """
            MATCH (n:{label} {{_template_id: $template_id}})
            RETURN n
            """.format(
                label=template.label
            )

            nodes_result, _ = await self._client.query(
                nodes_query, {"template_id": request.template_id}
            )

            nodes_updated = 0
            fields_added = []

            # For each node, add missing fields
            for node_row in nodes_result:
                node = node_row["n"]
                node_props = node.get("properties", {}) if hasattr(node, "properties") else {}

                # Find fields that don't exist in node
                updates = {}
                for field in template.fields:
                    if field.name not in node_props:
                        # Add field with default value or None
                        if request.apply_defaults and field.default_value is not None:
                            updates[field.name] = field.default_value
                        else:
                            updates[field.name] = None

                        if field.name not in fields_added:
                            fields_added.append(field.name)

                # Update node if there are new fields
                if updates:
                    # Build SET clause
                    set_clauses = [f"n.{key} = ${key}" for key in updates.keys()]
                    set_clause = ", ".join(set_clauses)

                    update_query = f"""
                    MATCH (n:{template.label} {{_template_id: $template_id}})
                    SET {set_clause}
                    """

                    params = {"template_id": request.template_id, **updates}
                    await self._client.query(update_query, params)
                    nodes_updated += len(nodes_result)

            logger.info(
                f"Migrated {nodes_updated} nodes for template '{template.label}', "
                f"added fields: {fields_added}"
            )

            return {
                "nodes_updated": nodes_updated,
                "fields_added": fields_added,
            }

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to migrate nodes: {e}", exc_info=True)
            raise ValidationError(f"Node migration failed: {str(e)}")

    async def export_templates(self) -> list[dict[str, Any]]:
        """Export all templates to JSON format.

        Returns:
            List of template data dictionaries

        Raises:
            ValidationError: If export fails
        """
        try:
            templates = await self.list_templates()
            return [template.model_dump() for template in templates]

        except Exception as e:
            logger.error(f"Failed to export templates: {e}", exc_info=True)
            raise ValidationError(f"Template export failed: {str(e)}")

    async def import_templates(
        self, templates_data: list[dict[str, Any]], overwrite: bool = False
    ) -> dict[str, Any]:
        """Import templates from JSON data.

        Args:
            templates_data: List of template data dictionaries
            overwrite: Whether to overwrite existing templates with same label

        Returns:
            Import results with counts

        Raises:
            ValidationError: If import fails
        """
        imported = 0
        skipped = 0
        errors = []

        try:
            for template_data in templates_data:
                try:
                    # Check if template with this label exists
                    label = template_data.get("label")
                    if not label:
                        errors.append("Template missing label field")
                        continue

                    existing = await self.get_template_by_label(label)

                    if existing:
                        if overwrite:
                            # Delete existing and create new
                            try:
                                await self.delete_template(existing.id)
                            except ValidationError:
                                # Can't delete because nodes exist - skip
                                errors.append(
                                    f"Cannot overwrite template '{label}' - "
                                    f"it has associated nodes"
                                )
                                skipped += 1
                                continue
                        else:
                            skipped += 1
                            continue

                    # Parse template fields
                    fields = []
                    for field_data in template_data.get("fields", []):
                        fields.append(TemplateField(**field_data))

                    # Create template
                    request = CreateTemplateRequest(
                        label=label,
                        icon=template_data.get("icon"),
                        description=template_data.get("description", "Imported template"),
                        fields=fields,
                    )

                    await self.create_template(request)
                    imported += 1

                except Exception as e:
                    errors.append(f"Failed to import template '{label}': {str(e)}")

            logger.info(
                f"Import completed: {imported} imported, {skipped} skipped, "
                f"{len(errors)} errors"
            )

            return {
                "imported": imported,
                "skipped": skipped,
                "errors": errors,
            }

        except Exception as e:
            logger.error(f"Failed to import templates: {e}", exc_info=True)
            raise ValidationError(f"Template import failed: {str(e)}")

