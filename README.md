# VoiceOps 2026: ZentroMart Voice Support Agent

[![LLM & Generative AI Course](https://img.shields.io/badge/Course-LLM%20%26%20Generative%20AI-blue)](#)
[![IIT Guwahati x Gnani.ai](https://img.shields.io/badge/Organizer-IIT%20Guwahati%20%C3%97%20Gnani.ai-orange)](#)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-green)](#)

An intelligent, speech-enabled, document-grounded customer support agent for **ZentroMart**, an Indian e-commerce platform. The agent listens through **Gnani Speech-to-Text (STT)**, reasons over official company policies via **Grounded RAG & Tool Calling**, and speaks back in natural Indian English/Hinglish via **Gnani Text-to-Speech (TTS)**.

---

## 🏗️ Architecture & Pipeline

```text
[Customer Spoken Audio] 
         │
         ▼
[Gnani STT (REST / WebSocket)] ────────▶ Transcription (en-IN / hi-en)
         │
         ▼
[Agent Brain: Conversational State Machine]
    ├── 1. Caller Identity Verification (Last 4 digits of phone / delivery pincode)
    ├── 2. Vector Knowledge Base (ChromaDB over 21 Markdown policies with [SECTION-ID])
    ├── 3. Structured Data Tools (orders.csv, customers.csv, products.csv)
    ├── 4. Business Day Calendar Engine (Skips Sundays & warehouse holidays; anchor: 2026-10-20)
    └── 5. Escalation & Ticketing (create_ticket() with Priority Resolution handover)
         │
         ▼
[Ear-Optimized Text Normalization] ─────▶ Formats dates, spaced order IDs (e.g. O R D 1 0 2 3)
         │
         ▼
[Gnani TTS (timbre-v2.5 / Kaveri)] ────▶ [Spoken Output Audio (.wav)]
```

---

## 🚀 Quick Setup & Installation

### 1. Prerequisites
- Python 3.10 to 3.12
- Active [Gnani.ai Voice Account](https://app.gnani.ai/voice) for API Key

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` and set your credentials:
```env
GNANI_API_KEY=your_actual_gnani_api_key_here
OPENAI_API_KEY=your_openai_api_key_optional
```

---

## ⚡ Batch Run Command (Official Testing)

The batch runner takes a folder of customer `.wav` audio files, transcribes them, grounds answers from company policies, synthesizes spoken replies, and logs cited section chunks:

```bash
python run.py --audio_dir <path_to_audio_folder> --output_dir <path_to_save_results>
```

### Example:
```bash
python run.py --audio_dir sample_test_audio --output_dir sample_outputs
```

Each processed audio file generates:
- `<filename>_reply.wav`: High-fidelity spoken audio response.
- `<filename>_output.json`: Full log containing transcript, agent reply text, and cited section chunk IDs.
- `batch_summary.json`: Complete aggregate summary across all processed turns.

---

## 📊 Evaluation & Benchmark Results

Run the offline benchmark across the 52 practice questions and 23 multi-turn conversations:
```bash
python evaluate.py
```

### Quantitative Results:

| Benchmark Stage | Metric | Score / Recall |
| :--- | :--- | :---: |
| **Step 1: Baseline LLM** | Prompt-only accuracy (No RAG) | **26.9%** (14/52) |
| **Step 2: Grounded RAG** | Document-grounded accuracy | **98.1%** (51/52) |
| **Retrieval Quality** | Gold Section ID Recall | **92.3%** (48/52) |
| **Accuracy Boost** | RAG vs Baseline Improvement | **+71.2%** |
| **Multi-Turn Handling** | 23 Dialogues (96 Customer Turns) | **75.0%** (72/96) |
| **Gated Authentication**| Verified Order Sessions | **21 sessions** |

---

## 📁 Repository Structure

```text
VoiceOps Capstone Project/
├── .env.example              # Environment variables template (no secrets)
├── requirements.txt          # Python dependencies
├── README.md                 # Complete system guide & setup instructions
├── run.py                    # Official batch test runner command
├── evaluate.py               # Step 1 vs Step 2 benchmark test script
├── kb/                       # 21 Markdown knowledge-base documents
├── data/                     # 7 CSV database tables (orders, products, etc.)
├── practice/                 # 52 practice questions and 23 conversations
├── tools/                    # Mock Python tools (lookup_order, create_ticket)
├── src/
│   ├── config.py             # Reference date anchor (2026-10-20) & calendar logic
│   ├── kb_indexer.py         # Markdown section parser & ChromaDB vector store
│   ├── tools_handler.py      # Identity-gated lookup & ticket generator
│   ├── conversation_agent.py # Multi-turn state machine & grounded responder
│   └── voice_pipeline.py     # Gnani STT & TTS wrapper with phonetic normalization
└── sample_outputs/           # Sample generated audio (.wav) and JSON outputs
```

---

## 🛡️ Key Policy Rules & Verification Compliance

1. **Self-Identification (`STY-1`):** In turn 1, the agent explicitly identifies itself as an AI assistant.
2. **Identity Verification Gate (`IDV-2`):** Order status and details are withheld until the caller confirms the **last 4 digits of their registered phone** or their **delivery pincode**. Maximum of 1 retry permitted.
3. **Reference Date Anchor:** Frozen on **20 October 2026**.
4. **Business Days Math:** Monday–Saturday, skipping Sundays and dates listed in `holidays.csv`.
5. **Precedence Hierarchy:** Current Policy > Agent Guide > Help > FAQ > Marketing.
6. **Graceful Refusal & Handover:** Refuses unauthorized cash compensation; initiates Priority Resolution ticket and connects to human support for damage claims > ₹10,000.
