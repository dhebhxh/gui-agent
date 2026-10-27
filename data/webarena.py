from datasets import load_dataset
from .common import UnifiedSample

def load_webarena_verified(split: str = "full", max_tasks: int = None):
    """
    Load WebArena-Verified tasks.
    These are task definitions only — no screenshots.
    Screenshots must be captured live by the agent in the Docker environment.
    
    Valid splits: "full" (812 tasks), "hard" (258 tasks).
    """
    ds = load_dataset("AmineHA/WebArena-Verified", split=split)

    if max_tasks:
        ds = ds.select(range(min(max_tasks, len(ds))))

    samples = []
    for row in ds:
        samples.append(UnifiedSample(
            image_bytes=None,           # no static screenshot
            image_path=None,
            instruction=row.get("intent", ""),
            action={},                  # no pre-annotated action sequence
            source="webarena_verified",
            metadata={
                "task_id": row.get("task_id"),
                "sites": row.get("sites"),
                "start_urls": row.get("start_urls"),
                "eval": row.get("eval"),           # 评测规则（字符串形式，运行时解析）
                "intent_template_id": row.get("intent_template_id"),
                "revision": row.get("revision"),
                "split": split,
            },
        ))

    return samples