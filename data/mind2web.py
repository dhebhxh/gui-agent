from datasets import load_dataset
from PIL import Image
import io
import os
from .common import UnifiedSample, normalize_action


def load_mind2web_multimodal(split: str = "train", max_samples: int = None):
    """
    Load osunlp/Multimodal-Mind2Web.
    Valid splits: train, test_task, test_website, test_domain.
    Each row is one action step.
    """
    ds = load_dataset("osunlp/Multimodal-Mind2Web", split=split)

    if max_samples:
        ds = ds.select(range(min(max_samples, len(ds))))

    samples = []
    for row in ds:
        # --- image: screenshot may be a path string or decoded PIL image ---
        screenshot = row.get("screenshot")
        img_bytes = None
        if isinstance(screenshot, Image.Image):
            buf = io.BytesIO()
            screenshot.save(buf, format="PNG")
            img_bytes = buf.getvalue()
        elif isinstance(screenshot, dict) and "bytes" in screenshot:
            img_bytes = screenshot["bytes"]
        elif isinstance(screenshot, str):
            # TODO: resolve relative path against the dataset's local cache dir
            # (e.g., ds.cache_files[0]["filename"] parent) or your extracted dump.
            # For now, leave None so you don't silently mis-read.
            pass

        # --- operation: verify actual nesting via ds[0].keys() ---
        op = row.get("operation", {})
        if not op and "actions" in row and row["actions"]:
            op = row["actions"][0].get("operation", {})

        raw_action = {
            "type": op.get("op", "CLICK"),
            "value": op.get("value", ""),
        }

        samples.append(UnifiedSample(
            image_bytes=img_bytes,
            image_path=screenshot if isinstance(screenshot, str) else None,
            instruction=row.get("confirmed_task", ""),
            action=normalize_action(raw_action, source="mind2web"),
            source="mind2web",
            metadata={
                "annotation_id": row.get("annotation_id"),
                "website": row.get("website"),
                "action_uid": row.get("action_uid"),
                "split": split,
            }
        ))

    return samples