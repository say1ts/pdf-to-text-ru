from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

class BaseRecognizer(ABC):
    @abstractmethod
    def recognize_image(self, image_path: Path) -> Optional[str]:
        pass