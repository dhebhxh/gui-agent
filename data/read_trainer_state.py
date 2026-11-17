import json
import os
import argparse

import matplotlib.pyplot as plt


def load_trainer_state(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def summarize(state):
    """打印报告里需要的关键字段。"""
    print("=" * 60)
    print("训练状态摘要")
    print("=" * 60)

    keys = [
        "global_step", "max_steps", "epoch",
        "num_train_epochs", "train_batch_size",
        "logging_steps", "save_steps",
        "total_flos", "num_input_tokens_seen",
        "best_model_checkpoint", "best_metric",
    ]
    for k in keys:
        if k in state:
            print(f"{k:24s}: {state[k]}")

    log_history = state.get("log_history", [])
    print(f"{'log_history 条数':24s}: {len(log_history)}")

    # 检查点
    ckpts = [
        (e["step"], e.get("train_loss"))
        for e in log_history
        if "train_loss" in e and e.get("step") is not None
    ]
    if ckpts:
        print(f"{'首条 train_loss':24s}: step={ckpts[0][0]}, loss={ckpts[0][1]:.6f}")
        print(f"{'末条 train_loss':24s}: step={ckpts[-1][0]}, loss={ckpts[-1][1]:.6f}")
        print(f"{'train_loss 记录数':24s}: {len(ckpts)}")


def extract_loss(state):
    """从 log_history 提取 (step, loss)，过滤掉 eval 记录。"""
    steps, losses = [], []
    for entry in state.get("log_history", []):
        if "loss" in entry and "step" in entry:
            steps.append(entry["step"])
            losses.append(entry["loss"])
    return steps, losses


def export_csv(steps, losses, out_csv):
    with open(out_csv, "w", encoding="utf-8") as f:
        f.write("step,loss\n")
        for s, l in zip(steps, losses):
            f.write(f"{s},{l}\n")
    print(f"已导出 CSV: {out_csv}")


def plot_loss(steps, losses, out_png, smooth_window=10):
    if not steps:
        print("没有 loss 数据，跳过绘图。")
        return

    plt.figure(figsize=(9, 5))
    plt.plot(steps, losses, alpha=0.3, label="raw loss")

    # 滑动平均，让曲线更平滑，适合放报告
    if smooth_window > 1 and len(losses) >= smooth_window:
        smoothed = []
        for i in range(len(losses)):
            lo = max(0, i - smooth_window + 1)
            window = losses[lo:i + 1]
            smoothed.append(sum(window) / len(window))
        plt.plot(steps, smoothed, linewidth=2, label=f"smoothed (window={smooth_window})")

    plt.xlabel("Step")
    plt.ylabel("Loss")
    plt.title("Training Loss")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close()
    print(f"已保存 loss 曲线: {out_png}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path",
        default="/root/autodl-tmp/mind2web_qwen25vl_sft/checkpoint-876/trainer_state.json",
        help="trainer_state.json 的路径",
    )
    parser.add_argument("--out_dir", default=".", help="输出目录")
    parser.add_argument("--smooth", type=int, default=10, help="滑动平均窗口")
    args = parser.parse_args()

    if not os.path.exists(args.path):
        raise FileNotFoundError(f"找不到文件: {args.path}")

    state = load_trainer_state(args.path)
    summarize(state)

    steps, losses = extract_loss(state)
    os.makedirs(args.out_dir, exist_ok=True)

    if steps:
        csv_path = os.path.join(args.out_dir, "loss_curve.csv")
        png_path = os.path.join(args.out_dir, "loss_curve.png")
        export_csv(steps, losses, csv_path)
        plot_loss(steps, losses, png_path, smooth_window=args.smooth)
    else:
        print("log_history 中没有找到 loss 记录。")


if __name__ == "__main__":
    main()