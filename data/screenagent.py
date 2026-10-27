"""
ScreenAgent dataset adapter.

Expected layout (after copying ScreenAgent's data/ScreenAgent/ into
gui_agent/data/screenagent_raw/):

    screenagent_raw/
        train/
            <session_id>/
                images/
                    *.jpg
                *.json          # one or more per session
        test/
            ...

The adapter is defensive about field names because the exact json schema
can vary between ScreenAgent releases. Run `inspect_json()` first to see
the real keys in your local copy, then tighten the TODOs if needed.
"""
import json
from pathlib import Path
from typing import List, Optional

from .common import UnifiedSample, normalize_action


# Candidate field names, tried in order.
_INSTRUCTION_KEYS = ("task_prompt_en", "task_prompt", "instruction", "task", "goal")
_IMAGE_NAME_KEYS = ("saved_image_name", "image_name", "image", "screenshot", "img")
_ACTIONS_KEYS = ("actions", "action", "action_list", "parsed_actions")
_HEIGHT_KEYS = ("video_height", "screen_height", "height", "image_height")
_WIDTH_KEYS = ("video_width", "screen_width", "width", "image_width")


def _first_present(d: dict, keys, default=None):
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


def _resolve_image_path(session_dir: Path, img_name: str) -> Optional[Path]:
    """Try a few common layouts for where the screenshot lives."""
    if not img_name:
        return None
    # Absolute or already-correct relative path.
    p = Path(img_name)
    if p.is_absolute() and p.exists():
        return p
    candidates = [
        session_dir / img_name,
        session_dir / "images" / Path(img_name).name,
        session_dir / "screenshots" / Path(img_name).name,
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def _iter_json_files(session_dir: Path):
    """Return all json files in a session dir (top-level)."""
    return sorted(session_dir.glob("*.json"))


def _extract_actions(meta: dict) -> list:
    """Return a list of raw action dicts from a meta json."""
    raw = _first_present(meta, _ACTIONS_KEYS, [])
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        # Sometimes actions is a single dict; wrap it.
        return [raw]
    if isinstance(raw, str):
        # TODO: if your copy stores actions as a raw LLM string,
        # parse it here (e.g. json.loads or regex extraction).
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, list) else [parsed]
        except json.JSONDecodeError:
            return []
    return []


def load_screenagent(data_root: str, split: str = "train") -> List[UnifiedSample]:
    """
    Load ScreenAgent samples from a local copy.

    Args:
        data_root: path to the folder containing train/ and test/
                   (e.g. "gui_agent/data/screenagent_raw")
        split: "train" or "test"

    Returns:
        List of UnifiedSample.
    """
    root = Path(data_root) / split
    if not root.exists():
        raise FileNotFoundError(f"ScreenAgent split not found: {root}")

    samples: List[UnifiedSample] = []

    for session_dir in sorted(root.iterdir()):
        if not session_dir.is_dir():
            continue

        for jf in _iter_json_files(session_dir):
            try:
                with open(jf, "r", encoding="utf-8") as f:
                    meta = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue

            instruction = _first_present(meta, _INSTRUCTION_KEYS, "")
            img_name = _first_present(meta, _IMAGE_NAME_KEYS, "")
            img_path = _resolve_image_path(session_dir, img_name)

            img_bytes = None
            if img_path is not None:
                try:
                    img_bytes = img_path.read_bytes()
                except OSError:
                    img_bytes = None

            height = _first_present(meta, _HEIGHT_KEYS)
            width = _first_present(meta, _WIDTH_KEYS)

            raw_actions = _extract_actions(meta)
            if not raw_actions:
                # Still emit a sample with empty action so we don't silently drop data.
                raw_actions = [{}]

            for act in raw_actions:
                if not isinstance(act, dict):
                    continue
                samples.append(UnifiedSample(
                    image_bytes=img_bytes,
                    image_path=str(img_path) if img_path else None,
                    instruction=instruction,
                    action=normalize_action(act, source="screenagent"),
                    source="screenagent",
                    metadata={
                        "session_id": session_dir.name,
                        "json_file": jf.name,
                        "video_height": height,
                        "video_width": width,
                    },
                ))

    return samples


# ---- Debug helper: run this once to inspect your real json schema ----
def inspect_json(data_root: str, split: str = "train", max_files: int = 3):
    """Print top-level keys and value types of the first few json files."""
    root = Path(data_root) / split
    files = []
    for session_dir in sorted(root.iterdir()):
        if session_dir.is_dir():
            files.extend(_iter_json_files(session_dir))
        if len(files) >= max_files:
            break

    for jf in files[:max_files]:
        print(f"\n=== {jf} ===")
        try:
            with open(jf, "r", encoding="utf-8") as f:
                meta = json.load(f)
        except Exception as e:
            print(f"  failed to load: {e}")
            continue
        for k, v in meta.items():
            if isinstance(v, list):
                first = v[0] if v else None
                print(f"  {k}: list[{len(v)}], first={first!r}"[:300])
            else:
                print(f"  {k}: {type(v).__name__} = {str(v)[:120]!r}")


if __name__ == "__main__":
    # Quick smoke test. Adjust the path to your local copy.
    root = "gui_agent/data/screenagent_raw"
    inspect_json(root, split="train", max_files=2)

    samples = load_screenagent(root, split="train")
    print(f"\nLoaded {len(samples)} samples.")
    if samples:
        s = samples[0]
        print("First sample:")
        print("  instruction:", s["instruction"][:80])
        print("  action:", s["action"])
        print("  image_path:", s["image_path"])
        print("  metadata:", s["metadata"])