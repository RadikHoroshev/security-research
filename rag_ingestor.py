#!/usr/bin/env python3
"""
rag_ingestor.py — Auto-ingestion of KB files into ChromaDB

Принцип:
  1. Мониторит knowledge_base/ на новые/изменённые .md и .json файлы
  2. Читает файл, извлекает YAML front-matter (если есть)
  3. Добавляет/обновляет документ в ChromaDB
  4. Метаданные: type, file, updated, age_days, source
  
Использование:
  python3 intel/rag_ingestor.py --ingest     # Ингестить все KB
  python3 intel/rag_ingestor.py --watch      # Фоновый мониторинг
  python3 intel/rag_ingestor.py --query "запрос"  # Поиск
  python3 intel/rag_ingestor.py --query "запрос" --fresh  # Только свежие (7 дней)
"""

import chromadb
import yaml
import re
import os
import json
import time
import hashlib
import argparse
from pathlib import Path
from datetime import datetime

KB_DIR = Path(__file__).parent.parent / "knowledge_base"
SESSION_LOGS = Path(__file__).parent / "session_logs"
RESULTS = Path(__file__).parent / "results"
INTEL_DIR = Path(__file__).parent
ALL_DIRS = [KB_DIR, SESSION_LOGS, RESULTS, INTEL_DIR]
CHROMA_PATH = str(Path(__file__).parent.parent / "var" / "chromadb")
COLLECTION = "knowledge_base"

def get_client():
    return chromadb.PersistentClient(path=CHROMA_PATH)

def parse_frontmatter(content):
    """Extract YAML front-matter if present."""
    match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
    if match:
        try:
            meta = yaml.safe_load(match.group(1))
            return meta or {}, match.group(2).strip()
        except:
            pass
    return {}, content.strip()

def file_age_days(filepath):
    mtime = Path(filepath).stat().st_mtime
    age = (time.time() - mtime) / 86400
    return int(age)

def ingest_file(filepath, collection=None):
    """Ingest a single file into ChromaDB."""
    if collection is None:
        collection = get_client().get_or_create_collection(COLLECTION)
    
    filepath = Path(filepath)
    ext = filepath.suffix
    content = filepath.read_text(encoding='utf-8', errors='replace')
    
    # Parse front-matter for .md files
    frontmatter = {}
    if ext == '.md':
        frontmatter, content = parse_frontmatter(content)
    
    # For .json files, store the full JSON as content
    if ext == '.json':
        try:
            data = json.loads(content)
            content = json.dumps(data, indent=2)
        except:
            pass
    
    # Generate metadata
    mtime = filepath.stat().st_mtime
    updated = frontmatter.get('updated', datetime.utcfromtimestamp(mtime).strftime('%Y-%m-%d'))
    # Convert date objects to strings for ChromaDB
    if hasattr(updated, "isoformat"): updated = updated.isoformat()
    
    # Generate stable ID from file path
    doc_id = hashlib.md5(str(filepath).encode()).hexdigest()[:16]
    
    collection.upsert(
        documents=[content[:65000]],  # ChromaDB limit ~40K tokens
        metadatas=[{
            'type': ext.lstrip('.'),
            'file': str(filepath.relative_to(KB_DIR.parent.parent)),
            'filename': filepath.name,
            'updated': updated,
            'age_days': file_age_days(filepath),
            'source': frontmatter.get('source', 'knowledge_base'),
            'version': str(frontmatter.get('version', '')),
        }],
        ids=[doc_id]
    )
    return filepath.name

def ingest_all_kb():
    """Ingest all .md and .json files from ALL directories."""
    collection = get_client().get_or_create_collection(COLLECTION)
    count = 0
    errors = 0

    for ext in ['*.md', '*.json']:
        for dir_path in ALL_DIRS:
            if not dir_path.exists():
                continue
            for filepath in sorted(dir_path.rglob(ext)):
                # Skip binary/cache dirs
                if any(skip in str(filepath) for skip in ['__pycache__', '.git', 'node_modules', '.venv']):
                    continue
                try:
                    name = ingest_file(filepath, collection)
                    count += 1
                    print(f"  ✅ {name}")
                except Exception as e:
                    errors += 1
                    print(f"  ❌ {filepath.name}: {str(e)[:80]}")

    print(f"\n📊 Ingested: {count} files, {errors} errors")
    print(f"📈 Total in ChromaDB: {collection.count()} documents")
    return count

def query(text, fresh_only=False, n_results=5):
    """Query the knowledge base."""
    collection = get_client().get_or_create_collection(COLLECTION)
    
    where = {'age_days': {'$lte': 7}} if fresh_only else None
    
    results = collection.query(
        query_texts=[text],
        n_results=n_results,
        where=where
    )
    
    print(f"\n🔍 Query: \"{text}\"{' (fresh only)' if fresh_only else ''}")
    print(f"   Found: {len(results['documents'][0])} results\n")
    
    for i, doc in enumerate(results['documents'][0]):
        meta = results['metadatas'][0][i]
        dist = results['distances'][0][i] if results.get('distances') else 0
        updated = meta.get('updated', '?')
        ftype = meta.get('type', '?')
        filename = meta.get('filename', '?')
        
        print(f"  [{updated}] {filename} ({ftype}, dist={dist:.3f})")
        preview = doc[:200].replace('\n', ' ')
        print(f"    {preview}...")
        print()

def watch(interval=30):
    """Watch KB directory for changes."""
    print(f"👀 Watching {KB_DIR} for changes (every {interval}s)...")
    known_files = {}
    
    # Initial scan
    for ext in ['*.md', '*.json']:
        for f in KB_DIR.rglob(ext):
            known_files[str(f)] = f.stat().st_mtime
    
    while True:
        changed = []
        for ext in ['*.md', '*.json']:
            for filepath in KB_DIR.rglob(ext):
                if '__pycache__' in str(filepath) or '.git' in str(filepath):
                    continue
                key = str(filepath)
                mtime = filepath.stat().st_mtime
                if key not in known_files or known_files[key] != mtime:
                    changed.append(filepath)
                    known_files[key] = mtime
        
        for filepath in changed:
            print(f"  🔄 Changed: {filepath.relative_to(KB_DIR.parent.parent)}")
            try:
                ingest_file(filepath)
                print(f"     ✅ Indexed")
            except Exception as e:
                print(f"     ❌ {str(e)[:80]}")
        
        time.sleep(interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG Ingestor — ChromaDB auto-ingestion")
    parser.add_argument("--ingest", action="store_true", help="Ingest all KB files")
    parser.add_argument("--watch", action="store_true", help="Watch for changes")
    parser.add_argument("--watch-interval", type=int, default=30, help="Watch interval (seconds)")
    parser.add_argument("--query", type=str, help="Search query")
    parser.add_argument("--fresh", action="store_true", help="Only fresh documents (7 days)")
    parser.add_argument("--count", action="store_true", help="Show document count")
    args = parser.parse_args()
    
    if args.ingest:
        ingest_all_kb()
    elif args.watch:
        watch(args.watch_interval)
    elif args.query:
        query(args.query, fresh_only=args.fresh)
    elif args.count:
        c = get_client().get_or_create_collection(COLLECTION)
        print(f"📈 ChromaDB documents: {c.count()}")
    else:
        print("Usage:")
        print("  python3 rag_ingestor.py --ingest          # Ingest all KB")
        print("  python3 rag_ingestor.py --watch             # Watch for changes")
        print("  python3 rag_ingestor.py --query 'запрос'    # Search")
        print("  python3 rag_ingestor.py --query 'запрос' --fresh  # Fresh only")
        print("  python3 rag_ingestor.py --count             # Document count")
