from typing import List, NamedTuple, Callable
import numpy as np
from sklearn.cluster import KMeans
from src.entities import Fragment

class ReadingOrderService:
    def center(self, fragment: Fragment) -> tuple[float, float]:
        left, top = fragment.left, fragment.top
        right, bottom = left + fragment.width, top + fragment.height
        return ((left + right) / 2, (top + bottom) / 2)

    def _estimate_clusters(self, centers: np.ndarray) -> int:
        height = max(centers[:, 1]) - min(centers[:, 1])
        threshold = height * 0.6
        distances = np.abs(centers[:, 1][:, None] - centers[:, 1])
        close_pairs = (distances < threshold).sum() // 2
        return max(1, len(centers) - close_pairs)

    def get_reading_order(self, fragments: List[Fragment]) -> List[int]:
        if not fragments:
            return []
        
        centers = np.array([self.center(fragment) for fragment in fragments])
        n_clusters = self._estimate_clusters(centers)
        
        if n_clusters == 1:
            indices = np.argsort(centers[:, 1])
        else:
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            labels = kmeans.fit_predict(centers)
            cluster_centers = kmeans.cluster_centers_
            cluster_order = np.argsort(cluster_centers[:, 1])
            indices = []
            for cluster in cluster_order:
                cluster_indices = np.where(labels == cluster)[0]
                indices.extend(cluster_indices[np.argsort(centers[cluster_indices, 1])])
        
        return indices.tolist()

def get_default_order(fragments: List[Fragment]) -> List[int]:
    return list(range(len(fragments)))

def visualize_fragments(fragments: List[Fragment], order: List[int], width: int = 595, height: int = 842) -> np.ndarray:
    import cv2
    img = np.ones((height, width, 3), dtype=np.uint8) * 255
    for idx, fragment in enumerate(fragments):
        left, top = fragment.left, fragment.top
        right, bottom = left + fragment.width, top + fragment.height
        cv2.rectangle(img, (int(left), int(top)), (int(right), int(bottom)), (0, 255, 0), 2)
        cv2.putText(img, str(order[idx]), (int(left), int(top) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
    return img