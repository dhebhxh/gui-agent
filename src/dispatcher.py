# dispatcher.py
import pyautogui
import mss

class ActionDispatcher:

    def dispatch(self, action: dict) -> dict:
        action_type = action.get("type")

        handler = getattr(self, f'_do_{action_type}', None)
        if handler is None:
            raise ValueError(f"Unknown action type: {action_type}")
        
        return handler(action)

    # screenshot
    def _do_screenshot(self, action):
        with mss.MSS() as sct:
            # Get the primary monitor
            monitor = sct.monitors[0]
            sct_img = sct.grab(monitor)
            png = mss.tools.to_png(sct_img.rgb, sct_img.size)
            return {"type": "image", "data": png}

    # cursor position
    def _do_cursor_position(self, action):
        x, y = pyautogui.position()

        return {"type": "text", "data": f"[{x}, {y}]"}

    # mouse move
    def _do_mouse_move(self, action):
        pyautogui.moveTo(action.get("x"), action.get("y"))
        return {"type": "ok"}

    # left click
    def _do_left_click(self, action):
        if "x" in action and "y" in action:
            pyautogui.moveTo(action.get("x"), action.get("y"))
        pressed = self._press_modifiers(action.get("modifiers"))
        pyautogui.click(button="left")
        self._release_modifiers(pressed)
        return {"type": "ok"}

    # right click
    def _do_right_click(self, action):
        if "x" in action and "y" in action:
            pyautogui.moveTo(action.get("x"), action.get("y"))
        pressed = self._press_modifiers(action.get("modifiers"))
        pyautogui.click(button="right")
        self._release_modifiers(pressed)
        return {"type": "ok"}

    # middle click
    def _do_middle_click(self, action):
        if "x" in action and "y" in action:
            pyautogui.moveTo(action.get("x"), action.get("y"))
        pressed = self._press_modifiers(action.get("modifiers"))
        pyautogui.click(button="middle")
        self._release_modifiers(pressed)
        return {"type": "ok"}

    # left double click
    def _do_left_double_click(self, action):
        if "x" in action and "y" in action:
            pyautogui.moveTo(action.get("x"), action.get("y"))
        pressed = self._press_modifiers(action.get("modifiers"))
        pyautogui.doubleClick(button="left")
        self._release_modifiers(pressed)
        return {"type": "ok"}

    # scroll
    def _do_scroll(self, action):
        if "x" in action and "y" in action:
            pyautogui.moveTo(action.get("x"), action.get("y"))

        direction = action["direction"]
        amount = action.get("amount", 1)

        if direction == "up":
            pyautogui.scroll(amount)
        elif direction == "down":
            pyautogui.scroll(-amount)
        elif direction == "left":
            pyautogui.hscroll(-amount)
        elif direction == "right":
            pyautogui.hscroll(amount)
        else:
            raise ValueError(f"Invalid scroll direction: {direction}")

        return {"type": "ok"}

    # left click drag
    def _do_left_click_drag(self, action):
        start_x = action.get("start_x")
        start_y = action.get("start_y")
        end_x = action.get("end_x")
        end_y = action.get("end_y")

        pyautogui.moveTo(start_x, start_y)
        pressed = self._press_modifiers(action.get("modifiers"))
        pyautogui.mouseDown(button="left")
        pyautogui.moveTo(end_x, end_y)
        pyautogui.mouseUp(button="left")
        self._release_modifiers(pressed)
        return {"type": "ok"}

    # left mouse down
    def _do_left_mouse_down(self, action):
        pyautogui.mouseDown(button="left")
        return {"type": "ok"}

    # left mouse up
    def _do_left_mouse_up(self, action):
        pyautogui.mouseUp(button="left")
        return {"type": "ok"}

    # right mouse down
    def _do_right_mouse_down(self, action):
        pyautogui.mouseDown(button="right")
        return {"type": "ok"}

    # right mouse up
    def _do_right_mouse_up(self, action):
        pyautogui.mouseUp(button="right")
        return {"type": "ok"}

    # middle mouse down
    def _do_middle_mouse_down(self, action):
        pyautogui.mouseDown(button="middle")
        return {"type": "ok"}

    # middle mouse up
    def _do_middle_mouse_up(self, action):
        pyautogui.mouseUp(button="middle")
        return {"type": "ok"}

    # key press
    def _do_key_press(self, action):
        key = action.get("key")
        if len(key) == 1:
            pyautogui.press(key[0])
        else:
            for k in key:
                pyautogui.keyDown(k)
            for k in reversed(key):
                pyautogui.keyUp(k)
        return {"type": "ok"}

    # key down
    def _do_key_down(self, action):
        pyautogui.keyDown(action.get("key"))
        return {"type": "ok"}

    # key up
    def _do_key_up(self, action):
        pyautogui.keyUp(action.get("key"))
        return {"type": "ok"}

    # type text
    def _do_type_text(self, action):
        pyautogui.write(action.get("text"))
        return {"type": "ok"}

    # utility functions
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
    