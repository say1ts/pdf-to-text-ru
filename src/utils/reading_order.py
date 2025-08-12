from typing import List, Dict
import numpy as np
from sklearn.cluster import KMeans

from collections import namedtuple
from typing import Tuple

# Определяем Block как namedtuple с типом и координатами
BlockBase = namedtuple("Block", ["type", "coordinates"])


class Block(BlockBase):
    """Класс блока текста с типом и координатами."""

    def center(self) -> Tuple[float, float]:
        """Вычисляет центр масс блока на основе координат [left, top, right, bottom]."""
        left, top, right, bottom = self.coordinates
        return ((left + right) / 2, (top + bottom) / 2)

    def __repr__(self) -> str:
        return f"Block(type={self.type}, coordinates={self.coordinates})"

class ReadingOrderService:
    """Service to determine the reading order of text blocks."""

    def _process_block_group_with_kmeans(self, group_orig_indices: List[int], blocks: List[Block], all_x_centers: np.ndarray, all_y_centers: np.ndarray) -> List[int]:
        if not group_orig_indices:
            return []

        ordered_indices_for_group = []
        subset_block_objects = [blocks[i] for i in group_orig_indices]
        if not subset_block_objects:
            return []

        subset_x_centers = np.array([block.center()[0] for block in subset_block_objects])

        if len(subset_block_objects) == 1:
            n_clusters_sec = 1
        else:
            n_clusters_sec = self._estimate_clusters(subset_x_centers)

        actual_n_clusters_sec = min(n_clusters_sec, len(subset_block_objects))
        if actual_n_clusters_sec < 1:
            actual_n_clusters_sec = 1

        # Prepare data for KMeans clustering
        if subset_x_centers.ndim == 1:
            subset_x_centers_reshaped = subset_x_centers[:, np.newaxis]
        else:
            subset_x_centers_reshaped = subset_x_centers

        if subset_x_centers_reshaped.shape[0] == 0:
            return []
        if subset_x_centers_reshaped.shape[0] < actual_n_clusters_sec:
            actual_n_clusters_sec = subset_x_centers_reshaped.shape[0]
            if actual_n_clusters_sec == 0:
                return []

        # Cluster blocks into columns based on x-centers
        kmeans_sec = KMeans(n_clusters=actual_n_clusters_sec, random_state=42, n_init='auto').fit(subset_x_centers_reshaped)
        column_labels_sec_local = kmeans_sec.labels_
        cluster_centroids_sec = kmeans_sec.cluster_centers_.flatten()

        # Order clusters from left to right
        sorted_cluster_indices_sec = np.argsort(cluster_centroids_sec)
        column_mapping_sec = {old_idx: new_idx for new_idx, old_idx in enumerate(sorted_cluster_indices_sec)}
        ordered_column_labels_for_subset = [column_mapping_sec[label] for label in column_labels_sec_local]

        # Group indices by ordered column labels
        columns_in_group: Dict[int, List[int]] = {}
        for i, sorted_col_label in enumerate(ordered_column_labels_for_subset):
            original_block_idx = group_orig_indices[i]
            if sorted_col_label not in columns_in_group:
                columns_in_group[sorted_col_label] = []
            columns_in_group[sorted_col_label].append(original_block_idx)

        # Sort blocks in each column by y-center (rounded to nearest 10) and x-center
        for col_label_sorted_key in sorted(columns_in_group.keys()):
            col_original_indices = columns_in_group[col_label_sorted_key]
            if not col_original_indices:
                continue
            sorted_indices_in_col = sorted(
                col_original_indices,
                key=lambda orig_idx: (round(all_y_centers[orig_idx], -1), all_x_centers[orig_idx])
            )
            ordered_indices_for_group.extend(sorted_indices_in_col)

        return ordered_indices_for_group

    def get_reading_order(self, blocks: List[Block]) -> List[int]:
        """Возвращает индексы блоков в корректном порядке чтения."""
        if not blocks:
            return []

        # Calculate overall width span for wide block detection
        all_coords = np.array([block.coordinates for block in blocks])
        min_x_coord_overall = np.min(all_coords[:, 0]) if len(blocks) > 0 else 0
        max_x_coord_overall = np.max(all_coords[:, 2]) if len(blocks) > 0 else 0
        overall_width_span = max_x_coord_overall - min_x_coord_overall
        wide_block_threshold = 0.6 * overall_width_span if overall_width_span > 0 else float('inf')

        # Calculate centers of all blocks
        all_block_centers = np.array([block.center() for block in blocks])
        all_x_centers = all_block_centers[:, 0]
        all_y_centers = all_block_centers[:, 1]

        title_original_indices = [i for i, block in enumerate(blocks) if block.type == "Title"]
        final_ordered_indices = []
        defined_sections = []

        # Define sections based on titles
        if not title_original_indices:
            if blocks:
                defined_sections.append(list(range(len(blocks))))
        else:
            if title_original_indices[0] > 0:
                defined_sections.append(list(range(0, title_original_indices[0])))
            for i in range(len(title_original_indices)):
                title_idx = title_original_indices[i]
                next_title_idx_or_end = title_original_indices[i + 1] if (i + 1) < len(title_original_indices) else len(blocks)
                defined_sections.append(list(range(title_idx, next_title_idx_or_end)))

        # Process each section
        for section_orig_indices in defined_sections:
            if not section_orig_indices:
                continue

            current_section_ordered_indices = []
            first_block_in_section_orig_idx = section_orig_indices[0]

            if blocks[first_block_in_section_orig_idx].type == "Title" and first_block_in_section_orig_idx in title_original_indices:
                current_section_ordered_indices.append(first_block_in_section_orig_idx)
                content_blocks_orig_indices = section_orig_indices[1:]
            else:
                content_blocks_orig_indices = list(section_orig_indices)

            if not content_blocks_orig_indices:
                final_ordered_indices.extend(current_section_ordered_indices)
                continue

            # Process content blocks, treating wide blocks as separators
            processing_group = list(content_blocks_orig_indices)
            while processing_group:
                first_wide_block_local_idx = -1
                wide_block_orig_idx = -1
                for i, orig_idx in enumerate(processing_group):
                    block = blocks[orig_idx]
                    block_width = block.coordinates[2] - block.coordinates[0]
                    if block.type != "Title" and block_width >= wide_block_threshold:
                        first_wide_block_local_idx = i
                        wide_block_orig_idx = orig_idx
                        break

                if first_wide_block_local_idx != -1:
                    blocks_before_wide = processing_group[:first_wide_block_local_idx]
                    if blocks_before_wide:
                        current_section_ordered_indices.extend(
                            self._process_block_group_with_kmeans(blocks_before_wide, blocks, all_x_centers, all_y_centers)
                        )
                    current_section_ordered_indices.append(wide_block_orig_idx)
                    processing_group = processing_group[first_wide_block_local_idx + 1:]
                else:
                    if processing_group:
                        current_section_ordered_indices.extend(
                            self._process_block_group_with_kmeans(processing_group, blocks, all_x_centers, all_y_centers)
                        )
                    processing_group = []

            final_ordered_indices.extend(current_section_ordered_indices)

        # Ensure all blocks are included without duplicates
        if blocks and (len(set(final_ordered_indices)) != len(blocks) or len(final_ordered_indices) != len(blocks)):
            all_indices_set = set(range(len(blocks)))
            current_indices_set = set(final_ordered_indices)
            missing_indices = list(all_indices_set - current_indices_set)
            if missing_indices:
                missing_sorted = sorted(missing_indices, key=lambda orig_idx: (round(all_y_centers[orig_idx], -1), all_x_centers[orig_idx]))
                final_ordered_indices.extend(missing_sorted)

            seen = set()
            deduplicated_list = [item for item in final_ordered_indices if not (item in seen or seen.add(item))]
            final_ordered_indices = deduplicated_list

            if len(final_ordered_indices) != len(blocks):
                return sorted(list(range(len(blocks))), key=lambda i: (round(all_y_centers[i], -1), all_x_centers[i]))

        return final_ordered_indices

    def _estimate_clusters(self, x_centers: np.ndarray) -> int:
        if len(x_centers) <= 1:
            return 1

        sorted_x = np.sort(x_centers)
        diffs = np.diff(sorted_x)
        if len(diffs) == 0:
            return 1

        # Estimate clusters based on significant gaps in x-centers
        mean_diff = np.mean(diffs)
        std_diff = np.std(diffs)
        threshold = mean_diff + 0.5 * std_diff if len(diffs) > 0 else 0
        n_clusters = 1 + np.sum(diffs >= threshold)
        return max(1, min(n_clusters, len(x_centers)))