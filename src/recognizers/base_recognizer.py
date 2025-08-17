from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

class BaseRecognizer(ABC):
    recognizer_type: str
    @abstractmethod
    def recognize_image(self, image_path: Path) -> Optional[str]:
        pass
    