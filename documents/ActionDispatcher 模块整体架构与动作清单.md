# ActionDispatcher 模块介绍

## 一、整体架构


**核心方法**：`ActionDispatcher.dispatch()` —— 唯一的入口方法，在内部根据不同的动作类型调用内部具体的处理方法。

**输入**：一个 `action` 字典，形如 `{"type": "...", 其他参数...}`，具体见下表

**输出**：一个 `dict`，统一为三种响应类型：`ok` / `image` / `text`

---

## 二、动作总览（共 19 种）

| action type | 输入字段 | 必填字段 | 可选字段 | 输出 |
|---|---|---|---|---|
| `screenshot` | — | — | — | `{"type": "image", "data": <PNG bytes>}` |
| `cursor_position` | — | — | — | `{"type": "text", "data": "[x, y]"}` |
| `mouse_move` | `x`, `y` | `x`, `y` | — | `{"type": "ok"}` |
| `left_click` | `x`, `y`, `modifiers` | — | `x`, `y`, `modifiers` | `{"type": "ok"}` |
| `right_click` | `x`, `y`, `modifiers` | — | `x`, `y`, `modifiers` | `{"type": "ok"}` |
| `middle_click` | `x`, `y`, `modifiers` | — | `x`, `y`, `modifiers` | `{"type": "ok"}` |
| `left_double_click` | `x`, `y`, `modifiers` | — | `x`, `y`, `modifiers` | `{"type": "ok"}` |
| `left_click_drag` | `start_x`, `start_y`, `end_x`, `end_y`, `modifiers` | `start_x`, `start_y`, `end_x`, `end_y` | `modifiers` | `{"type": "ok"}` |
| `left_mouse_down` | — | — | — | `{"type": "ok"}` |
| `left_mouse_up` | — | — | — | `{"type": "ok"}` |
| `right_mouse_down` | — | — | — | `{"type": "ok"}` |
| `right_mouse_up` | — | — | — | `{"type": "ok"}` |
| `middle_mouse_down` | — | — | — | `{"type": "ok"}` |
| `middle_mouse_up` | — | — | — | `{"type": "ok"}` |
| `scroll` | `direction`, `amount`, `x`, `y` | `direction` | `amount`, `x`, `y` | `{"type": "ok"}` |
| `key_press` | `key` | `key` | — | `{"type": "ok"}` |
| `key_down` | `key` | `key` | — | `{"type": "ok"}` |
| `key_up` | `key` | `key` | — | `{"type": "ok"}` |
| `type_text` | `text` | `text` | — | `{"type": "ok"}` |