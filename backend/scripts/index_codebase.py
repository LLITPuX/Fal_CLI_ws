"""
Index Python codebase into Knowledge Base (cursor_memory graph).

This script parses Python files using AST and creates CodeFile and Function nodes.

Usage:
    python backend/scripts/index_codebase.py [--force-reload]
"""

import asyncio
import ast
import hashlib
import sys
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.falkordb.client import FalkorDBClient
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)


class CodebaseIndexer:
    """Index Python codebase into FalkorDB Knowledge Base."""
    
    def __init__(self, codebase_path: str = "backend/app"):
        self.codebase_path = Path(codebase_path)
        self.kb_id = "cursor_rules_v3"  # Same KB as rules
        self.client: FalkorDBClient | None = None
        self._client_created_here = False
        self.stats = {
            "files_indexed": 0,
            "functions_indexed": 0,
            "errors": []
        }
    
    async def index_all(self, force_reload: bool = False):
        """
        Index all Python files in codebase.
        
        Args:
            force_reload: If True, clear existing code nodes and reindex
        """
        print("[*] Codebase Indexer")
        print(f"    Target Graph: cursor_memory")
        print(f"    KB ID: {self.kb_id}")
        print(f"    Codebase Path: {self.codebase_path}\n")
        
        # Initialize FalkorDB client if not already set
        if self.client is None:
            print("[+] Connecting to FalkorDB...")
            self.client = FalkorDBClient(
                host=settings.falkordb_host,
                port=settings.falkordb_port,
                graph_name="cursor_memory",
                max_query_time=60
            )
            self._client_created_here = True
            
            try:
                await self.client.connect()
                print(f"    [OK] Connected to FalkorDB\n")
            except Exception as e:
                print(f"    [ERROR] Failed to connect: {e}")
                return False
        else:
            print("[+] Using existing FalkorDB connection\n")
        
        # Check if KB exists
        kb_exists = await self._check_knowledge_base_exists()
        if not kb_exists:
            print("[!] Knowledge Base not found. Load rules first.")
            return False
        
        # Check if code already indexed
        if force_reload:
            print("[+] Force reload: clearing existing code nodes...")
            await self._clear_code_nodes()
        
        code_count = await self._check_code_file_count()
        if code_count > 0 and not force_reload:
            print(f"[!] Codebase already indexed ({code_count} files). Use --force-reload to reindex.")
            return False
        
        # Find all Python files
        python_files = self._find_python_files()
        print(f"[*] Found {len(python_files)} Python files to index\n")
        
        if not python_files:
            print("[!] No Python files found.")
            return False
        
        # Index each file
        print(f"[+] Indexing {len(python_files)} files...")
        for idx, file_path in enumerate(python_files, 1):
            print(f"\n  [{idx}/{len(python_files)}] {file_path.relative_to(self.codebase_path)}")
            await self._index_file(file_path)
        
        # Print summary
        self._print_summary()
        
        # Cleanup
        if self._client_created_here:
            try:
                await self.client.disconnect()
            except Exception:
                pass
        
        return len(self.stats["errors"]) == 0
    
    def _find_python_files(self) -> List[Path]:
        """Find all Python files in codebase (excluding tests)."""
        python_files = []
        
        # Try container path first, then local path
        if not self.codebase_path.exists():
            # Try container path
            container_path = Path("/app/app")
            if container_path.exists():
                base_path = container_path
            else:
                return []
        else:
            base_path = self.codebase_path
        
        # Find all .py files, excluding __pycache__ and tests
        for py_file in base_path.rglob("*.py"):
            # Skip __pycache__ directories
            if "__pycache__" in str(py_file):
                continue
            
            # Skip test files (optional - user said no tests for now)
            # if "test" in py_file.name.lower():
            #     continue
            
            python_files.append(py_file)
        
        return sorted(python_files)
    
    async def _check_knowledge_base_exists(self) -> bool:
        """Check if Knowledge Base exists."""
        cypher = """
        MATCH (kb:KnowledgeBase {id: $kb_id})
        RETURN kb
        """
        
        try:
            results, _ = await self.client.query(cypher, {"kb_id": self.kb_id})
            return len(results) > 0
        except Exception as e:
            print(f"    [ERROR] Failed to check KB: {e}")
            return False
    
    async def _check_code_file_count(self) -> int:
        """Check how many CodeFile nodes exist."""
        cypher = """
        MATCH (kb:KnowledgeBase {id: $kb_id})<-[:IN_BASE]-(cf:CodeFile)
        RETURN count(cf) as file_count
        """
        
        try:
            results, _ = await self.client.query(cypher, {"kb_id": self.kb_id})
            file_count = results[0].get("file_count", 0) if results else 0
            return file_count
        except Exception as e:
            print(f"    [ERROR] Failed to check code file count: {e}")
            return 0
    
    async def _clear_code_nodes(self):
        """Clear existing code nodes (for force reload)."""
        cypher = """
        MATCH (kb:KnowledgeBase {id: $kb_id})<-[:IN_BASE]-(cf:CodeFile)
        OPTIONAL MATCH (cf)<-[:IN_FILE]-(f:Function)
        DETACH DELETE cf, f
        """
        
        try:
            await self.client.query(cypher, {"kb_id": self.kb_id})
            print("    [OK] Cleared existing code nodes")
        except Exception as e:
            print(f"    [ERROR] Failed to clear code nodes: {e}")
            raise
    
    async def _index_file(self, file_path: Path):
        """Index single Python file."""
        try:
            # Read file content
            content = file_path.read_text(encoding="utf-8")
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            lines_count = len(content.splitlines())
            
            # Calculate relative path
            if str(file_path).startswith("/app/"):
                # Container path
                rel_path = str(file_path.relative_to(Path("/app")))
            else:
                # Local path
                rel_path = str(file_path.relative_to(self.codebase_path.parent))
            
            # Normalize path separators
            rel_path = rel_path.replace("\\", "/")
            
            print(f"    Size: {len(content)} bytes, {lines_count} lines")
            
            # Parse AST
            try:
                tree = ast.parse(content, filename=str(file_path))
            except SyntaxError as e:
                print(f"    [WARNING] Syntax error: {e}")
                self.stats["errors"].append(f"Syntax error in {rel_path}: {e}")
                return
            
            # Create CodeFile node
            file_id = await self._create_code_file_node(
                file_path=rel_path,
                content_hash=content_hash,
                lines_count=lines_count
            )
            
            # Extract and create Function nodes
            functions = self._extract_functions(tree, content)
            print(f"    Functions: {len(functions)}")
            
            for func in functions:
                await self._create_function_node(
                    file_id=file_id,
                    function_info=func
                )
            
            self.stats["files_indexed"] += 1
            self.stats["functions_indexed"] += len(functions)
            
            print(f"    [OK] Indexed successfully")
            
        except Exception as e:
            error_msg = f"Failed to index {file_path}: {e}"
            print(f"    [ERROR] {error_msg}")
            self.stats["errors"].append(error_msg)
    
    async def _create_code_file_node(self, file_path: str, content_hash: str, lines_count: int) -> str:
        """Create CodeFile node in graph."""
        file_id = f"codefile_{content_hash[:16]}"
        
        cypher = """
        MATCH (kb:KnowledgeBase {id: $kb_id})
        MERGE (cf:CodeFile {id: $id})
        ON CREATE SET
          cf.path = $path,
          cf.language = 'python',
          cf.lines_count = $lines_count,
          cf.content_hash = $content_hash,
          cf.valid_at = $timestamp,
          cf.invalid_at = NULL,
          cf.last_modified = $timestamp
        ON MATCH SET
          cf.lines_count = $lines_count,
          cf.content_hash = $content_hash,
          cf.last_modified = $timestamp,
          cf.invalid_at = NULL
        MERGE (cf)-[:IN_BASE]->(kb)
        RETURN cf.id as id
        """
        
        params = {
            "kb_id": self.kb_id,
            "id": file_id,
            "path": file_path,
            "lines_count": lines_count,
            "content_hash": content_hash,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            results, _ = await self.client.query(cypher, params)
            return results[0]["id"] if results else file_id
        except Exception as e:
            raise Exception(f"Failed to create code file node: {e}")
    
    def _extract_functions(self, tree: ast.AST, source_code: str) -> List[Dict]:
        """Extract function definitions from AST."""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = self._parse_function(node, source_code)
                if func_info:
                    functions.append(func_info)
        
        return functions
    
    def _parse_function(self, node: ast.FunctionDef, source_code: str) -> Optional[Dict]:
        """Parse function node into structured info."""
        try:
            # Get function source code
            func_source = None
            if hasattr(ast, 'get_source_segment'):
                func_source = ast.get_source_segment(source_code, node)
            
            # Fallback: extract manually if get_source_segment not available
            if not func_source:
                lines = source_code.splitlines()
                start_line = node.lineno - 1  # 0-indexed
                end_line = node.end_lineno if node.end_lineno else node.lineno
                func_source = "\n".join(lines[start_line:end_line])
            
            if not func_source:
                return None
            
            # Build signature
            args = []
            for arg in node.args.args:
                arg_name = arg.arg
                # Try to get annotation
                if arg.annotation:
                    try:
                        annotation = ast.unparse(arg.annotation) if hasattr(ast, 'unparse') else None
                        if annotation:
                            arg_name += f": {annotation}"
                    except:
                        pass
                args.append(arg_name)
            
            signature = f"def {node.name}({', '.join(args)})"
            
            # Get return type annotation
            return_type = None
            if node.returns:
                try:
                    return_type = ast.unparse(node.returns) if hasattr(ast, 'unparse') else None
                except:
                    pass
            
            # Check if async
            is_async = isinstance(node, ast.AsyncFunctionDef)
            if is_async:
                signature = f"async {signature}"
            
            # Get docstring
            docstring = ast.get_docstring(node)
            
            return {
                "name": node.name,
                "signature": signature,
                "source_code": func_source,
                "start_line": node.lineno,
                "end_line": node.end_lineno or node.lineno,
                "is_async": is_async,
                "parameters": [arg.arg for arg in node.args.args],
                "return_type": return_type,
                "docstring": docstring
            }
        except Exception as e:
            print(f"      [WARNING] Failed to parse function {node.name}: {e}")
            return None
    
    async def _create_function_node(self, file_id: str, function_info: Dict):
        """Create Function node in graph."""
        func_id = f"func_{hashlib.sha256(function_info['source_code'].encode()).hexdigest()[:16]}"
        
        cypher = """
        MATCH (cf:CodeFile {id: $file_id})
        MERGE (f:Function {id: $id})
        ON CREATE SET
          f.name = $name,
          f.signature = $signature,
          f.source_code = $source_code,
          f.start_line = $start_line,
          f.end_line = $end_line,
          f.is_async = $is_async,
          f.parameters = $parameters,
          f.return_type = $return_type,
          f.docstring = $docstring,
          f.valid_at = $timestamp,
          f.invalid_at = NULL,
          f.status = 'pending_vectorization'
        ON MATCH SET
          f.signature = $signature,
          f.source_code = $source_code,
          f.start_line = $start_line,
          f.end_line = $end_line,
          f.is_async = $is_async,
          f.parameters = $parameters,
          f.return_type = $return_type,
          f.docstring = $docstring,
          f.invalid_at = NULL
        MERGE (f)-[:IN_FILE {start_line: $start_line, end_line: $end_line}]->(cf)
        RETURN f.id as id
        """
        
        params = {
            "file_id": file_id,
            "id": func_id,
            "name": function_info["name"],
            "signature": function_info["signature"],
            "source_code": function_info["source_code"],
            "start_line": function_info["start_line"],
            "end_line": function_info["end_line"],
            "is_async": function_info.get("is_async", False),
            "parameters": function_info.get("parameters", []),
            "return_type": function_info.get("return_type"),
            "docstring": function_info.get("docstring"),
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            await self.client.query(cypher, params)
        except Exception as e:
            raise Exception(f"Failed to create function node: {e}")
    
    def _print_summary(self):
        """Print indexing summary."""
        print("\n" + "=" * 60)
        print("[*] INDEXING SUMMARY")
        print("=" * 60)
        print(f"Files indexed:     {self.stats['files_indexed']}")
        print(f"Functions indexed: {self.stats['functions_indexed']}")
        print(f"Errors:            {len(self.stats['errors'])}")
        
        if self.stats["errors"]:
            print("\nErrors:")
            for error in self.stats["errors"][:10]:  # Show first 10
                print(f"  - {error}")
            if len(self.stats["errors"]) > 10:
                print(f"  ... and {len(self.stats['errors']) - 10} more")
        
        print("=" * 60)


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Index Python codebase into Knowledge Base")
    parser.add_argument(
        "--force-reload",
        action="store_true",
        help="Clear existing code nodes and reindex"
    )
    parser.add_argument(
        "--codebase-path",
        type=str,
        default="backend/app",
        help="Path to codebase directory (default: backend/app)"
    )
    
    args = parser.parse_args()
    
    indexer = CodebaseIndexer(codebase_path=args.codebase_path)
    success = await indexer.index_all(force_reload=args.force_reload)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())

