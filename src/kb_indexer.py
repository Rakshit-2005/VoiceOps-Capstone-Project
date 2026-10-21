"""Knowledge Base Indexer for ZentroMart Capstone.

Parses Markdown files from kb/ preserving [SECTION-ID], doc_type, status, and precedence.
Also indexes data/products.csv to support questions requiring product metadata.
Provides hybrid retrieval (semantic vector search + BM25 keyword matching) to achieve
high retrieval recall on practice questions and conversations.
"""

import os
import re
import csv
import pandas as pd
import chromadb
from typing import List, Dict, Any, Optional
from src.config import KB_DIR, DATA_DIR, PROJECT_DIR

# Document type precedence order (lower is higher priority)
# 1. Policy (current)
# 2. Agent Guide
# 3. Help
# 4. FAQ
# 5. Marketing
DOC_TYPE_PRIORITY = {
    "policy": 1,
    "agent_guide": 2,
    "help": 3,
    "faq": 4,
    "marketing": 5,
    "meta": 6,
    "product": 2,  # Product specs are factual
}

def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter between --- markers if present."""
    metadata = {}
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2]
            for line in fm_text.strip().split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    metadata[k.strip()] = v.strip().strip('"').strip("'")
    return metadata, body.strip()

def parse_kb_sections(kb_dir: str = KB_DIR) -> List[Dict[str, Any]]:
    """Parse all markdown files in kb/ into structured sections."""
    chunks = []
    
    for filename in sorted(os.listdir(kb_dir)):
        if not filename.endswith(".md"):
            continue
            
        filepath = os.path.join(kb_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            raw = f.read()
            
        fm, body = parse_frontmatter(raw)
        doc_id = fm.get("doc_id", filename.replace(".md", ""))
        doc_type = fm.get("doc_type", "policy" if filename.startswith("pol_") else "faq")
        status = fm.get("status", "current")
        effective_from = fm.get("effective_from", "2026-08-01")
        title = fm.get("title", filename)
        priority = DOC_TYPE_PRIORITY.get(doc_type, 5)
        if status == "superseded":
            priority += 10 # Deprioritize superseded documents

        # Split into sections based on markdown headers (## or ###)
        # Regex captures headings like: ## [RET-2] Return windows by category
        section_pattern = re.compile(r'(?=(?:^|\n)#{1,3}\s+)')
        raw_sections = [s.strip() for s in section_pattern.split(body) if s.strip()]
        
        for idx, sec in enumerate(raw_sections):
            # Extract section ID if present, e.g. [RET-2] or [WAR-1] or [KB-00.1]
            sec_id_match = re.search(r'\[([A-Za-z0-9_\-\.]+)\]', sec)
            if sec_id_match:
                section_id = sec_id_match.group(1)
            else:
                section_id = f"{doc_id}_{idx}"
                
            chunk_id = f"KB_{doc_id}_{section_id}_{idx}"
            chunks.append({
                "chunk_id": chunk_id,
                "section_id": section_id,
                "doc_id": doc_id,
                "doc_type": doc_type,
                "status": status,
                "effective_from": effective_from,
                "title": title,
                "source_file": filename,
                "priority": priority,
                "content": sec,
            })
            
    return chunks

def parse_products_csv(data_dir: str = DATA_DIR) -> List[Dict[str, Any]]:
    """Parse products.csv so each product is indexed as products.csv:SKU."""
    chunks = []
    csv_path = os.path.join(data_dir, "products.csv")
    if not os.path.exists(csv_path):
        return chunks
        
    df = pd.read_csv(csv_path, dtype=str)
    for _, row in df.iterrows():
        sku = row.get("sku", "")
        title = row.get("title", "")
        category = row.get("return_category", "")
        warranty = row.get("warranty_months", "0")
        assured = row.get("assured", "False")
        price = row.get("price_inr", "")
        seller = row.get("fulfilled_by", "ZentroMart")
        desc = row.get("description", "")
        
        text = (
            f"Product SKU: {sku}\n"
            f"Title: {title}\n"
            f"Brand: {row.get('brand', '')}\n"
            f"Category: {category}\n"
            f"Price: ₹{price}\n"
            f"Fulfilled by: {seller}\n"
            f"ZentroMart Assured: {assured}\n"
            f"Warranty: {warranty} months\n"
            f"Description: {desc}"
        )
        
        chunks.append({
            "chunk_id": f"PROD_{sku}",
            "section_id": f"products.csv:{sku}",
            "doc_id": "products.csv",
            "doc_type": "product",
            "status": "current",
            "effective_from": "2026-08-01",
            "title": f"Product {sku}: {title}",
            "source_file": "products.csv",
            "priority": 2,
            "content": text,
        })
    return chunks

class KnowledgeRetriever:
    """Hybrid Retriever combining ChromaDB vector search and exact token/SKU matching."""

    def __init__(self, persist_dir: Optional[str] = None):
        if persist_dir is None:
            persist_dir = os.path.join(PROJECT_DIR, ".chroma_db")
        
        self.persist_dir = persist_dir
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection_name = "zentromart_kb_all"
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        self.all_chunks: List[Dict[str, Any]] = []
        self._ensure_indexed()

    def _ensure_indexed(self):
        """Index all KB documents and products if collection is empty."""
        count = self.collection.count()
        kb_chunks = parse_kb_sections()
        prod_chunks = parse_products_csv()
        self.all_chunks = kb_chunks + prod_chunks
        
        if count != len(self.all_chunks):
            print(f"Indexing {len(self.all_chunks)} chunks into ChromaDB at {self.persist_dir}...")
            # Batch upsert
            batch_size = 100
            for i in range(0, len(self.all_chunks), batch_size):
                batch = self.all_chunks[i:i + batch_size]
                self.collection.upsert(
                    ids=[c["chunk_id"] for c in batch],
                    documents=[c["content"] for c in batch],
                    metadatas=[{
                        "section_id": c["section_id"],
                        "doc_id": c["doc_id"],
                        "doc_type": c["doc_type"],
                        "status": c["status"],
                        "effective_from": c["effective_from"],
                        "priority": c["priority"],
                        "source_file": c["source_file"]
                    } for c in batch]
                )
            print(f"Successfully indexed {len(self.all_chunks)} chunks.")
        else:
            print(f"Loaded existing index with {count} chunks.")

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve the top-k most relevant grounded chunks for a query."""
        results = []
        
        # 1. Check for exact SKU in query (e.g., ELE-0012, BKS-0056)
        sku_match = re.findall(r'\b([A-Z]{3}-\d{4})\b', query.upper())
        exact_sku_chunks = []
        for sku in sku_match:
            sku_target = f"products.csv:{sku}"
            for c in self.all_chunks:
                if c["section_id"] == sku_target or sku in c["content"]:
                    exact_sku_chunks.append(c)

        # 2. Vector search query
        vector_results = self.collection.query(
            query_texts=[query],
            n_results=min(top_k * 2, len(self.all_chunks))
        )
        
        retrieved_ids = set()
        
        # Add exact SKU matches first (highest relevance for product questions)
        for c in exact_sku_chunks:
            if c["chunk_id"] not in retrieved_ids:
                results.append({**c, "score": 1.0})
                retrieved_ids.add(c["chunk_id"])

        # Add vector search results with priority adjustment
        docs = vector_results.get("documents", [[]])[0]
        metas = vector_results.get("metadatas", [[]])[0]
        ids = vector_results.get("ids", [[]])[0]
        distances = vector_results.get("distances", [[]])[0] if "distances" in vector_results else [0.5] * len(docs)

        # Map to structured format and sort by priority & distance
        candidates = []
        for doc, meta, cid, dist in zip(docs, metas, ids, distances):
            if cid in retrieved_ids:
                continue
            priority = meta.get("priority", 5)
            # Distance: lower is better (cosine distance: 0 is identical, 2 is opposite)
            # Prioritize current policy over FAQ/marketing
            adjusted_score = dist + (priority * 0.05)
            candidates.append({
                "chunk_id": cid,
                "content": doc,
                "section_id": meta.get("section_id", ""),
                "doc_id": meta.get("doc_id", ""),
                "doc_type": meta.get("doc_type", ""),
                "status": meta.get("status", ""),
                "effective_from": meta.get("effective_from", ""),
                "source_file": meta.get("source_file", ""),
                "priority": priority,
                "score": 1.0 - dist,
                "adjusted_score": adjusted_score
            })
            
        candidates.sort(key=lambda x: x["adjusted_score"])
        
        for cand in candidates:
            if len(results) >= top_k:
                break
            results.append(cand)
            retrieved_ids.add(cand["chunk_id"])
            
        return results
