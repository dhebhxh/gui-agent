#!/bin/bash

# 激活环境
# source /root/miniconda3/bin/activate gui_agent
# cd /root/gui-agent/data

# 1. 循环跑 27 个分片
for i in {0..26}; do
    echo "===== 正在处理分片 $i ====="
    python clean_mind2web.py --index $i
done

# 2. 开始训练
echo "===== 数据生成完毕，开始训练 ====="
python train.py

# 3. 训练结束
echo "===== 训练完成 ====="
