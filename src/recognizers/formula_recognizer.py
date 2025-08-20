from pathlib import Path
from typing import Optional
import torch
import onnxruntime as ort
from pix2text import Pix2Text
from src.config import config_provider
from src.recognizers.base_recognizer import BaseRecognizer

settings = config_provider.get_settings()
logger = config_provider.get_logger(__name__)


class FormulaRecognizerError(Exception):
    """Базовое исключение для ошибок FormulaRecognizer."""

    pass


class ModelLoadError(FormulaRecognizerError):
    """Вызывается при сбое загрузки модели."""

    pass


class ProcessingError(FormulaRecognizerError):
    """Вызывается при сбое обработки изображения."""

    pass


_model: Optional[Pix2Text] = None
_device: str = "cuda:0" if torch.cuda.is_available() else "cpu"


def get_available_providers() -> list[str]:
    """Возвращает список доступных провайдеров ONNX Runtime."""
    return ort.get_available_providers()


def load_model() -> None:
    """Загружает модель Pix2Text с подходящим провайдером."""
    global _model
    if _model:
        return

    try:
        formula_config = {}
        formula_config["model_fp"] = str(settings.FORMULA_RECOGNIZER_MODEL_DIR / "model.onnx")
        formula_config["model_backend"] = settings.FORMULA_RECOGNIZER_MODEL_BACKEND

        # Проверка доступных провайдеров ONNX
        available_providers = get_available_providers()
        logger.info(f"Доступные провайдеры ONNX: {available_providers}")

        # Используем CPU, если CUDA недоступен
        execution_provider = (
            "CUDAExecutionProvider"
            if "CUDAExecutionProvider" in available_providers
            else "CPUExecutionProvider"
        )
        logger.info(f"Используется провайдер ONNX: {execution_provider}")

        total_configs = {
            "formula": formula_config,
            "device": _device,
            "onnx_providers": [execution_provider],
        }
        _model = Pix2Text.from_config(total_configs=total_configs)
        logger.info(f"Модель распознавания формул загружена на {_device} с {execution_provider}")
    except Exception as e:
        logger.error(f"Не удалось загрузить модель: {str(e)}")
        raise ModelLoadError(f"Не удалось загрузить модель: {str(e)}")


class FormulaRecognizer(BaseRecognizer):
    """Распознает математические формулы из изображений с помощью Pix2Text."""

    recognizer_type = "pix2text-mfr-onnx"

    def recognize_image(self, image_path: Path) -> Optional[str]:
        """Распознает формулу из указанного изображения."""
        load_model()
        if not image_path.exists():
            logger.error(f"Изображение не найдено: {image_path}")
            raise ProcessingError(f"Изображение не найдено: {image_path}")

        try:
            latex_output = _model.recognize_formula(image_path, return_text=True)
            logger.debug(
                f"Распознанная формула (превью): {latex_output[:200] if latex_output else 'None'}"
            )
            return latex_output.strip() if latex_output else None
        except Exception as e:
            logger.error(f"Не удалось распознать формулу из {image_path}: {str(e)}")
            return None
