from __future__ import annotations

from typing import Any

import librosa
import torch

from .base import SpeechQAModel, render_prompt

MODEL_ID = "Qwen/Qwen2-Audio-7B-Instruct"


class Qwen2AudioModel(SpeechQAModel):
    name = "qwen2audio"

    def __init__(self, load_in_8bit: bool = True) -> None:
        from transformers import AutoProcessor, Qwen2AudioForConditionalGeneration

        self.processor = AutoProcessor.from_pretrained(MODEL_ID)
        kwargs: dict[str, Any] = {"device_map": "auto"}
        if load_in_8bit:
            from transformers import BitsAndBytesConfig

            kwargs["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True)
        else:
            kwargs["torch_dtype"] = torch.float16
        self.model = Qwen2AudioForConditionalGeneration.from_pretrained(MODEL_ID, **kwargs)
        self.sample_rate = int(self.processor.feature_extractor.sampling_rate)  # 16000

    def _pack_inputs(self, text: str, audio) -> dict[str, Any]:
        # transformers renamed the processor kwarg across versions (audios= -> audio=).
        try:
            return self.processor(text=text, audios=[audio], return_tensors="pt", padding=True)
        except TypeError:
            return self.processor(text=text, audio=[audio], return_tensors="pt", padding=True)

    def answer(self, audio_path, question, prompt_template, gen_kwargs=None):
        gen_kwargs = {"max_new_tokens": 256, "do_sample": False, **(gen_kwargs or {})}
        prompt = render_prompt(prompt_template, question)
        conversation = [
            {
                "role": "user",
                "content": [
                    {"type": "audio", "audio_url": audio_path},
                    {"type": "text", "text": prompt},
                ],
            },
        ]
        text = self.processor.apply_chat_template(
            conversation, add_generation_prompt=True, tokenize=False
        )
        audio, _ = librosa.load(audio_path, sr=self.sample_rate, mono=True)
        inputs = self._pack_inputs(text, audio)
        inputs = {k: (v.to(self.model.device) if hasattr(v, "to") else v) for k, v in inputs.items()}
        with torch.no_grad():
            out = self.model.generate(**inputs, **gen_kwargs)
        new_tokens = out[:, inputs["input_ids"].shape[1]:]
        return self.processor.batch_decode(new_tokens, skip_special_tokens=True)[0].strip()
