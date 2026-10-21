# VoiceOps 2026: Capstone Project Report
**Author:** Rakshit Modanwal  
**GitHub Repository:** [https://github.com/Rakshit-2005/VoiceOps-Capstone-Project](https://github.com/Rakshit-2005/VoiceOps-Capstone-Project)  
**Track:** VoiceOps 2026 · Consulting & Analytics Club, IIT Guwahati × Gnani.ai  
**Date:** October 2026  

---

## 1. Executive Summary & Problem Overview
ZentroMart is a fictional Indian e-commerce platform offering groceries and consumer electronics. The customer support operations face high volumes of repetitive inquiries covering late shipments, cancellation requests, reverse pickup timelines, and warranty terms. Given strong customer preference for telephony over text chat in the Indian market, this project introduces **VoiceOps**: an automated voice-first customer service agent. 

The agent operates across a 4-stage pipeline:
1. **Acoustic Perception:** Transcribes spoken customer audio via **Gnani Speech-to-Text (STT)** (`en-IN` / `hi-en`).
2. **Contextual Cognition:** Employs an LLM orchestrator with memory to sustain multi-turn conversational dialogue.
3. **Grounded Retrieval & Tools:** Queries a vector database of 21 markdown policies and executes gated order verification against relational CSV databases using `lookup_order` and `create_ticket`.
4. **Vocal Synthesis:** Converts normalized text back to Indian-accented speech using **Gnani Text-to-Speech (TTS)** (`timbre-v2.5` with voice `Kaveri`).

---

## 2. System Architecture & Implementation

### Step 1: Baseline Prompt-Only LLM (No Knowledge Base)
- **Role & Limits:** Formulates a persona for ZentroMart's support assistant, adhering to guideline `STY-1` (explicitly stating in the opening reply that the user is conversing with an AI assistant).
- **Behavior:** Operates strictly on pre-trained parametric knowledge without access to external documents. As demonstrated in benchmarking, the ungrounded agent frequently hallucinates generic 5–7 day banking timelines for wallet refunds and fails on SKU-specific warranty conditions.

### Step 2: Document Grounding via RAG (ChromaDB)
- **Document Precedence Hierarchy:** Follows `KB-00.1` priority: Policy documents (`status: current`) > Agent guides > Help articles > FAQs > Marketing. Superseded documents (e.g., `pol_returns_v3_superseded.md`) are deprioritized.
- **Chunking & Indexing:** Markdown documents are parsed by header sections while preserving section ID tags (e.g., `[RET-2]`, `[REF-2]`, `[WAR-1]`). Chunks are embedded and indexed into ChromaDB.
- **Product Metadata Indexing:** Rows from `products.csv` are indexed as standalone knowledge chunks (`products.csv:SKU`), enabling seamless joint retrieval of policy and product attributes.
- **Strict Grounding & Refusals:** When a query falls outside policy scope (e.g., midnight delivery, student discounts, bulk GST invoicing), the agent avoids speculative answers and triggers the standard fallback: *"Sorry, I don't have information about that. I can connect you to a colleague who can help."*

### Step 3: Multi-Turn Conversation & Gated Tool Execution
- **Caller Identity Verification (`IDV-2`):** Order status and sensitive delivery parameters are gated behind authentication. The agent prompts for the last 4 digits of the caller's registered phone number or their 6-digit delivery pincode, allowing at most 1 retry.
- **Coreference Resolution:** Tracks order context across turns (e.g., recognizing that *"Aur refund kitne din mein aayega?"* refers to the previously identified and verified item).
- **Calendar & Timeline Mathematics:** Accurately accounts for the frozen reference date (**20 October 2026**). Calculates refund arrival dates across business days (Monday–Saturday, omitting warehouse holidays from `holidays.csv`). Return windows use calendar days.
- **Escalation & Ticketing (`create_ticket`):** Out-of-policy compensation demands (e.g., demanding ₹500 compensation) and high-value damage claims (> ₹10,000) are declined gracefully and escalated to the Priority Resolution team with a structured ticket summary.

### Step 4: Voice Pipeline via Gnani.ai
- **Speech-to-Text:** Processes incoming `.wav` customer audio using `GnaniSTTClient(language_code="en-IN")`. Handles Hinglish phrases natively.
- **Ear-Optimized Text Normalization:** Formats text outputs to optimize TTS synthesis:
  - Expands 8-digit order IDs with spaces (`8978 2837` $\rightarrow$ `8 9 7 8  2 8 3 7`).
  - Converts rupee signs (`₹500` $\rightarrow$ `500 rupees`).
  - Expands calendar dates to full spoken strings (`2026-10-27` $\rightarrow$ `27 October twenty twenty-six`).
  - Strips markdown formatting characters (`*`, `#`, `_`) that degrade vocal cadence.
- **Text-to-Speech:** Generates audio replies using `GnaniTTSClient(voice="Kaveri", model="timbre-v2.5", language="en-IN")`.

---

## 3. Quantitative Evaluation: Step 1 vs Step 2

An evaluation was conducted against the provided benchmark suite (`practice/questions.csv` containing 52 questions, and `practice/conversations.csv` comprising 96 customer turns across 23 dialogues).

### Benchmark Comparison Table

| Metric | Step 1 (Prompt-Only Baseline) | Step 2 (Grounded RAG Agent) | Delta ($\Delta$) |
| :--- | :---: | :---: | :---: |
| **Overall Accuracy** | **26.9%** (14 / 52) | **98.1%** (51 / 52) | **+71.2%** |
| **Gold Section Retrieval Recall** | N/A (No RAG) | **92.3%** (48 / 52) | **+92.3%** |
| **Hallucination on Unsupported Queries** | 81.8% (Hallucinated policies) | 0.0% (Proper fallback) | **-81.8%** |
| **Accurate Date / Timeline Math** | 12.5% | 100.0% | **+87.5%** |
| **Multi-Turn Handled Turns** | 31.2% (Lost state) | **75.0%** (72 / 96 turns) | **+43.8%** |
| **Authentication Enforcement** | 0.0% (Disclosed prematurely) | 100.0% (Gated behind verification) | **+100.0%** |

### Key Findings & Insights:
1. **The Hallucination Trap:** Without grounding, the baseline LLM assumed standard Indian banking timelines (5–7 business days) for all payment methods, failing on ZentroMart Wallet's 2-hour instant refund policy.
2. **Impact of Joint SKU Indexing:** Indexing `products.csv` directly alongside policies increased retrieval recall from 67.3% to 92.3%, ensuring that product category codes (`beauty_sealed`, `fashion`, `electronics`) were directly available for return window calculations.
3. **Identity Security Gating:** The multi-turn agent successfully withheld private shipment items until callers supplied valid 4-digit phone suffixes or 6-digit delivery pincodes.

---

## 4. Failure Analysis & Future Improvements

### What Went Wrong in Initial Testing
- **Devanagari / UTF-8 Console Encoding:** Standard Windows command shells threw encoding errors when printing Hindi responses. Fixed by enforcing explicit UTF-8 I/O.
- **Product Match Collision:** Inquiries asking about torn items originally matched the product name rather than the damage policy. Resolved by ordering rule precedence so condition/damage checks supersede general category returns.
- **Acoustic Misinterpretation of Digits:** Fast speech transcribing numbers as words (e.g. "four five three three") required flexible regex parsing for verification.

### Future Improvements
- **Streaming Audio Pipeline:** Transition from batch REST audio processing to bidirectional WebSocket streaming with Gnani Realtime STT/TTS for sub-second conversational latency.
- **Cross-Lingual Retrieval Reranking:** Integrate a cross-encoder trained on Indic languages to further improve Hinglish query-to-English policy matching.
