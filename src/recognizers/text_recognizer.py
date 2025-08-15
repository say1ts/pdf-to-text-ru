from pathlib import Path
from typing import Optional
import torch
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from src.config import config_provider
from qwen_vl_utils import process_vision_info  # Утилита для vision

from .base_recognizer import BaseRecognizer

settings = config_provider.get_settings()
logger = config_provider.get_logger(__name__)

class TextRecognizerError(Exception):
    pass

class ModelLoadError(TextRecognizerError):
    pass

class ProcessingError(TextRecognizerError):
    pass

_model: Optional[Qwen2VLForConditionalGeneration] = None
_processor: Optional[AutoProcessor] = None
_device: str = "cuda" if torch.cuda.is_available() else "cpu"

def load_model() -> None:
    global _model, _processor
    if _model and _processor:
        return
    try:
        _model = Qwen2VLForConditionalGeneration.from_pretrained(
            settings.TEXT_RECOGNIZER_MODEL_NAME,
            torch_dtype="auto",
            device_map="auto",
            cache_dir=str(settings.TEXT_RECOGNIZER_CACHE_DIR),
            trust_remote_code=True
        )
        _processor = AutoProcessor.from_pretrained(
            settings.TEXT_RECOGNIZER_MODEL_NAME,
            cache_dir=str(settings.TEXT_RECOGNIZER_CACHE_DIR),
            trust_remote_code=True
        )
        logger.info(f"Text recognizer model loaded on {_device}")
    except Exception as e:
        raise ModelLoadError(f"Failed to load model: {str(e)}")

class TextRecognizer(BaseRecognizer):
    def recognize_image(self, image_path: Path) -> Optional[str]:
        load_model()
        if not image_path.exists():
            raise ProcessingError(f"Image not found: {image_path}")

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": str(image_path)},
                    {"type": "text", "text": settings.TEXT_RECOGNIZER_PROMPT},
                ],
            }
        ]

        text_input = _processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        image_inputs, video_inputs = process_vision_info(messages)
        inputs = _processor(
            text=[text_input],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        ).to(_device)

        generated_ids = _model.generate(**inputs, max_new_tokens=512)
        generated_ids_trimmed = [out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs["input_ids"], generated_ids)]
        output_text = _processor.batch_decode(
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
        )[0].strip().replace("<|im_end|>", "").strip()

        logger.debug(f"Recognized text preview: {output_text[:200]}")
        return output_text if output_text.strip() else None