"""
Load .cursor/rules files into Knowledge Base (cursor_memory graph) - STANDALONE VERSION.

This version doesn't depend on app config, can be run directly.

Usage:
    python backend/scripts/load_rules_standalone.py [--force-reload] [--host localhost] [--port 6379]
"""

import asyncio
import json
import hashlib
import re
import os
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import sys

# Standalone imports
try:
    from falkordb import FalkorDB
    import time
except ImportError:
    print("[ERROR] FalkorDB not installed. Run: pip install falkordb")
    sys.exit(1)


class FalkorDBClientSimple:
    """Simplified FalkorDB client for standalone script."""
    
    def __init__(self, host: str, port: int, graph_name: str):
        self.host = host
        self.port = port
        self.graph_name = graph_name
        self._client = None
        self._graph = None
    
    async def connect(self):
        """Connect to FalkorDB."""
        loop = asyncio.get_event_loop()
        self._client = await loop.run_in_executor(
            None,
            lambda: FalkorDB(host=self.host, port=self.port)
        )
        self._graph = self._client.select_graph(self.graph_name)
        # Test connection
        await loop.run_in_executor(None, self._client.connection.ping)
    
    async def disconnect(self):
        """Disconnect from FalkorDB."""
        if self._client:
            try:
                # FalkorDB client doesn't have close() method
                # Connection will be closed automatically
                pass
            except Exception:
                pass
    
    async def query(self, cypher: str, params: dict = None):
        """Execute Cypher query."""
        loop = asyncio.get_event_loop()
        start = time.time()
        
        result = await loop.run_in_executor(
            None,
            lambda: self._graph.query(cypher, params or {})
        )
        
        exec_time = (time.time() - start) * 1000
        
        # Parse results
        results = []
        if result.result_set:
            for record in result.result_set:
                row_dict = {}
                for idx, col_name in enumerate(result.header):
                    if isinstance(col_name, list) and len(col_name) >= 2:
                        key = col_name[1]
                    else:
                        key = str(col_name)
                    row_dict[key] = record[idx]
                results.append(row_dict)
        
        return results, exec_time


class KnowledgeBaseLoader:
    """Load rules files into FalkorDB Knowledge Base."""
    
    def __init__(self, rules_path: str, host: str, port: int):
        self.rules_path = Path(rules_path)
        self.kb_id = "cursor_rules_v3"
        self.kb_version = "3.0.0"
        self.client: FalkorDBClientSimple | None = None
        self.host = host
        self.port = port
        self.stats = {
            "documents_created": 0,
            "chunks_created": 0,
            "errors": []
        }
    
    async def load_all(self, force_reload: bool = False):
        """Load all rule files into Knowledge Base."""
        print("[*] Knowledge Base Loader")
        print(f"    Target Graph: cursor_memory")
        print(f"    Host: {self.host}:{self.port}")
        print(f"    KB ID: {self.kb_id}\n")
        
        # Connect to FalkorDB
        print("[+] Connecting to FalkorDB...")
        self.client = FalkorDBClientSimple(
            host=self.host,
            port=self.port,
            graph_name="cursor_memory"
        )
        
        try:
            await self.client.connect()
            print("    [OK] Connected\n")
        except Exception as e:
            print(f"    [ERROR] Failed to connect: {e}")
            return False
        
        # Load manifest
        manifest = self._load_manifest()
        if not manifest:
            print("[!] No manifest found. Run validate_rules.py first.")
            await self.client.disconnect()
            return False
        
        print(f"[*] Found {len(manifest)} files to load\n")
        
        # Check/create KB
        if force_reload:
            print("[+] Force reload: clearing existing KB...")
            await self._clear_knowledge_base()
        
        kb_exists = await self._check_knowledge_base_exists()
        if kb_exists and not force_reload:
            print("[!] Knowledge Base already exists. Use --force-reload to overwrite.")
            await self.client.disconnect()
            return False
        
        if not kb_exists:
            print("[+] Creating KnowledgeBase root node...")
            await self._create_knowledge_base()
        
        # Load documents
        print(f"\n[+] Loading {len(manifest)} documents...")
        for idx, file_info in enumerate(manifest, 1):
            print(f"\n  [{idx}/{len(manifest)}] {file_info['relative_path']}")
            await self._load_document(file_info)
        
        # Summary
        self._print_summary()
        
        # Cleanup
        await self.client.disconnect()
        return len(self.stats["errors"]) == 0
    
    def _load_manifest(self) -> List[Dict]:
        """Load manifest generated by validate_rules.py"""
        manifest_path = Path("backend/scripts/rules_manifest.json")
        if not manifest_path.exists():
            return []
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    
    async def _check_knowledge_base_exists(self) -> bool:
        """Check if Knowledge Base exists."""
        cypher = "MATCH (kb:KnowledgeBase {id: $kb_id}) RETURN kb"
        try:
            results, _ = await self.client.query(cypher, {"kb_id": self.kb_id})
            exists = len(results) > 0
            print(f"    [{'EXISTS' if exists else 'NEW'}] Knowledge Base")
            return exists
        except Exception as e:
            print(f"    [ERROR] Failed to check KB: {e}")
            return False
    
    async def _create_knowledge_base(self):
        """Create KnowledgeBase root node."""
        cypher = """
        CREATE (kb:KnowledgeBase {
          id: $id,
          type: 'rules',
          version: $version,
          initialized_at: $timestamp,
          total_documents: 0,
          total_chunks: 0,
          status: 'loading'
        })
        RETURN kb.id as id
        """
        params = {
            "id": self.kb_id,
            "version": self.kb_version,
            "timestamp": datetime.now().isoformat()
        }
        await self.client.query(cypher, params)
        print("    [OK] Created KnowledgeBase node")
    
    async def _clear_knowledge_base(self):
        """Clear existing Knowledge Base."""
        cypher = """
        MATCH (kb:KnowledgeBase {id: $kb_id})
        OPTIONAL MATCH (kb)<-[:IN_BASE]-(d:Document)
        OPTIONAL MATCH (d)<-[:PART_OF]-(c:Chunk)
        DETACH DELETE kb, d, c
        """
        await self.client.query(cypher, {"kb_id": self.kb_id})
        print("    [OK] Cleared existing KB")
    
    async def _load_document(self, file_info: Dict):
        """Load single document with chunks."""
        try:
            # Read file
            file_path = Path(file_info["path"])
            content = file_path.read_text(encoding="utf-8")
            
            print(f"    Size: {len(content)} bytes")
            print(f"    Category: {file_info['category']}")
            
            # Create Document node
            doc_id = await self._create_document_node(file_info)
            
            # Chunk content
            chunks = self._chunk_content(content)
            print(f"    Chunks: {len(chunks)}")
            
            # Create Chunk nodes
            for chunk in chunks:
                await self._create_chunk_node(chunk, doc_id)
            
            self.stats["documents_created"] += 1
            self.stats["chunks_created"] += len(chunks)
            print(f"    [OK] Loaded successfully")
            
        except Exception as e:
            error_msg = f"Failed to load {file_info['path']}: {e}"
            print(f"    [ERROR] {error_msg}")
            self.stats["errors"].append(error_msg)
    
    async def _create_document_node(self, file_info: Dict) -> str:
        """Create Document node."""
        doc_id = f"doc_{file_info['content_hash'][:16]}"
        
        cypher = """
        MATCH (kb:KnowledgeBase {id: $kb_id})
        CREATE (d:Document {
          id: $id,
          path: $path,
          relative_path: $relative_path,
          type: 'rules',
          category: $category,
          content_hash: $content_hash,
          version: $version,
          size_bytes: $size_bytes,
          lines: $lines,
          loaded_at: $timestamp,
          status: 'active',
          chunk_count: 0
        })
        CREATE (d)-[:IN_BASE]->(kb)
        RETURN d.id as id
        """
        
        params = {
            "kb_id": self.kb_id,
            "id": doc_id,
            "path": str(file_info["path"]),
            "relative_path": file_info["relative_path"],
            "category": file_info["category"],
            "content_hash": file_info["content_hash"],
            "version": file_info["version"],
            "size_bytes": file_info["size_bytes"],
            "lines": file_info["lines"],
            "timestamp": datetime.now().isoformat()
        }
        
        results, _ = await self.client.query(cypher, params)
        return results[0]["id"] if results else doc_id
    
    def _chunk_content(self, content: str) -> List[Dict]:
        """Chunk content into semantic chunks."""
        chunks = []
        
        # Remove frontmatter
        content_clean = re.sub(r'^---\s*\n.*?\n---\s*\n', '', content, flags=re.DOTALL)
        
        # Split by paragraphs
        paragraphs = content_clean.split('\n\n')
        
        current_chunk = ""
        char_pos = 0
        chunk_idx = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Save current chunk if adding para exceeds limit
            if current_chunk and len(current_chunk) + len(para) > 800:
                chunks.append({
                    "content": current_chunk.strip(),
                    "position": chunk_idx,
                    "char_start": char_pos,
                    "char_end": char_pos + len(current_chunk),
                    "chunk_type": self._detect_chunk_type(current_chunk)
                })
                char_pos += len(current_chunk) + 2
                chunk_idx += 1
                current_chunk = ""
            
            current_chunk += para + "\n\n"
        
        # Add last chunk
        if current_chunk.strip():
            chunks.append({
                "content": current_chunk.strip(),
                "position": chunk_idx,
                "char_start": char_pos,
                "char_end": char_pos + len(current_chunk),
                "chunk_type": self._detect_chunk_type(current_chunk)
            })
        
        return chunks
    
    def _detect_chunk_type(self, text: str) -> str:
        """Detect chunk type."""
        text = text.strip()
        if text.startswith('#'):
            return "heading"
        elif text.startswith('```'):
            return "code"
        elif text.startswith(('-', '*')):
            return "list"
        elif len(text.split('\n')) == 1 and len(text) < 200:
            return "sentence"
        return "paragraph"
    
    async def _create_chunk_node(self, chunk: Dict, doc_id: str):
        """Create Chunk node."""
        chunk_id = f"chunk_{hashlib.sha256(chunk['content'].encode()).hexdigest()[:16]}"
        
        cypher = """
        MATCH (d:Document {id: $doc_id})
        CREATE (c:Chunk {
          id: $id,
          content: $content,
          position: $position,
          char_start: $char_start,
          char_end: $char_end,
          chunk_type: $chunk_type,
          status: 'pending_vectorization',
          created_at: $timestamp
        })
        CREATE (c)-[:PART_OF {position: $position}]->(d)
        RETURN c.id as id
        """
        
        params = {
            "doc_id": doc_id,
            "id": chunk_id,
            "content": chunk["content"][:4000],
            "position": chunk["position"],
            "char_start": chunk["char_start"],
            "char_end": chunk["char_end"],
            "chunk_type": chunk["chunk_type"],
            "timestamp": datetime.now().isoformat()
        }
        
        await self.client.query(cypher, params)
    
    def _print_summary(self):
        """Print loading summary."""
        print("\n" + "="*60)
        print("LOADING SUMMARY")
        print("="*60 + "\n")
        print(f"[*] Statistics:")
        print(f"    Documents created: {self.stats['documents_created']}")
        print(f"    Chunks created: {self.stats['chunks_created']}")
        print(f"    Errors: {len(self.stats['errors'])}")
        
        if self.stats["errors"]:
            print(f"\n[!] Errors:")
            for error in self.stats["errors"]:
                print(f"    - {error}")
        
        print("\n" + "="*60)
        
        if len(self.stats["errors"]) == 0:
            print("\n[SUCCESS] All files loaded successfully!")
            print("\n[*] Next steps:")
            print("    1. Async workers will process chunks (vectorization)")
            print("    2. Entity extraction will run")
            print("    3. Similarity links will be created")


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Load .cursor/rules into Knowledge Base")
    parser.add_argument("--force-reload", action="store_true", help="Clear existing KB and reload")
    parser.add_argument("--host", default="localhost", help="FalkorDB host")
    parser.add_argument("--port", type=int, default=6379, help="FalkorDB port")
    
    args = parser.parse_args()
    
    # Check manifest
    if not Path("backend/scripts/rules_manifest.json").exists():
        print("[!] Manifest not found. Run validate_rules.py first:")
        print("    python backend/scripts/validate_rules.py")
        return 1
    
    # Load
    loader = KnowledgeBaseLoader(".cursor/rules", args.host, args.port)
    success = await loader.load_all(force_reload=args.force_reload)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

