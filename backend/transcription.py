#!/usr/bin/env python3
"""
Uses OpenAI API format, compatible with Ollama, OpenAI, LM Studio, and other providers.
Configuration is loaded from .env file.
"""

from pathlib import Path

from faster_whisper import WhisperModel
from openai import OpenAI

# Edit system_prompt.txt to change how the LLM cleans transcriptions
PROMPT_FILE = Path(__file__).parent / "system_prompt.txt"
SYSTEM_PROMPT = PROMPT_FILE.read_text().strip()


class TranscriptionService:
    """Uses OpenAI-compatible API, works with any provider (Ollama, OpenAI, LM Studio, etc.)."""

    def __init__(
        self, whisper_model: str, llm_base_url: str, llm_api_key: str, llm_model: str
    ):
        print(f"🔄 Loading Whisper model '{whisper_model}'...")
        self.whisper = WhisperModel(
            whisper_model,
            device="auto",  # Auto-detect: Metal (Mac), CUDA (NVIDIA), or CPU
            compute_type="int8",
        )
        print(f"✅ Whisper model '{whisper_model}' loaded!")

        print(f"🔄 Connecting to LLM at {llm_base_url}...")
        self.llm_client = OpenAI(base_url=llm_base_url, api_key=llm_api_key)
        self.llm_model = llm_model

        try:
            self.llm_client.models.list()
            print("✅ Connected to LLM API!")
        except Exception as e:
            print(f"⚠️  Warning: Could not connect to LLM: {e}")
            print(f"   Make sure your LLM server is running at {llm_base_url}")

    def transcribe(self, audio_file):
        print("🔄 Transcribing...")

        segments, info = self.whisper.transcribe(
            audio_file, beam_size=5, language="en", condition_on_previous_text=False
        )

        text = " ".join([segment.text for segment in segments]).strip()
        print(f"📝 Raw: {text}")
        return text

    def get_default_system_prompt(self):
        return SYSTEM_PROMPT

    def clean_with_llm(self, text, system_prompt=None):
        if not text:
            return ""

        # Use custom prompt or fall back to default
        prompt_to_use = system_prompt if system_prompt else SYSTEM_PROMPT

        print("🤖 Cleaning with LLM...")

        try:
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": prompt_to_use},
                    {"role": "user", "content": text},
                ],
                temperature=0.3,
                max_tokens=200,
            )

            cleaned = response.choices[0].message.content.strip()
            print(f"✨ Cleaned: {cleaned}")
            return cleaned

        except Exception as e:
            print(f"⚠️  LLM error: {e}")
            return text  # Fallback to raw text

    def generate_mindmap(self, text, system_prompt=None):
        """Generate a Graphviz DOT representation of the text as a mind-map."""
        if not text:
            return ""

        # Custom prompt for mind-map generation
        mindmap_prompt = """You are a mind-map generator. Convert the given text into a hierarchical mind-map structure.

Output ONLY valid Graphviz DOT syntax that creates a mind-map visualization. Requirements:
1. Use 'digraph' with proper syntax
2. Create a central topic node and branch out to subtopics
3. Keep node labels concise (2-5 words max)
4. Use proper node relationships with arrows (->)
5. Add styling: node [shape=box, style=filled, fillcolor=lightblue]
6. Do NOT include any explanation, markdown code blocks, or text outside the DOT syntax
7. Start directly with 'digraph MindMap {'

Example format:
digraph MindMap {
    node [shape=box, style=filled, fillcolor=lightblue]
    "Main Topic" -> "Subtopic 1"
    "Main Topic" -> "Subtopic 2"
    "Subtopic 1" -> "Detail A"
}"""

        print("🧠 Generating mind-map with LLM...")

        try:
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": mindmap_prompt},
                    {"role": "user", "content": text},
                ],
                temperature=0.5,
                max_tokens=1000,
            )

            dot_code = response.choices[0].message.content.strip()

            # Remove markdown code blocks if present
            if dot_code.startswith("```"):
                lines = dot_code.split("\n")
                dot_code = "\n".join(lines[1:-1]) if len(lines) > 2 else dot_code

            print("🗺️ Mind-map DOT generated")
            return dot_code

        except Exception as e:
            print(f"⚠️  Mind-map generation error: {e}")
            # Return a simple fallback mind-map
            return 'digraph MindMap {\n    node [shape=box, style=filled, fillcolor=lightblue]\n    "Transcript" -> "No mind-map generated"\n}'

    def transcribe_file(self, audio_file_path: str, use_llm: bool = True) -> dict:
        raw_text = self.transcribe(audio_file_path)

        result = {"raw_text": raw_text}

        if use_llm and raw_text:
            cleaned_text = self.clean_with_llm(raw_text)
            result["cleaned_text"] = cleaned_text
        else:
            result["cleaned_text"] = raw_text

        return result
