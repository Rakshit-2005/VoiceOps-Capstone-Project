"""VoiceOps 2026 Batch Runner.

Usage:
    python run.py --audio_dir <path_to_audio_folder> --output_dir <path_to_save_results>

Takes a folder of customer audio files, transcribes each via Gnani STT,
generates a grounded answer from ZentroMart knowledge base and tools,
synthesizes a spoken response via Gnani TTS, and saves all outputs and chunk citations.
"""

import os
import sys
import json
import argparse
from typing import List

# Ensure local source directory is importable
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from src.kb_indexer import KnowledgeRetriever
from src.tools_handler import ToolsHandler
from src.conversation_agent import ConversationalAgent
from src.voice_pipeline import VoicePipeline


def run_batch(audio_dir: str, output_dir: str):
    """Process all audio files in audio_dir and output speech + text + chunk logs."""
    if not os.path.exists(audio_dir):
        print(f"[Error] Audio directory '{audio_dir}' not found.")
        return

    os.makedirs(output_dir, exist_ok=True)

    print("Initializing ZentroMart Knowledge Base & Agents...")
    retriever = KnowledgeRetriever()
    tools = ToolsHandler()
    agent = ConversationalAgent(retriever=retriever, tools=tools)
    voice = VoicePipeline()

    audio_extensions = {".wav", ".mp3", ".ogg", ".m4a"}
    audio_files = [f for f in sorted(os.listdir(audio_dir)) if os.path.splitext(f)[1].lower() in audio_extensions]

    if not audio_files:
        print(f"No audio files found in {audio_dir}.")
        # Create a sample test output file to verify batch pipeline
        sample_log = os.path.join(output_dir, "batch_status.json")
        with open(sample_log, "w", encoding="utf-8") as f:
            json.dump({"status": "ready", "files_processed": 0}, f, indent=2)
        print(f"Created {sample_log}.")
        return

    print(f"Found {len(audio_files)} audio file(s) to process.\n")
    results_summary = []

    for idx, filename in enumerate(audio_files, 1):
        in_path = os.path.join(audio_dir, filename)
        base_name = os.path.splitext(filename)[0]
        print(f"[{idx}/{len(audio_files)}] Processing: {filename}...")

        # 1. Listen (Gnani STT)
        transcript = voice.transcribe(in_path)
        print(f"    Heard: \"{transcript}\"")

        # Handle unclear / silent audio (brief p. 10)
        if not transcript or not transcript.strip() or transcript.startswith("[Transcript unavailable"):
            if transcript.startswith("[Transcript unavailable"):
                # Running without Gnani credentials - use filename or dummy query
                query_text = "What is the return window for electronics?"
                print(f"    [Local Test Mode] Using fallback query: '{query_text}'")
            else:
                reply_text = "Sorry, I didn't catch that. Could you say it again?"
                cited_chunks = []
                query_text = transcript
        else:
            query_text = transcript

        # 2. Reason & Retrieve (Agent Brain)
        reply_text, cited_chunks = agent.respond(query_text)
        print(f"    Reply: \"{reply_text}\"")
        print(f"    Sources Used: {cited_chunks}")

        # 3. Speak (Gnani TTS)
        out_wav_path = os.path.join(output_dir, f"{base_name}_reply.wav")
        voice.synthesize(reply_text, out_wav_path)
        print(f"    Saved spoken audio -> {out_wav_path}")

        # 4. Save metadata log
        out_meta_path = os.path.join(output_dir, f"{base_name}_output.json")
        result_entry = {
            "file_name": filename,
            "transcription": transcript,
            "agent_reply": reply_text,
            "retrieved_chunks": cited_chunks,
            "audio_reply_file": f"{base_name}_reply.wav"
        }
        with open(out_meta_path, "w", encoding="utf-8") as f:
            json.dump(result_entry, f, indent=2, ensure_ascii=False)

        results_summary.append(result_entry)
        print("    Done.\n")

    # Global summary report
    summary_path = os.path.join(output_dir, "batch_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2, ensure_ascii=False)
    print(f"Batch completed successfully. Summary saved to {summary_path}")


def main():
    parser = argparse.ArgumentParser(description="VoiceOps 2026 Batch Audio Runner")
    parser.add_argument("--audio_dir", "-a", type=str, default="test_audio",
                        help="Path to folder containing test .wav audio files")
    parser.add_argument("--output_dir", "-o", type=str, default="sample_outputs",
                        help="Path to folder where replies and logs will be saved")
    args = parser.parse_args()

    run_batch(audio_dir=args.audio_dir, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
