# 微调
## 任务1
(gui_agent) root@autodl-container-8r96hvx588-1c949339:~/gui-agent/app# python cli.py "open the web browser"
2026-11-25 03:43:39 | INFO     | langchain_openai.chat_models._client_utils | langchain-openai detected http_proxy, https_proxy and no explicit `http_socket_options` / `http_client` / `http_async_client` / `openai_proxy`; skipping the custom `httpx` transport so httpx's env-proxy auto-detection applies. Pass `http_socket_options=[...]` to opt back into kernel-level TCP keepalive tuning on top of the env proxy.
2026-11-25 03:43:39 | INFO     | agent | Agent created | model=mind2web base_url=http://127.0.0.1:8000/v1 max_steps=10
2026-11-25 03:43:39 | INFO     | agent | run start | thread_id=None goal='open the web browser'
2026-11-25 03:43:39 | INFO     | perception | node=perception step=0
2026-11-25 03:43:39 | INFO     | perception | http request | GET /screenshot status=200 latency=0.532s size=1835842
2026-11-25 03:43:39 | INFO     | perception | Screenshot resized | 1920x1080 -> 1316x728 | scale_x=0.6854 scale_y=0.6741
2026-11-25 03:43:40 | INFO     | verifier | node=verifier step=0
2026-11-25 03:43:40 | INFO     | verifier | verification result | status=skipped reason=No previous screenshot
2026-11-25 03:43:40 | INFO     | planner | node=planner step=0
2026-11-25 03:43:40 | INFO     | planner | llm call start
2026-11-25 03:43:48 | INFO     | httpx2 | HTTP Request: POST http://127.0.0.1:8000/v1/chat/completions "HTTP/1.1 200 OK"
2026-11-25 03:43:48 | INFO     | planner | llm call end | latency=7.98s
2026-11-25 03:43:48 | INFO     | planner | llm output | step=0
{
  "thought": "The goal is to open the web browser. The Firefox icon is visible on the desktop. I will perform a left-click on the Firefox icon to open the web browser.",
  "expected_result": "The Firefox browser window will open.",
  "action": {
    "type": "left_single_click",
    "x": 150,
    "y": 439,
    "modifiers": []
  }
}
2026-11-25 03:43:48 | INFO     | planner | planner done | step=0 action=ActionType.LEFT_SINGLE_CLICK total_time=7.98s
2026-11-25 03:43:48 | INFO     | executor | node executer | step=0
2026-11-25 03:43:49 | INFO     | executor | http request | POST /execute action=ActionType.LEFT_SINGLE_CLICK status=200 latency=0.338s
2026-11-25 03:43:51 | INFO     | agent | loop done | step=0 loop_time=12.11s
2026-11-25 03:43:51 | INFO     | perception | node=perception step=1
2026-11-25 03:43:51 | INFO     | perception | http request | GET /screenshot status=200 latency=0.454s size=1838306
2026-11-25 03:43:52 | INFO     | perception | Screenshot resized | 1920x1080 -> 1316x728 | scale_x=0.6854 scale_y=0.6741
2026-11-25 03:43:52 | INFO     | verifier | node=verifier step=1
2026-11-25 03:43:52 | INFO     | verifier | verification result | status=failure reason=No significant visual changes detected. Local changed ratio: 0.0000, Global changed ratio: 0.0000
2026-11-25 03:43:52 | INFO     | planner | node=planner step=1
2026-11-25 03:43:52 | INFO     | planner | llm call start
2026-11-25 03:43:55 | INFO     | httpx2 | HTTP Request: POST http://127.0.0.1:8000/v1/chat/completions "HTTP/1.1 200 OK"
2026-11-25 03:43:55 | INFO     | planner | llm call end | latency=3.78s
2026-11-25 03:43:55 | INFO     | planner | llm output | step=1
{
  "thought": "The previous action involved a left single click on the Firefox icon, which resulted in a 'failure' status. This suggests that the Firefox icon was selected but did not open the web browser. Since the icon is clearly visible, I will attempt a left double click to open the browser.",
  "expected_result": "The Firefox browser window should open upon a left double click.",
  "action": {
    "type": "left_double_click",
    "x": 150,
    "y": 439,
    "modifiers": []
  }
}
2026-11-25 03:43:55 | INFO     | planner | planner done | step=1 action=ActionType.LEFT_DOUBLE_CLICK total_time=3.78s
2026-11-25 03:43:55 | INFO     | executor | node executer | step=1
2026-11-25 03:43:56 | INFO     | executor | http request | POST /execute action=ActionType.LEFT_DOUBLE_CLICK status=200 latency=0.310s
2026-11-25 03:43:58 | INFO     | agent | loop done | step=1 loop_time=6.95s
2026-11-25 03:43:58 | INFO     | perception | node=perception step=2
2026-11-25 03:43:58 | INFO     | perception | http request | GET /screenshot status=200 latency=0.255s size=260330
2026-11-25 03:43:58 | INFO     | perception | Screenshot resized | 1920x1080 -> 1316x728 | scale_x=0.6854 scale_y=0.6741
2026-11-25 03:43:58 | INFO     | verifier | node=verifier step=2
2026-11-25 03:43:58 | INFO     | verifier | verification result | status=success reason={'reason': 'Significant visual changes detected after double-click', 'global_changed_ratio': 0.9011594408630883, 'global_mean_diff': 70.59745127592772, 'global_changed_regions': [{'bbox': [823, 721, 837, 724], 'area': 25.0}, {'bbox': [1140, 701, 1154, 710], 'area': 47.0}, {'bbox': [0, 0, 1316, 688], 'area': 903394.0}]}
2026-11-25 03:43:58 | INFO     | planner | node=planner step=2
2026-11-25 03:43:58 | INFO     | planner | llm call start
2026-11-25 03:44:01 | INFO     | httpx2 | HTTP Request: POST http://127.0.0.1:8000/v1/chat/completions "HTTP/1.1 200 OK"
2026-11-25 03:44:01 | INFO     | planner | llm call end | latency=3.21s
2026-11-25 03:44:01 | INFO     | planner | llm output | step=2
{
  "thought": "The previous action involved a left double-click on the Firefox icon, resulting in a 'success' status. This indicates that the Firefox icon was clicked and the web browser opened. The current screenshot confirms that the Firefox browser is open and ready for use.",
  "expected_result": "The Firefox browser window is open and active, displaying the home page with search and bookmark options.",
  "action": {
    "type": "finish"
  }
}
2026-11-25 03:44:01 | INFO     | planner | planner done | step=2 action=ActionType.FINISH total_time=3.21s
2026-11-25 03:44:01 | INFO     | agent | Agent 运行结束 | thread_id=None goal='open the web browser'

## 任务2
失败了，因为搜索按键太小，导致定位失败


# 基模
## 任务1
(gui_agent) root@autodl-container-8r96hvx588-1c949339:~/gui-agent/app# python cli.py "open the web browser"
2026-11-25 03:26:04 | INFO     | langchain_openai.chat_models._client_utils | langchain-openai detected http_proxy, https_proxy and no explicit `http_socket_options` / `http_client` / `http_async_client` / `openai_proxy`; skipping the custom `httpx` transport so httpx's env-proxy auto-detection applies. Pass `http_socket_options=[...]` to opt back into kernel-level TCP keepalive tuning on top of the env proxy.
2026-11-25 03:26:04 | INFO     | agent | Agent created | model=Qwen2.5-VL-7B-Instruct base_url=http://127.0.0.1:8000/v1 max_steps=10
2026-11-25 03:26:04 | INFO     | agent | run start | thread_id=None goal='open the web browser'
2026-11-25 03:26:04 | INFO     | perception | node=perception step=0
2026-11-25 03:26:05 | INFO     | perception | http request | GET /screenshot status=200 latency=0.989s size=1835878
2026-11-25 03:26:06 | INFO     | perception | Screenshot resized | 1920x1080 -> 1316x728 | scale_x=0.6854 scale_y=0.6741
2026-11-25 03:26:07 | INFO     | verifier | node=verifier step=0
2026-11-25 03:26:07 | INFO     | verifier | verification result | status=skipped reason=No previous screenshot
2026-11-25 03:26:07 | INFO     | planner | node=planner step=0
2026-11-25 03:26:07 | INFO     | planner | llm call start
2026-11-25 03:26:10 | INFO     | httpx2 | HTTP Request: POST http://127.0.0.1:8000/v1/chat/completions "HTTP/1.1 200 OK"
2026-11-25 03:26:10 | INFO     | planner | llm call end | latency=3.28s
2026-11-25 03:26:10 | INFO     | planner | llm output | step=0
{
  "thought": "The goal is to open the web browser. The current screen shows the desktop with various icons, including Firefox.exe which is a web browser. I will perform a left_single_click on the Firefox icon.",
  "expected_result": "The Firefox web browser will open.",
  "action": {
    "type": "left_single_click",
    "x": 150,
    "y": 439,
    "modifiers": []
  }
}
2026-11-25 03:26:10 | INFO     | planner | planner done | step=0 action=ActionType.LEFT_SINGLE_CLICK total_time=3.28s
2026-11-25 03:26:10 | INFO     | executor | node executer | step=0
2026-11-25 03:26:10 | INFO     | executor | http request | POST /execute action=ActionType.LEFT_SINGLE_CLICK status=200 latency=0.340s
2026-11-25 03:26:12 | INFO     | agent | loop done | step=0 loop_time=7.92s
2026-11-25 03:26:12 | INFO     | perception | node=perception step=1
2026-11-25 03:26:13 | INFO     | perception | http request | GET /screenshot status=200 latency=0.895s size=1838334
2026-11-25 03:26:13 | INFO     | perception | Screenshot resized | 1920x1080 -> 1316x728 | scale_x=0.6854 scale_y=0.6741
2026-11-25 03:26:13 | INFO     | verifier | node=verifier step=1
2026-11-25 03:26:14 | INFO     | verifier | verification result | status=failure reason=No significant visual changes detected. Local changed ratio: 0.0000, Global changed ratio: 0.0000
2026-11-25 03:26:14 | INFO     | planner | node=planner step=1
2026-11-25 03:26:14 | INFO     | planner | llm call start
2026-11-25 03:26:17 | INFO     | httpx2 | HTTP Request: POST http://127.0.0.1:8000/v1/chat/completions "HTTP/1.1 200 OK"
2026-11-25 03:26:17 | INFO     | planner | llm call end | latency=3.59s
2026-11-25 03:26:17 | INFO     | planner | llm output | step=1
{
  "thought": "The previous action involved a left_single_click on the Firefox icon, but the verification result indicated a failure. This suggests that the single click did not open the browser. Since the Firefox icon is clearly visible, I will attempt a left_double_click to open the browser.",
  "expected_result": "The Firefox browser window should open upon a left_double_click on the Firefox icon.",
  "action": {
    "type": "left_double_click",
    "x": 150,
    "y": 439,
    "modifiers": []
  }
}
2026-11-25 03:26:17 | INFO     | planner | planner done | step=1 action=ActionType.LEFT_DOUBLE_CLICK total_time=3.60s
2026-11-25 03:26:17 | INFO     | executor | node executer | step=1
2026-11-25 03:26:17 | INFO     | executor | http request | POST /execute action=ActionType.LEFT_DOUBLE_CLICK status=200 latency=0.338s
2026-11-25 03:26:19 | INFO     | agent | loop done | step=1 loop_time=7.24s
2026-11-25 03:26:19 | INFO     | perception | node=perception step=2
2026-11-25 03:26:20 | INFO     | perception | http request | GET /screenshot status=200 latency=0.287s size=260362
2026-11-25 03:26:20 | INFO     | perception | Screenshot resized | 1920x1080 -> 1316x728 | scale_x=0.6854 scale_y=0.6741
2026-11-25 03:26:20 | INFO     | verifier | node=verifier step=2
2026-11-25 03:26:20 | INFO     | verifier | verification result | status=success reason={'reason': 'Significant visual changes detected after double-click', 'global_changed_ratio': 0.9011594408630883, 'global_mean_diff': 70.59745127592772, 'global_changed_regions': [{'bbox': [823, 721, 837, 724], 'area': 25.0}, {'bbox': [1140, 701, 1154, 710], 'area': 47.0}, {'bbox': [0, 0, 1316, 688], 'area': 903394.0}]}
2026-11-25 03:26:20 | INFO     | planner | node=planner step=2
2026-11-25 03:26:20 | INFO     | planner | llm call start
2026-11-25 03:26:22 | INFO     | httpx2 | HTTP Request: POST http://127.0.0.1:8000/v1/chat/completions "HTTP/1.1 200 OK"
2026-11-25 03:26:22 | INFO     | planner | llm call end | latency=2.51s
2026-11-25 03:26:22 | INFO     | planner | llm output | step=2
{
  "thought": "The previous action was a left_double_click on the Firefox icon, which resulted in a successful verification. The current screenshot shows the Firefox browser window open, indicating that the web browser has been successfully opened.",
  "expected_result": "The Firefox browser window is open and ready for use.",
  "action": {
    "type": "finish"
  }
}
2026-11-25 03:26:22 | INFO     | planner | planner done | step=2 action=ActionType.FINISH total_time=2.51s
2026-11-25 03:26:22 | INFO     | agent | Agent 运行结束 | thread_id=None goal='open the web browser'