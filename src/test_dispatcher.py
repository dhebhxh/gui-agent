# test_dispatcher.py
import unittest
from unittest.mock import patch, MagicMock

from dispatcher import ActionDispatcher


class TestActionDispatcherScreenshot(unittest.TestCase):
    def setUp(self):
        self.dispatcher = ActionDispatcher()

    def test_screenshot(self):
        fake_img = MagicMock()
        fake_img.rgb = b"rgb-bytes"
        fake_img.size = (100, 50)

        fake_sct = MagicMock()
        fake_sct.monitors = [{}, {"top": 0, "left": 0, "width": 1920, "height": 1080}]
        fake_sct.grab.return_value = fake_img

        with patch("dispatcher.mss.MSS") as mock_mss, \
             patch("dispatcher.mss.tools.to_png", return_value=b"png-bytes") as mock_to_png:
            mock_mss.return_value.__enter__.return_value = fake_sct

            result = self.dispatcher.dispatch({"type": "screenshot"})

            self.assertEqual(result, {"type": "image", "data": b"png-bytes"})
            fake_sct.grab.assert_called_once_with(fake_sct.monitors[0])
            mock_to_png.assert_called_once_with(b"rgb-bytes", (100, 50))


class TestActionDispatcherMouse(unittest.TestCase):
    def setUp(self):
        self.dispatcher = ActionDispatcher()

    def test_cursor_position(self):
        with patch("dispatcher.pyautogui.position", return_value=(123, 456)) as mock_pos:
            result = self.dispatcher.dispatch({"type": "cursor_position"})
            self.assertEqual(result, {"type": "text", "data": "[123, 456]"})
            mock_pos.assert_called_once()

    def test_mouse_move(self):
        with patch("dispatcher.pyautogui.moveTo") as mock_move:
            result = self.dispatcher.dispatch({"type": "mouse_move", "x": 10, "y": 20})
            self.assertEqual(result, {"type": "ok"})
            mock_move.assert_called_once_with(10, 20)

    def test_left_click_no_coords(self):
        with patch("dispatcher.pyautogui.moveTo") as mock_move, \
             patch("dispatcher.pyautogui.click") as mock_click:
            result = self.dispatcher.dispatch({"type": "left_click"})
            self.assertEqual(result, {"type": "ok"})
            mock_move.assert_not_called()
            mock_click.assert_called_once_with(button="left")

    def test_left_click_with_coords_and_modifiers(self):
        with patch("dispatcher.pyautogui.moveTo") as mock_move, \
             patch("dispatcher.pyautogui.click") as mock_click, \
             patch("dispatcher.pyautogui.keyDown") as mock_keydown, \
             patch("dispatcher.pyautogui.keyUp") as mock_keyup:
            result = self.dispatcher.dispatch({
                "type": "left_click", "x": 5, "y": 6,
                "modifiers": ["ctrl", "shift"]
            })
            self.assertEqual(result, {"type": "ok"})
            mock_move.assert_called_once_with(5, 6)
            mock_click.assert_called_once_with(button="left")
            # 按下顺序 ctrl, shift；释放为逆序 shift, ctrl
            self.assertEqual(mock_keydown.call_args_list, [
                unittest.mock.call("ctrl"), unittest.mock.call("shift")
            ])
            self.assertEqual(mock_keyup.call_args_list, [
                unittest.mock.call("shift"), unittest.mock.call("ctrl")
            ])

    def test_right_click(self):
        with patch("dispatcher.pyautogui.moveTo"), \
             patch("dispatcher.pyautogui.click") as mock_click:
            result = self.dispatcher.dispatch({"type": "right_click", "x": 1, "y": 2})
            self.assertEqual(result, {"type": "ok"})
            mock_click.assert_called_once_with(button="right")

    def test_middle_click(self):
        with patch("dispatcher.pyautogui.moveTo"), \
             patch("dispatcher.pyautogui.click") as mock_click:
            result = self.dispatcher.dispatch({"type": "middle_click"})
            self.assertEqual(result, {"type": "ok"})
            mock_click.assert_called_once_with(button="middle")

    def test_left_double_click(self):
        with patch("dispatcher.pyautogui.moveTo") as mock_move, \
             patch("dispatcher.pyautogui.doubleClick") as mock_dclick:
            result = self.dispatcher.dispatch({"type": "left_double_click", "x": 3, "y": 4})
            self.assertEqual(result, {"type": "ok"})
            mock_move.assert_called_once_with(3, 4)
            mock_dclick.assert_called_once_with(button="left")

    def test_left_click_drag(self):
        with patch("dispatcher.pyautogui.moveTo") as mock_move, \
             patch("dispatcher.pyautogui.mouseDown") as mock_down, \
             patch("dispatcher.pyautogui.mouseUp") as mock_up:
            result = self.dispatcher.dispatch({
                "type": "left_click_drag",
                "start_x": 1, "start_y": 2, "end_x": 8, "end_y": 9
            })
            self.assertEqual(result, {"type": "ok"})
            self.assertEqual(mock_move.call_args_list, [
                unittest.mock.call(1, 2), unittest.mock.call(8, 9)
            ])
            mock_down.assert_called_once_with(button="left")
            mock_up.assert_called_once_with(button="left")


class TestActionDispatcherScroll(unittest.TestCase):
    def setUp(self):
        self.dispatcher = ActionDispatcher()

    def test_scroll_up(self):
        with patch("dispatcher.pyautogui.moveTo") as mock_move, \
             patch("dispatcher.pyautogui.scroll") as mock_scroll:
            result = self.dispatcher.dispatch({
                "type": "scroll", "x": 10, "y": 20,
                "direction": "up", "amount": 3
            })
            self.assertEqual(result, {"type": "ok"})
            mock_move.assert_called_once_with(10, 20)
            mock_scroll.assert_called_once_with(3)

    def test_scroll_down(self):
        with patch("dispatcher.pyautogui.scroll") as mock_scroll:
            self.dispatcher.dispatch({"type": "scroll", "direction": "down", "amount": 2})
            mock_scroll.assert_called_once_with(-2)

    def test_scroll_left(self):
        with patch("dispatcher.pyautogui.hscroll") as mock_hscroll:
            self.dispatcher.dispatch({"type": "scroll", "direction": "left", "amount": 4})
            mock_hscroll.assert_called_once_with(-4)

    def test_scroll_right(self):
        with patch("dispatcher.pyautogui.hscroll") as mock_hscroll:
            self.dispatcher.dispatch({"type": "scroll", "direction": "right", "amount": 5})
            mock_hscroll.assert_called_once_with(5)

    def test_scroll_default_amount(self):
        with patch("dispatcher.pyautogui.scroll") as mock_scroll:
            self.dispatcher.dispatch({"type": "scroll", "direction": "up"})
            mock_scroll.assert_called_once_with(1)

    def test_scroll_invalid_direction(self):
        with self.assertRaises(ValueError) as ctx:
            self.dispatcher.dispatch({"type": "scroll", "direction": "diagonal"})
        self.assertIn("Invalid scroll direction", str(ctx.exception))


class TestActionDispatcherMouseButtons(unittest.TestCase):
    def setUp(self):
        self.dispatcher = ActionDispatcher()

    def test_left_mouse_down(self):
        with patch("dispatcher.pyautogui.mouseDown") as mock_down:
            self.assertEqual(
                self.dispatcher.dispatch({"type": "left_mouse_down"}), {"type": "ok"}
            )
            mock_down.assert_called_once_with(button="left")

    def test_left_mouse_up(self):
        with patch("dispatcher.pyautogui.mouseUp") as mock_up:
            self.dispatcher.dispatch({"type": "left_mouse_up"})
            mock_up.assert_called_once_with(button="left")

    def test_right_mouse_down(self):
        with patch("dispatcher.pyautogui.mouseDown") as mock_down:
            self.dispatcher.dispatch({"type": "right_mouse_down"})
            mock_down.assert_called_once_with(button="right")

    def test_right_mouse_up(self):
        with patch("dispatcher.pyautogui.mouseUp") as mock_up:
            self.dispatcher.dispatch({"type": "right_mouse_up"})
            mock_up.assert_called_once_with(button="right")

    def test_middle_mouse_down(self):
        with patch("dispatcher.pyautogui.mouseDown") as mock_down:
            self.dispatcher.dispatch({"type": "middle_mouse_down"})
            mock_down.assert_called_once_with(button="middle")

    def test_middle_mouse_up(self):
        with patch("dispatcher.pyautogui.mouseUp") as mock_up:
            self.dispatcher.dispatch({"type": "middle_mouse_up"})
            mock_up.assert_called_once_with(button="middle")


class TestActionDispatcherKeyboard(unittest.TestCase):
    def setUp(self):
        self.dispatcher = ActionDispatcher()

    def test_key_press_single_char(self):
        with patch("dispatcher.pyautogui.press") as mock_press:
            self.dispatcher.dispatch({"type": "key_press", "key": "a"})
            mock_press.assert_called_once_with("a")

    def test_key_press_combination(self):
        with patch("dispatcher.pyautogui.keyDown") as mock_down, \
             patch("dispatcher.pyautogui.keyUp") as mock_up:
            self.dispatcher.dispatch({"type": "key_press", "key": ["ctrl", "c"]})
            self.assertEqual(mock_down.call_args_list, [
                unittest.mock.call("ctrl"), unittest.mock.call("c")
            ])
            self.assertEqual(mock_up.call_args_list, [
                unittest.mock.call("c"), unittest.mock.call("ctrl")
            ])

    def test_key_down(self):
        with patch("dispatcher.pyautogui.keyDown") as mock_down:
            self.dispatcher.dispatch({"type": "key_down", "key": "shift"})
            mock_down.assert_called_once_with("shift")

    def test_key_up(self):
        with patch("dispatcher.pyautogui.keyUp") as mock_up:
            self.dispatcher.dispatch({"type": "key_up", "key": "shift"})
            mock_up.assert_called_once_with("shift")

    def test_type_text(self):
        with patch("dispatcher.pyautogui.write") as mock_write:
            self.dispatcher.dispatch({"type": "type_text", "text": "hello world"})
            mock_write.assert_called_once_with("hello world")


class TestActionDispatcherDispatch(unittest.TestCase):
    def setUp(self):
        self.dispatcher = ActionDispatcher()

    def test_dispatch_unknown_type_raises(self):
        # getattr 返回 None，调用 None(action) 会抛 TypeError
        with self.assertRaises(TypeError):
            self.dispatcher.dispatch({"type": "nonexistent_action"})

    def test_dispatch_routes_to_correct_handler(self):
        with patch.object(self.dispatcher, "_do_mouse_move", return_value={"type": "ok"}) as mock_handler:
            result = self.dispatcher.dispatch({"type": "mouse_move", "x": 1, "y": 2})
            self.assertEqual(result, {"type": "ok"})
            mock_handler.assert_called_once_with({"type": "mouse_move", "x": 1, "y": 2})


class TestModifierHelpers(unittest.TestCase):
    def setUp(self):
        self.dispatcher = ActionDispatcher()

    def test_press_modifiers_none(self):
        self.assertEqual(self.dispatcher._press_modifiers(None), [])

    def test_press_modifiers_empty(self):
        self.assertEqual(self.dispatcher._press_modifiers([]), [])

    def test_press_modifiers_returns_pressed(self):
        with patch("dispatcher.pyautogui.keyDown") as mock_down:
            pressed = self.dispatcher._press_modifiers(["ctrl", "alt"])
            self.assertEqual(pressed, ["ctrl", "alt"])
            self.assertEqual(mock_down.call_args_list, [
                unittest.mock.call("ctrl"), unittest.mock.call("alt")
            ])

    def test_release_modifiers_reverse_order(self):
        with patch("dispatcher.pyautogui.keyUp") as mock_up:
            self.dispatcher._release_modifiers(["ctrl", "alt"])
            self.assertEqual(mock_up.call_args_list, [
                unittest.mock.call("alt"), unittest.mock.call("ctrl")
            ])

    def test_release_modifiers_empty(self):
        with patch("dispatcher.pyautogui.keyUp") as mock_up:
            self.dispatcher._release_modifiers([])
            mock_up.assert_not_called()


if __name__ == "__main__":
    unittest.main()