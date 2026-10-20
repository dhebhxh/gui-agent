# 测试报告：test_dispatcher.py

---

## 一、测试概况

| 项目 | 内容 |
|------|------|
| 被测模块 | `dispatcher.py` — `ActionDispatcher` |
| 测试文件 | `test_dispatcher.py` |
| 测试框架 | `unittest` + `unittest.mock` |
| 测试类数量 | 7 个 |
| 测试用例总数 | **38 个** |
| 测试策略 | 白盒 + Mock 隔离，全部替换 `pyautogui` / `mss` 外部依赖，不产生真实设备操作 |

---

## 二、测试类与用例清单

### 1. `TestActionDispatcherScreenshot`（1 个）

| 用例 | 验证点 | Mock 对象 |
|------|--------|-----------|
| `test_screenshot` | 返回 `{"type":"image","data":b"png-bytes"}`；`grab` 用主显示器；`to_png` 入参正确 | `mss.MSS`、`mss.tools.to_png` |

### 2. `TestActionDispatcherMouse`（8 个）

| 用例 | 验证点 |
|------|--------|
| `test_cursor_position` | 返回 `"[123, 456]"` 文本 |
| `test_mouse_move` | `moveTo(10,20)` 被调用一次 |
| `test_left_click_no_coords` | 无坐标时不调用 `moveTo`，仅 `click(button="left")` |
| `test_left_click_with_coords_and_modifiers` | 移动 → 按下顺序 `ctrl,shift` → 点击 → 释放逆序 `shift,ctrl` |
| `test_right_click` | 带坐标移动 + `click(button="right")` |
| `test_middle_click` | `click(button="middle")` |
| `test_left_double_click` | 移动 + `doubleClick(button="left")` |
| `test_left_click_drag` | `moveTo` 起止两次 + `mouseDown/mouseUp(button="left")` |

### 3. `TestActionDispatcherScroll`（6 个）

| 用例 | 验证点 |
|------|--------|
| `test_scroll_up` | 先移动到 (10,20)，`scroll(3)` |
| `test_scroll_down` | `scroll(-2)` |
| `test_scroll_left` | `hscroll(-4)` |
| `test_scroll_right` | `hscroll(5)` |
| `test_scroll_default_amount` | 缺省 `amount` → `scroll(1)` |
| `test_scroll_invalid_direction` | 非法方向抛 `ValueError`，含 "Invalid scroll direction" |

### 4. `TestActionDispatcherMouseButtons`（6 个）

| 用例 | 验证点 |
|------|--------|
| `test_left_mouse_down` / `test_left_mouse_up` | `button="left"` |
| `test_right_mouse_down` / `test_right_mouse_up` | `button="right"` |
| `test_middle_mouse_down` / `test_middle_mouse_up` | `button="middle"` |

### 5. `TestActionDispatcherKeyboard`（5 个）

| 用例 | 验证点 |
|------|--------|
| `test_key_press_single_char` | 单字符 `press("a")` |
| `test_key_press_combination` | 列表按键：按下 `ctrl,c`，逆序抬起 `c,ctrl` |
| `test_key_down` | `keyDown("shift")` |
| `test_key_up` | `keyUp("shift")` |
| `test_type_text` | `write("hello world")` |

### 6. `TestActionDispatcherDispatch`（2 个）

| 用例 | 验证点 |
|------|--------|
| `test_dispatch_unknown_type_raises` | 未知 type → 抛 `TypeError`（当前实现特征，见风险 R1） |
| `test_dispatch_routes_to_correct_handler` | 路由到正确 handler，且原样传入 action |

### 7. `TestModifierHelpers`（5 个）

| 用例 | 验证点 |
|------|--------|
| `test_press_modifiers_none` | `None` → 返回 `[]` |
| `test_press_modifiers_empty` | `[]` → 返回 `[]` |
| `test_press_modifiers_returns_pressed` | 返回按下列表，顺序正确 |
| `test_release_modifiers_reverse_order` | 逆序释放 |
| `test_release_modifiers_empty` | 空列表不调用 `keyUp` |

---