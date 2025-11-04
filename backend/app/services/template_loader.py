"""Template loader for loading default templates on startup."""

import json
import logging
from pathlib import Path
from typing import Any

from app.db.falkordb.client import FalkorDBClient
from app.db.falkordb.schemas import CreateTemplateRequest, TemplateField
from app.services.template_service import TemplateService

logger = logging.getLogger(__name__)


class TemplateLoader:
    """Loads default templates from JSON files."""

    def __init__(self, client: FalkorDBClient, templates_dir: str = "backend/templates"):
        """Initialize template loader.

        Args:
            client: FalkorDB client instance
            templates_dir: Directory containing template JSON files
        """
        self._service = TemplateService(client)
        self._templates_dir = Path(templates_dir)

    async def load_default_templates(self) -> dict[str, int]:
        """Load default templates from JSON files.

        Returns:
            Dictionary with counts: loaded, skipped, errors

        Raises:
            Exception: If template loading fails critically
        """
        loaded = 0
        skipped = 0
        errors = 0

        try:
            # Check if templates directory exists
            if not self._templates_dir.exists():
                logger.warning(
                    f"Templates directory '{self._templates_dir}' does not exist"
                )
                return {"loaded": 0, "skipped": 0, "errors": 0}

            # Get all JSON files in templates directory
            template_files = list(self._templates_dir.glob("*.json"))

            if not template_files:
                logger.warning(
                    f"No template files found in '{self._templates_dir}'"
                )
                return {"loaded": 0, "skipped": 0, "errors": 0}

            logger.info(f"Found {len(template_files)} template file(s) to load")

            # Load each template file
            for template_file in template_files:
                try:
                    # Read JSON file
                    with open(template_file, "r", encoding="utf-8") as f:
                        template_data = json.load(f)

                    label = template_data.get("label")
                    if not label:
                        logger.error(
                            f"Template in {template_file.name} missing label field"
                        )
                        errors += 1
                        continue

                    # Check if template already exists
                    existing = await self._service.get_template_by_label(label)
                    if existing:
                        logger.info(
                            f"Template '{label}' already exists, skipping"
                        )
                        skipped += 1
                        continue

                    # Parse fields
                    fields = []
                    for field_data in template_data.get("fields", []):
                        fields.append(TemplateField(**field_data))

                    # Create template
                    request = CreateTemplateRequest(
                        label=label,
                        icon=template_data.get("icon"),
                        description=template_data.get(
                            "description", "Default template"
                        ),
                        fields=fields,
                    )

                    await self._service.create_template(request)
                    logger.info(f"Loaded template '{label}' from {template_file.name}")
                    loaded += 1

                except Exception as e:
                    logger.error(
                        f"Failed to load template from {template_file.name}: {e}",
                        exc_info=True,
                    )
                    errors += 1

            logger.info(
                f"Template loading completed: {loaded} loaded, "
                f"{skipped} skipped, {errors} errors"
            )

            return {
                "loaded": loaded,
                "skipped": skipped,
                "errors": errors,
            }

        except Exception as e:
            logger.error(f"Template loading failed: {e}", exc_info=True)
            raise


async def load_default_templates(client: FalkorDBClient) -> None:
    """Load default templates on startup.

    Args:
        client: FalkorDB client instance
    """
    try:
        logger.info("Loading default node templates...")
        loader = TemplateLoader(client)
        result = await loader.load_default_templates()
        logger.info(
            f"Default templates loaded: {result['loaded']} new, "
            f"{result['skipped']} existing, {result['errors']} errors"
        )
    except Exception as e:
        logger.error(f"Failed to load default templates: {e}", exc_info=True)
        logger.warning("Continuing without default templates")

