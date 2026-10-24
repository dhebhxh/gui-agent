# dispatcher.py
import pyautogui
import mss

# 允许的修饰键（归一化后）
_VALID_MODIFIERS = {"ctrl", "alt", "shift", "win", "cmd", "command", "option"}

# 允许的滚动方向
_VALID_DIRECTIONS = {"up", "down", "left", "right"}

# key_down / key_up / key_press 允许的键名（可扩充）
_VALID_KEYS = {
    # 字母
    *"abcdefghijklmnopqrstuvwxyz",
    # 数字
    *"0123456789",
    # 常用符号
    "space", "enter", "return", "tab", "esc", "escape", "backspace",
    "delete", "insert", "home", "end", "pageup", "pagedown",
    "up", "down", "left", "right",
    "ctrl", "alt", "shift", "win", "cmd", "command",
    "capslock", "numlock", "scrolllock", "printscreen", "pause",
    "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8",
    "f9", "f10", "f11", "f12",
    # 符号
    "`", "~", "!", "@", "#", "$", "%", "^", "&", "*", "(",
    ")", "-", "_", "=", "+", "[", "]", "{", "}", ";", ":",
    "'", '"', ",", "<", ".", ">", "/", "?", "\\", "|",
}


class ActionDispatcher:

    def dispatch(self, action: dict) -> dict:
        if not isinstance(action, dict):
            raise TypeError(f"action must be a dict, got {type(action).__name__}")

        action_type = action.get("type")
        if not isinstance(action_type, str):
            raise ValueError(f"action 'type' must be a non-empty string, got {action_type!r}")

        handler = getattr(self, f'_do_{action_type}', None)
        if handler is None:
            raise ValueError(f"Unknown action type: {action_type}")

        return handler(action)

    # ---------------------------------------------------------
    # 校验工具
    # ---------------------------------------------------------
    @staticmethod
    def _require(action, *keys):
        for k in keys:
            if k not in action or action[k] is None:
                raise ValueError(f"missing required key: {k}")

    @staticmethod
    def _validate_coord(value, name):
        """坐标必须是 int（bool 显式排除），允许负数/越界（交给 pyautogui 处理）"""
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"{name} must be int, got {type(value).__name__}: {value!r}")
        return value

    @classmethod
    def _validate_xy(cls, action):
        """校验并返回 (x, y)，缺任一键则报错"""
        cls._require(action, "x", "y")
        x = cls._validate_coord(action["x"], "x")
        y = cls._validate_coord(action["y"], "y")
        return x, y

    @staticmethod
    def _normalize_modifiers(modifiers):
        """返回归一化后的修饰键列表；空/None → []；非 list → TypeError"""
        if modifiers is None:
            return []
        if not isinstance(modifiers, list):
            raise TypeError(f"modifiers must be a list, got {type(modifiers).__name__}")
        normalized = []
        for m in modifiers:
            if not isinstance(m, str):
                raise TypeError(f"modifier must be str, got {type(m).__name__}: {m!r}")
            low = m.lower()
            if low not in _VALID_MODIFIERS:
                raise ValueError(f"unknown modifier: {m!r}")
            normalized.append(low)
        return normalized

    @staticmethod
    def _normalize_key(key, field="key"):
        if not isinstance(key, str):
            raise TypeError(f"{field} must be str, got {type(key).__name__}: {key!r}")
        low = key.lower()
        if low not in _VALID_KEYS:
            raise ValueError(f"unknown key: {key!r}")
        return low

    # ---------------------------------------------------------
    # screenshot
    # ---------------------------------------------------------
    def _do_screenshot(self, action):
        with mss.MSS() as sct:
            monitor = sct.monitors[0]
            sct_img = sct.grab(monitor)
            png = mss.tools.to_png(sct_img.rgb, sct_img.size)
            return {"type": "image", "data": png}

    # ---------------------------------------------------------
    # cursor position
    # ---------------------------------------------------------
    def _do_cursor_position(self, action):
        x, y = pyautogui.position()
        return {"type": "text", "data": f"[{x}, {y}]"}

    # ---------------------------------------------------------
    # mouse move
    # ---------------------------------------------------------
    def _do_mouse_move(self, action):
        x, y = self._validate_xy(action)
        pyautogui.moveTo(x, y)
        return {"type": "ok"}

    # ---------------------------------------------------------
    # 点击（left / right / middle / double）
    # ---------------------------------------------------------
    def _do_click(self, action, button, double=False):
        # 坐标：要么 x/y 都有，要么都没有；只给一个视为非法
        has_x = "x" in action and action["x"] is not None
        has_y = "y" in action and action["y"] is not None
        if has_x or has_y:
            if not (has_x and has_y):
                raise ValueError("both x and y must be provided together")
            x = self._validate_coord(action["x"], "x")
            y = self._validate_coord(action["y"], "y")
            pyautogui.moveTo(x, y)

        modifiers = self._normalize_modifiers(action.get("modifiers"))
        pressed = self._press_modifiers(modifiers)
        if double:
            pyautogui.doubleClick(button=button)
        else:
            pyautogui.click(button=button)
        self._release_modifiers(pressed)
        return {"type": "ok"}

    def _do_left_click(self, action):
        return self._do_click(action, "left")

    def _do_right_click(self, action):
        return self._do_click(action, "right")

    def _do_middle_click(self, action):
        return self._do_click(action, "middle")

    def _do_left_double_click(self, action):
        return self._do_click(action, "left", double=True)

    # ---------------------------------------------------------
    # scroll
    # ---------------------------------------------------------
    def _do_scroll(self, action):
        # 坐标可选，但若给则必须成对
        has_x = "x" in action and action["x"] is not None
        has_y = "y" in action and action["y"] is not None
        if has_x or has_y:
            if not (has_x and has_y):
                raise ValueError("both x and y must be provided together")
            x = self._validate_coord(action["x"], "x")
            y = self._validate_coord(action["y"], "y")
            pyautogui.moveTo(x, y)

        self._require(action, "direction")
        direction = action["direction"]
        if not isinstance(direction, str) or direction.lower() not in _VALID_DIRECTIONS:
            raise ValueError(f"Invalid scroll direction: {direction!r}")
        direction = direction.lower()

        amount = action.get("amount", 1)
        if isinstance(amount, bool) or not isinstance(amount, (int, float)):
            raise TypeError(f"amount must be int/float, got {type(amount).__name__}: {amount!r}")

        if direction == "up":
            pyautogui.scroll(amount)
        elif direction == "down":
            pyautogui.scroll(-amount)
        elif direction == "left":
            pyautogui.hscroll(-amount)
        elif direction == "right":
            pyautogui.hscroll(amount)

        return {"type": "ok"}

    # ---------------------------------------------------------
    # left click drag
    # ---------------------------------------------------------
    def _do_left_click_drag(self, action):
        # end_x / end_y 必需
        self._require(action, "end_x", "end_y")
        end_x = self._validate_coord(action["end_x"], "end_x")
        end_y = self._validate_coord(action["end_y"], "end_y")

        # start_x / start_y 可选；都不给则用当前位置
        has_sx = "start_x" in action and action["start_x"] is not None
        has_sy = "start_y" in action and action["start_y"] is not None
        if has_sx or has_sy:
            if not (has_sx and has_sy):
                raise ValueError("both start_x and start_y must be provided together")
            start_x = self._validate_coord(action["start_x"], "start_x")
            start_y = self._validate_coord(action["start_y"], "start_y")
        else:
            start_x, start_y = pyautogui.position()

        modifiers = self._normalize_modifiers(action.get("modifiers"))
        pressed = self._press_modifiers(modifiers)
        pyautogui.moveTo(start_x, start_y)
        pyautogui.mouseDown(button="left")
        pyautogui.moveTo(end_x, end_y)
        pyautogui.mouseUp(button="left")
        self._release_modifiers(pressed)
        return {"type": "ok"}

    # ---------------------------------------------------------
    # mouse down / up
    # ---------------------------------------------------------
    def _do_left_mouse_down(self, action):
        pyautogui.mouseDown(button="left")
        return {"type": "ok"}

    def _do_left_mouse_up(self, action):
        pyautogui.mouseUp(button="left")
        return {"type": "ok"}

    def _do_right_mouse_down(self, action):
        pyautogui.mouseDown(button="right")
        return {"type": "ok"}

    def _do_right_mouse_up(self, action):
        pyautogui.mouseUp(button="right")
        return {"type": "ok"}

    def _do_middle_mouse_down(self, action):
        pyautogui.mouseDown(button="middle")
        return {"type": "ok"}

    def _do_middle_mouse_up(self, action):
        pyautogui.mouseUp(button="middle")
        return {"type": "ok"}

    # ---------------------------------------------------------
    # key press / down / up
    # ---------------------------------------------------------
    def _do_key_press(self, action):
        self._require(action, "key")
        key = action["key"]

        # 统一成 list[str]
        if isinstance(key, str):
            keys = [key]
        elif isinstance(key, list):
            if not key:
                raise ValueError("key list must not be empty")
            keys = key
        else:
            raise TypeError(f"key must be str or list[str], got {type(key).__name__}")

        normalized = [self._normalize_key(k) for k in keys]

        if len(normalized) == 1:
            pyautogui.press(normalized[0])
        else:
            for k in normalized:
                pyautogui.keyDown(k)
            for k in reversed(normalized):
                pyautogui.keyUp(k)
        return {"type": "ok"}

    def _do_key_down(self, action):
        self._require(action, "key")
        key = self._normalize_key(action["key"])
        pyautogui.keyDown(key)
        return {"type": "ok"}

    def _do_key_up(self, action):
        self._require(action, "key")
        key = self._normalize_key(action["key"])
        pyautogui.keyUp(key)
        return {"type": "ok"}

    # ---------------------------------------------------------
    # type text
    # ---------------------------------------------------------
    def _do_type_text(self, action):
        self._require(action, "text")
        text = action["text"]
        if not isinstance(text, str):
            raise TypeError(f"text must be str, got {type(text).__name__}: {text!r}")
        if text == "":
            raise ValueError("text must not be empty")
        pyautogui.write(text)
        return {"type": "ok"}

    # ---------------------------------------------------------
    # utility
    # ---------------------------------------------------------
    def _press_modifiers(self, modifiers):
        if not modifiers:
            return []
        pressed = []
        for key in modifiers:
            pyautogui.keyDown(key)
            pressed.append(key)
        return pressed

    def _release_modifiers(self, pressed):
        for key in reversed(pressed):
            pyautogui.keyUp(key)