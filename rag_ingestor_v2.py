#!/Users/code/.pyenv/versions/3.11.9/bin/python3
"""
rag_ingestor_v2.py — Smart auto-ingestion with categorization, versioning, and change detection

Architecture:
  - Separate ChromaDB collections per category (not one big pile)
  - File-to-category mapping based on folder structure
  - Full metadata: created, modified, ingested, version, checksum, source_agent
  - Change detection via SHA256 — only re-index when content actually changed
  - Background watcher for auto-ingestion
  - Validation: warns if file is in wrong folder for its type

Collections:
  - daily_logs     → session_logs/, agent activity logs
  - research       → vulnerability findings, target analysis
  - solutions      → fixes, workarounds, lessons learned, technology reviews
  - workflows      → protocols, procedures, file structures, agent guidelines
  - errors         → error logs, troubleshooting, failed attempts
  - reports        → huntr reports, PoC scripts, submission details
  - reference      → architecture docs, agent passports, system docs

Usage:
  python3 rag_ingestor_v2.py --ingest          # Ingest all, categorize, version
  python3 rag_ingestor_v2.py --watch            # Background daemon (auto-ingest on change)
  python3 rag_ingestor_v2.py --query "llama_index MCP"  # Search across all collections
  python3 rag_ingestor_v2.py --query "RCE" --collection reports  # Search specific collection
  python3 rag_ingestor_v2.py --status           # Show collection stats
  python3 rag_ingestor_v2.py --validate         # Check files in wrong folders
"""

import chromadb
import yaml
import re
import os
import json
import time
import hashlib
import argparse
import signal
from pathlib import Path
from datetime import datetime
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent
CHROMA_PATH = str(PROJECT_ROOT / "var" / "chromadb")

# ============================================================
# CATEGORY MAPPING: folder → (collection, subcategory)
# ============================================================
CATEGORY_MAP = {
    # knowledge_base subdirs
    "knowledge_base/workflows":         ("workflows", "protocol"),
    "knowledge_base/research":          ("research", "finding"),
    "knowledge_base/troubleshooting":   ("errors", "troubleshooting"),
    "knowledge_base/agent_logs":        ("daily_logs", "agent_activity"),
    "knowledge_base/architecture":      ("reference", "architecture"),
    "knowledge_base/reference":         ("reference", "documentation"),

    # intel subdirs
    "intel/session_logs":              ("daily_logs", "session"),
    "intel/results":                   ("reports", "result"),
    "intel":                           ("research", "analysis"),  # catch-all for intel root
}

# Reverse mapping: expected folder for each category
EXPECTED_FOLDERS = {
    "daily_logs": ["intel/session_logs", "knowledge_base/agent_logs"],
    "research":   ["knowledge_base/research", "intel"],
    "solutions":  ["knowledge_base/workflows"],
    "workflows":  ["knowledge_base/workflows"],
    "errors":     ["knowledge_base/troubleshooting"],
    "reports":    ["intel/results"],
    "reference":  ["knowledge_base/reference", "knowledge_base/architecture"],
}

# File extensions to index
INDEXABLE_EXTS = {'.md', '.json', '.py', '.yaml', '.yml', '.txt', '.toml'}

# ============================================================
# ChromaDB Client
# ============================================================
def get_client():
    return chromadb.PersistentClient(path=CHROMA_PATH)

def get_or_create_collection(name: str):
    """Get or create a ChromaDB collection with proper embedding config."""
    client = get_client()
    # Try to get existing, create if not
    collections = client.list_collections()
    for c in collections:
        if c.name == name:
            return client.get_collection(name)
    return client.create_collection(name)

ALL_COLLECTIONS = ["daily_logs", "research", "solutions", "workflows", "errors", "reports", "reference"]

# ============================================================
# File Analysis
# ============================================================
def compute_checksum(filepath: Path) -> str:
    """SHA256 checksum of file content."""
    h = hashlib.sha256()
    h.update(filepath.read_bytes())
    return h.hexdigest()

def detect_category(filepath: Path) -> tuple[str, str]:
    """Detect category and subcategory based on file path."""
    rel_path = str(filepath.relative_to(PROJECT_ROOT))

    # Try exact folder match first
    for folder_prefix, (collection, subcategory) in CATEGORY_MAP.items():
        if rel_path.startswith(folder_prefix):
            return collection, subcategory

    # Fallback: infer from filename patterns
    name = filepath.name.lower()
    if 'poc' in name or 'exploit' in name:
        return "reports", "poc"
    if 'report' in name or 'submission' in name:
        return "reports", "report"
    if 'error' in name or 'troubleshoot' in name:
        return "errors", "error_log"
    if 'log' in name or 'session' in name or 'activity' in name:
        return "daily_logs", "session"
    if 'protocol' in name or 'procedure' in name:
        return "workflows", "protocol"
    if 'research' in name or 'analysis' in name or 'scan' in name:
        return "research", "analysis"

    # Default fallback
    return "reference", "misc"

def validate_file_placement(filepath: Path, collection: str) -> list[str]:
    """Check if file is in the expected folder for its category."""
    warnings = []
    rel_path = str(filepath.relative_to(PROJECT_ROOT))
    expected = EXPECTED_FOLDERS.get(collection, [])
    if expected and not any(rel_path.startswith(f) for f in expected):
        warnings.append(
            f"⚠️  File in wrong folder for category '{collection}':\n"
            f"     Found: {rel_path}\n"
            f"     Expected in: {', '.join(expected)}"
        )
    return warnings

def extract_metadata(filepath: Path, collection: str, subcategory: str, version: int, checksum: str) -> dict:
    """Extract full metadata for a document."""
    stat = filepath.stat()
    created = datetime.fromtimestamp(stat.st_ctime).isoformat()
    modified = datetime.fromtimestamp(stat.st_mtime).isoformat()
    now = datetime.now().isoformat()

    # Try to extract YAML front-matter
    content = filepath.read_text(errors='ignore')
    frontmatter = {}
    m = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if m:
        try:
            frontmatter = yaml.safe_load(m.group(1)) or {}
        except:
            pass

    # Try to detect source agent from filename or content
    source_agent = frontmatter.get('agent', 'unknown')
    if not source_agent or source_agent == 'unknown':
        name = filepath.name.lower()
        for agent in ['qwen', 'gemini', 'claude', 'copilot', 'codex', 'jules', 'oz']:
            if agent in name or agent in content[:500].lower():
                source_agent = agent
                break

    # Try to detect target from filename or content
    target = frontmatter.get('target', '')
    if not target:
        for kw in ['llama_index', 'litellm', 'ollama', 'lollms', 'nltk', 'open-webui',
                    'xinference', 'transformers', 'huntr']:
            if kw in filepath.name.lower() or kw in content[:1000].lower():
                target = kw
                break

    # Try to detect status
    status = frontmatter.get('status', '')
    if not status:
        if 'submitted' in content[:500].lower():
            status = 'submitted'
        elif 'pending' in content[:500].lower():
            status = 'pending'
        elif 'confirmed' in content[:500].lower() or 'vulnerability confirmed' in content[:1000].lower():
            status = 'confirmed'
        elif 'failed' in content[:500].lower() or 'hallucination' in content[:500].lower():
            status = 'failed'

    return {
        # Identity
        'category': collection,
        'subcategory': subcategory,
        'file': str(filepath.relative_to(PROJECT_ROOT)),
        'filename': filepath.name,

        # Timestamps
        'created_date': created,
        'modified_date': modified,
        'ingested_date': now,
        'age_days': round((time.time() - stat.st_mtime) / 86400, 1),

        # Versioning
        'version': version,
        'checksum': checksum,

        # Semantic
        'source_agent': source_agent,
        'target': target,
        'status': status,

        # Front-matter passthrough
        'title': frontmatter.get('title', filepath.stem),
        'date': frontmatter.get('date', ''),
        'tags': json.dumps(frontmatter.get('tags', [])),
    }

# ============================================================
# Version Tracking
# ============================================================
def get_current_version(filepath: Path, collection) -> int:
    """Get current version of a file in the collection, or 0 if new."""
    checksum = compute_checksum(filepath)

    if collection.count() == 0:
        return 1, checksum, False

    # Search by filename
    results = collection.get(
        where={'filename': filepath.name},
        include=['metadatas']
    )

    if not results['metadatas']:
        return 1, checksum, False  # New file

    # Check if content changed
    existing = results['metadatas'][0]
    if existing.get('checksum') == checksum:
        return existing.get('version', 1), checksum, False  # No change

    # Content changed — new version
    return existing.get('version', 1) + 1, checksum, True  # Updated

# ============================================================
# Ingestion
# ============================================================
def ingest_file(filepath: Path) -> Optional[dict]:
    """Ingest a single file. Returns metadata if successful."""
    if filepath.suffix not in INDEXABLE_EXTS:
        return None
    if any(skip in str(filepath) for skip in ['__pycache__', '.git', 'node_modules', '.venv', 'var/']):
        return None

    # Determine category
    collection_name, subcategory = detect_category(filepath)
    collection = get_or_create_collection(collection_name)

    # Validate placement
    warnings = validate_file_placement(filepath, collection_name)

    # Get version
    version, checksum, is_update = get_current_version(filepath, collection)
    if not is_update and version > 1:
        return None  # Already indexed, no changes

    # Extract content
    content = filepath.read_text(errors='ignore')

    # Extract metadata
    metadata = extract_metadata(filepath, collection_name, subcategory, version, checksum)

    # Upsert into ChromaDB
    doc_id = hashlib.md5(str(filepath).encode()).hexdigest()
    collection.upsert(
        ids=[doc_id],
        documents=[content],
        metadatas=[metadata]
    )

    action = "UPDATED" if is_update else "NEW"
    print(f"  ✅ [{action} v{version}] {collection_name}/{subcategory}: {filepath.name}")
    for w in warnings:
        print(f"     {w}")

    return metadata

def ingest_all():
    """Ingest all indexable files from all tracked directories."""
    total = 0
    new_count = 0
    update_count = 0
    errors = 0
    warnings_list = []

    # Scan all directories
    dirs_to_scan = [
        PROJECT_ROOT / "knowledge_base",
        PROJECT_ROOT / "intel",
    ]

    for base_dir in dirs_to_scan:
        if not base_dir.exists():
            continue
        for ext in INDEXABLE_EXTS:
            for filepath in sorted(base_dir.rglob(f'*{ext}')):
                if any(skip in str(filepath) for skip in ['__pycache__', '.git', 'node_modules', '.venv', 'var/']):
                    continue
                try:
                    result = ingest_file(filepath)
                    if result:
                        total += 1
                        if result.get('version', 1) == 1:
                            new_count += 1
                        else:
                            update_count += 1
                except Exception as e:
                    errors += 1
                    print(f"  ❌ {filepath.name}: {str(e)[:80]}")

    print(f"\n📊 Total processed: {total} files")
    print(f"   🆕 New: {new_count}")
    print(f"   🔄 Updated: {update_count}")
    print(f"   ❌ Errors: {errors}")

    # Show collection stats
    print(f"\n📁 Collection sizes:")
    for cname in ALL_COLLECTIONS:
        try:
            c = get_or_create_collection(cname)
            print(f"   {cname}: {c.count()} docs")
        except:
            print(f"   {cname}: 0 docs")

    return total

# ============================================================
# Query
# ============================================================
def query(text: str, collection_name: Optional[str] = None, n_results: int = 5, fresh_only: bool = False):
    """Query across collections."""
    where = {'age_days': {'$lte': 7}} if fresh_only else None

    if collection_name:
        # Search specific collection
        collection = get_or_create_collection(collection_name)
        results = collection.query(query_texts=[text], n_results=n_results, where=where)
        _print_results(results, collection_name)
    else:
        # Search all collections
        for cname in ALL_COLLECTIONS:
            try:
                collection = get_or_create_collection(cname)
                results = collection.query(query_texts=[text], n_results=n_results, where=where)
                if results['documents'][0]:
                    _print_results(results, cname)
            except:
                pass

def _print_results(results, collection_name):
    docs = results['documents'][0]
    metas = results['metadatas'][0]
    if not docs:
        return
    print(f"\n🔍 [{collection_name}] Found {len(docs)} results:")
    for i, (doc, meta) in enumerate(zip(docs, metas)):
        print(f"  [{i+1}] {meta.get('filename', '?')} (v{meta.get('version', 1)}, {meta.get('age_days', '?')}d old)")
        print(f"      Agent: {meta.get('source_agent', '?')} | Target: {meta.get('target', '?')} | Status: {meta.get('status', '?')}")
        print(f"      {doc[:200]}...")

# ============================================================
# Validation
# ============================================================
def validate_all():
    """Check all files are in correct folders for their detected category."""
    warnings = []
    dirs_to_scan = [PROJECT_ROOT / "knowledge_base", PROJECT_ROOT / "intel"]
    for base_dir in dirs_to_scan:
        if not base_dir.exists():
            continue
        for ext in INDEXABLE_EXTS:
            for filepath in sorted(base_dir.rglob(f'*{ext}')):
                if any(skip in str(filepath) for skip in ['__pycache__', '.git', 'node_modules', '.venv', 'var/']):
                    continue
                collection_name, _ = detect_category(filepath)
                w = validate_file_placement(filepath, collection_name)
                warnings.extend(w)

    if warnings:
        print(f"⚠️  Found {len(warnings)} placement issues:")
        for w in warnings:
            print(f"  {w}")
    else:
        print("✅ All files are in correct folders for their categories")

# ============================================================
# Watcher (background daemon)
# ============================================================
def watch(interval: int = 60):
    """Watch for file changes and auto-ingest."""
    print(f"👁️  Watching for changes (every {interval}s)...")
    print(f"    Monitored: knowledge_base/, intel/")
    print(f"    Press Ctrl+C to stop\n")

    known_checksums = {}

    # Initialize known checksums
    dirs_to_scan = [PROJECT_ROOT / "knowledge_base", PROJECT_ROOT / "intel"]
    for base_dir in dirs_to_scan:
        if not base_dir.exists():
            continue
        for ext in INDEXABLE_EXTS:
            for filepath in base_dir.rglob(f'*{ext}'):
                if any(skip in str(filepath) for skip in ['__pycache__', '.git', 'node_modules', '.venv', 'var/']):
                    continue
                try:
                    known_checksums[str(filepath)] = compute_checksum(filepath)
                except:
                    pass

    last_check = time.time()
    while True:
        time.sleep(interval)
        changed = []

        # Check for new or modified files
        for base_dir in dirs_to_scan:
            if not base_dir.exists():
                continue
            for ext in INDEXABLE_EXTS:
                for filepath in base_dir.rglob(f'*{ext}'):
                    if any(skip in str(filepath) for skip in ['__pycache__', '.git', 'node_modules', '.venv', 'var/']):
                        continue
                    try:
                        cs = compute_checksum(filepath)
                        if str(filepath) not in known_checksums:
                            changed.append(('new', filepath))
                            known_checksums[str(filepath)] = cs
                        elif known_checksums[str(filepath)] != cs:
                            changed.append(('changed', filepath))
                            known_checksums[str(filepath)] = cs
                    except:
                        pass

        # Check for deleted files
        current_files = set()
        for base_dir in dirs_to_scan:
            if not base_dir.exists():
                continue
            for ext in INDEXABLE_EXTS:
                for filepath in base_dir.rglob(f'*{ext}'):
                    current_files.add(str(filepath))

        deleted = [f for f in known_checksums if f not in current_files]
        for f in deleted:
            print(f"  🗑️  Deleted: {Path(f).name}")
            del known_checksums[f]

        # Ingest changes
        if changed:
            now = datetime.now().strftime('%H:%M:%S')
            print(f"\n[{now}] Found {len(changed)} changes:")
            for change_type, filepath in changed:
                icon = "🆕" if change_type == 'new' else "🔄"
                print(f"  {icon} {change_type}: {filepath.name}")
                try:
                    ingest_file(filepath)
                except Exception as e:
                    print(f"  ❌ Error: {e}")

        last_check = time.time()

# ============================================================
# Status
# ============================================================
def show_status():
    """Show collection status and recent documents."""
    print("📊 ChromaDB Collections:")
    print(f"   Path: {CHROMA_PATH}")
    print()
    for cname in ALL_COLLECTIONS:
        try:
            c = get_or_create_collection(cname)
            count = c.count()
            # Get most recent
            recent = c.get(limit=1, include=['metadatas'])
            if recent['metadatas']:
                meta = recent['metadatas'][0]
                print(f"  📁 {cname}: {count} docs | Latest: {meta.get('filename', '?')} ({meta.get('ingested_date', '?')[:16]})")
            else:
                print(f"  📁 {cname}: {count} docs (empty)")
        except Exception as e:
            print(f"  📁 {cname}: error — {e}")

# ============================================================
# CLI
# ============================================================
def main():
    parser = argparse.ArgumentParser(description='RAG Ingestor v2 — Smart auto-indexing')
    parser.add_argument('--ingest', action='store_true', help='Ingest all files')
    parser.add_argument('--watch', action='store_true', help='Watch for changes (daemon)')
    parser.add_argument('--watch-interval', type=int, default=60, help='Watch interval in seconds')
    parser.add_argument('--query', type=str, help='Search query')
    parser.add_argument('--collection', type=str, help='Search specific collection')
    parser.add_argument('--fresh', action='store_true', help='Only fresh docs (7 days)')
    parser.add_argument('--n', type=int, default=5, help='Number of results')
    parser.add_argument('--validate', action='store_true', help='Validate file placement')
    parser.add_argument('--status', action='store_true', help='Show collection status')
    args = parser.parse_args()

    if args.ingest:
        ingest_all()
    elif args.watch:
        try:
            watch(args.watch_interval)
        except KeyboardInterrupt:
            print("\n👁️  Watcher stopped")
    elif args.query:
        query(args.query, args.collection, args.n, args.fresh)
    elif args.validate:
        validate_all()
    elif args.status:
        show_status()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
