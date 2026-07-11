from __future__ import annotations

from typing import Any

import torch

from .base import SpeechQAModel, render_prompt

WHISPER_ID = "openai/whisper-medium"  # whisper-large-v3 if VRAM allows
LLM_ID = "Qwen/Qwen2.5-7B-Instruct"


class CascadeModel(SpeechQAModel):
    """Diagnostic baseline: Whisper transcribes, a text LLM answers from the transcript.

    If even this hallucinates, the failure is in reasoning about evidence, not in hearing.
    """

    name = "cascade"

    def __init__(self, load_in_8bit: bool = True) -> None:
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            BitsAndBytesConfig,
            pipeline,
        )

        self.asr = pipeline(
            "automatic-speech-recognition",
            model=WHISPER_ID,
            torch_dtype=torch.float16,
            device_map="auto",
        )
        self.tokenizer = AutoTokenizer.from_pretrained(LLM_ID)
        kwargs: dict[str, Any] = {"device_map": "auto"}
        if load_in_8bit:
            kwargs["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True)
        else:
            kwargs["torch_dtype"] = torch.float16
        self.llm = AutoModelForCausalLM.from_pretrained(LLM_ID, **kwargs)
        # src/inference.py reads this after each answer() to log it (asr_transcript field).
        self.last_transcript: str = ""

    def transcribe(self, audio_path: str) -> str:
        return self.asr(audio_path, chunk_length_s=30)["text"].strip()

    def answer(self, audio_path, question, prompt_template, gen_kwargs=None):
        gen_kwargs = {"max_new_tokens": 256, "do_sample": False, **(gen_kwargs or {})}
        transcript = self.transcribe(audio_path)
        self.last_transcript = transcript
        prompt = render_prompt(prompt_template, question)
        user_msg = (
            "The audio is given to you as a transcript.\n"
            f'Transcript: "{transcript}"\n\n{prompt}'
        )
        messages = [{"role": "user", "content": user_msg}]
        text = self.tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, tokenize=False
        )
        inputs = self.tokenizer(text, return_tensors="pt").to(self.llm.device)
        with torch.no_grad():
            out = self.llm.generate(
                **inputs, pad_token_id=self.tokenizer.eos_token_id, **gen_kwargs
            )
        new_tokens = out[:, inputs["input_ids"].shape[1]:]
        return self.tokenizer.decode(new_tokens[0], skip_special_tokens=True).strip()
