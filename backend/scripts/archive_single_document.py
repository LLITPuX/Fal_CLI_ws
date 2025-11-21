"""
Archive a single document using DocumentArchiverService.

Usage:
    python backend/scripts/archive_single_document.py \
        --file path/to/document.mdc \
        [--document-type type_id] \
        [--schema-id schema_id] \
        [--prompt-id prompt_id] \
        [--preview] \
        [--output-json output.json]
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.db.falkordb.client import FalkorDBClient
from app.models.archive_schemas import ArchiveRequest, PreviewRequest
from app.services.document_archiver_service import DocumentArchiverService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Archive a single document to FalkorDB"
    )
    parser.add_argument(
        "--file",
        type=str,
        required=True,
        help="Path to document file (.mdc, .md, .txt)",
    )
    parser.add_argument(
        "--document-type",
        type=str,
        default=None,
        help="Document type ID (optional, auto-detected from extension)",
    )
    parser.add_argument(
        "--schema-id",
        type=str,
        default=None,
        help="Schema ID (optional, uses default for document type)",
    )
    parser.add_argument(
        "--prompt-id",
        type=str,
        default=None,
        help="Prompt ID (optional, uses default for document type)",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Preview only, don't save to database",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="Save JSON preview to file (only for --preview)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default=settings.falkordb_host,
        help="FalkorDB host (default: from config)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.falkordb_port,
        help="FalkorDB port (default: from config)",
    )
    parser.add_argument(
        "--graph",
        type=str,
        default="cursor_memory",
        help="Graph name (default: cursor_memory)",
    )

    args = parser.parse_args()

    # Read file
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"[ERROR] File not found: {args.file}")
        return 1

    try:
        content = file_path.read_text(encoding="utf-8")
        print(f"[+] Read file: {args.file} ({len(content)} bytes)")
    except Exception as e:
        print(f"[ERROR] Failed to read file: {e}")
        return 1

    # Auto-detect document type if not provided
    document_type = args.document_type
    if not document_type:
        extension = file_path.suffix.lower()
        extension_to_type = {
            ".mdc": "doctype_markdown_rules",
            ".md": "doctype_markdown",
            ".txt": "doctype_text",
        }
        document_type = extension_to_type.get(extension, "doctype_markdown")
        print(f"[+] Auto-detected document type: {document_type} (extension: {extension})")

    # Connect to FalkorDB
    print(f"[+] Connecting to FalkorDB at {args.host}:{args.port}...")
    client = FalkorDBClient(
        host=args.host,
        port=args.port,
        graph_name=args.graph,
        max_query_time=60,
    )

    try:
        await client.connect()
        print(f"    [OK] Connected to graph: {args.graph}\n")
    except Exception as e:
        print(f"    [ERROR] Failed to connect: {e}")
        return 1

    try:
        # Create archiver service
        archiver = DocumentArchiverService(client)

        if args.preview:
            # Preview mode
            print("[*] PREVIEW MODE - No changes will be saved\n")
            request = PreviewRequest(
                content=content,
                document_type=document_type,
                schema_id=args.schema_id,
                prompt_id=args.prompt_id,
            )

            try:
                result = await archiver.preview_archive(request)
                print(f"[OK] Preview generated successfully\n")

                # Print summary
                print("=" * 60)
                print("PREVIEW SUMMARY")
                print("=" * 60)
                print(f"Nodes to create: {len(result.nodes)}")
                print(f"  - Documents: {sum(1 for n in result.nodes if n.label == 'Document')}")
                print(f"  - Rules: {sum(1 for n in result.nodes if n.label == 'Rule')}")
                print(f"  - Entities: {sum(1 for n in result.nodes if n.label == 'Entity')}")
                print(f"Relationships to create: {len(result.relationships)}")
                print(f"  - CONTAINS: {sum(1 for r in result.relationships if r.relationship_type == 'CONTAINS')}")
                print(f"  - HAS_RULE: {sum(1 for r in result.relationships if r.relationship_type == 'HAS_RULE')}")
                print("=" * 60)

                # Save JSON if requested
                if args.output_json:
                    output_path = Path(args.output_json)
                    output_path.write_text(
                        json.dumps(result.json_preview, indent=2), encoding="utf-8"
                    )
                    print(f"\n[+] JSON preview saved to: {args.output_json}")
                else:
                    # Print sample JSON (first 1000 chars)
                    json_str = json.dumps(result.json_preview, indent=2)
                    print(f"\n[*] JSON Preview (first 1000 chars):")
                    print("-" * 60)
                    print(json_str[:1000])
                    if len(json_str) > 1000:
                        print(f"\n... ({len(json_str) - 1000} more characters)")
                    print("-" * 60)

            except Exception as e:
                print(f"[ERROR] Preview failed: {e}")
                logger.exception(e)
                return 1
        else:
            # Archive mode
            print("[*] ARCHIVE MODE - Document will be saved to database\n")
            request = ArchiveRequest(
                content=content,
                file_path=str(file_path),
                document_type=document_type,
                schema_id=args.schema_id,
                prompt_id=args.prompt_id,
            )

            try:
                result = await archiver.archive_document(request)
                print(f"[OK] Document archived successfully\n")

                # Print summary
                print("=" * 60)
                print("ARCHIVE SUMMARY")
                print("=" * 60)
                print(f"Document ID: {result.stats.document_id}")
                print(f"Rules created: {result.stats.rules_created}")
                print(f"Entities created: {result.stats.entities_created}")
                print(f"Relationships created: {result.stats.relationships_created}")
                print("=" * 60)

            except Exception as e:
                print(f"[ERROR] Archive failed: {e}")
                logger.exception(e)
                return 1

        return 0

    finally:
        await client.disconnect()
        print("\n[+] Disconnected from FalkorDB")


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)



