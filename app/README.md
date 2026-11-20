
被截图和操作的电脑：
进到app目录
uvicorn server:app --host 0.0.0.0 --port 8001
ssh -CNg -R 8001:127.0.0.1:8001 -p 27206 root@connect.westc.seetacloud.com

跑agent循环和推理的电脑：
vllm serve /root/autodl-tmp/Qwen2.5-VL-7B-Instruct-clean \
    --served-model-name Qwen2.5-VL-7B-Instruct \
    --trust-remote-code \
    --host 0.0.0.0 \
    --port 8000 \
    --dtype bfloat16 \
    --gpu-memory-utilization 0.90 \
    --max-model-len 8192 \
    --max-num-seqs 2