# test_dispatcher.py
import pytest
from unittest import mock
from dispatcher import ActionDispatcher


# ============================================================
# _do_screenshot
# ============================================================
class TestScreenshot:

    def setup_method(self):
        self.d = ActionDispatcher()

    def test_normal(self):
        fake_img = mock.Mock()
        fake_img.rgb = b"rgb"
        fake_img.size = (100, 100)

        fake_sct = mock.MagicMock()
        fake_sct.__enter__.return_value.monitors = [
            {"left": 0, "top": 0, "width": 100, "height": 50}
        ]
        fake_sct.__enter__.return_value.grab.return_value = fake_img

        with mock.patch("dispatcher.mss.MSS", return_value=fake_sct), \
             mock.patch("dispatcher.mss.tools.to_png", return_value=b"PNGDATA"):
            r = self.d.dispatch({"type": "screenshot"})

        assert r == {"type": "image", "data": b"PNGDATA"}


# ============================================================
# _do_cursor_position
# ============================================================
class TestCursorPosition:

    def setup_method(self):
        self.d = ActionDispatcher()

    def test_normal(self):
        with mock.patch("dispatcher.pyautogui.position", return_value=(100, 200)):
            r = self.d.dispatch({"type": "cursor_position"})

        assert r == {"type": "text", "data": "[100, 200]"}


# ============================================================
# _do_mouse_move
# ============================================================
class TestMouseMove:

    def setup_method(self):
        self.d = ActionDispatcher()

    def test_normal(self):
        with mock.patch("dispatcher.pyautogui.moveTo") as mock_moveTo:
            r = self.d.dispatch({"type": "mouse_move", "x": 100, "y": 200})

        mock_moveTo.assert_called_once_with(100, 200)
        assert r == {"type": "ok"}

    @pytest.mark.parametrize("x,y", [(0, 0), (1920, 1080), (99999, 99999)])
    def test_edge(self, x, y):
        with mock.patch("dispatcher.pyautogui.moveTo") as mock_moveTo:
            r = self.d.dispatch({"type": "mouse_move", "x": x, "y": y})

        mock_moveTo.assert_called_once_with(x, y)
        assert r == {"type": "ok"}

    @pytest.mark.parametrize("x,y", [("100", 200), (100, "200"), (True, 200)])
    def test_invalid_type(self, x, y):
        with pytest.raises(TypeError):
            self.d.dispatch({"type": "mouse_move", "x": x, "y": y})

    @pytest.mark.parametrize("action", [
        {"type": "mouse_move"},
        {"type": "mouse_move", "x": 100},
        {"type": "mouse_move", "y": 200},
    ])
    def test_missing(self, action):
        with pytest.raises(ValueError):
            self.d.dispatch(action)


# ============================================================
# left / right / middle click + left double click
# ============================================================
class TestClicks:

    def setup_method(self):
        self.d = ActionDispatcher()

    @pytest.mark.parametrize("atype,button", [
        ("left_click", "left"),
        ("right_click", "right"),
        ("middle_click", "middle"),
    ])
    def test_normal(self, atype, button):
        cases = [
            {"type": atype},
            {"type": atype, "x": 100, "y": 200},
            {"type": atype, "x": 100, "y": 200, "modifiers": ["ctrl"]},
        ]
        for c in cases:
            with mock.patch("dispatcher.pyautogui.moveTo") as m_move, \
                 mock.patch("dispatcher.pyautogui.click") as m_click, \
                 mock.patch("dispatcher.pyautogui.keyDown") as m_down, \
                 mock.patch("dispatcher.pyautogui.keyUp") as m_up:
                r = self.d.dispatch(c)

            assert r == {"type": "ok"}
            m_click.assert_called_once_with(button=button)

            if "x" in c and "y" in c:
                m_move.assert_called_once_with(c["x"], c["y"])
            else:
                m_move.assert_not_called()

            mods = c.get("modifiers")
            if mods:
                for m in mods:
                    m_down.assert_any_call(m)
                    m_up.assert_any_call(m)
            else:
                m_down.assert_not_called()
                m_up.assert_not_called()

    @pytest.mark.parametrize("atype", ["left_click", "right_click", "middle_click"])
    def test_normal_none_coord(self, atype):
        # x=None, y=None 视为未提供坐标 → 在当前鼠标位置点击
        with mock.patch("dispatcher.pyautogui.moveTo") as m_move, \
             mock.patch("dispatcher.pyautogui.click") as m_click:
            r = self.d.dispatch({"type": atype, "x": None, "y": None})

        m_move.assert_not_called()
        m_click.assert_called_once()
        assert r == {"type": "ok"}
        
    @pytest.mark.parametrize("atype", ["left_click", "right_click", "middle_click"])
    @pytest.mark.parametrize("x,y", [(0, 0), (1920, 1080), (99999, 99999)])
    def test_edge_coord(self, atype, x, y):
        with mock.patch("dispatcher.pyautogui.moveTo") as m_move, \
             mock.patch("dispatcher.pyautogui.click"):
            r = self.d.dispatch({"type": atype, "x": x, "y": y})

        m_move.assert_called_once_with(x, y)
        assert r == {"type": "ok"}

    @pytest.mark.parametrize("atype", ["left_click", "right_click", "middle_click"])
    def test_edge_modifiers_empty(self, atype):
        with mock.patch("dispatcher.pyautogui.click"), \
             mock.patch("dispatcher.pyautogui.keyDown") as m_down, \
             mock.patch("dispatcher.pyautogui.keyUp") as m_up:
            r = self.d.dispatch({"type": atype, "x": 10, "y": 10, "modifiers": []})

        m_down.assert_not_called()
        m_up.assert_not_called()
        assert r == {"type": "ok"}

    @pytest.mark.parametrize("atype", ["left_click", "right_click", "middle_click"])
    def test_edge_modifiers_case(self, atype):
        # 源码归一化小写
        with mock.patch("dispatcher.pyautogui.click"), \
             mock.patch("dispatcher.pyautogui.keyDown") as m_down, \
             mock.patch("dispatcher.pyautogui.keyUp") as m_up:
            r = self.d.dispatch({"type": atype, "x": 10, "y": 10, "modifiers": ["Ctrl"]})

        m_down.assert_called_once_with("ctrl")
        m_up.assert_called_once_with("ctrl")
        assert r == {"type": "ok"}

    @pytest.mark.parametrize("atype", ["left_click", "right_click", "middle_click"])
    @pytest.mark.parametrize("bad", [
        {"x": "100", "y": 200},
        {"x": True, "y": False},
        {"x": 10, "y": 10, "modifiers": "ctrl"},
        {"x": 10, "y": 10, "modifiers": [1, 2]},
        {"x": 10, "y": 10, "modifiers": ["nokey"]},
    ])
    def test_invalid(self, atype, bad):
        with pytest.raises((TypeError, ValueError)):
            self.d.dispatch({"type": atype, **bad})

    @pytest.mark.parametrize("atype", ["left_click", "right_click", "middle_click"])
    @pytest.mark.parametrize("action", [
        {"type": "left_click", "x": 100},   # 只给 x
        {"type": "left_click", "y": 100},   # 只给 y
    ])
    def test_invalid_partial_coord(self, atype, action):
        action = dict(action)
        action["type"] = atype
        with pytest.raises(ValueError):
            self.d.dispatch(action)


class TestLeftDoubleClick:

    def setup_method(self):
        self.d = ActionDispatcher()

    def test_normal(self):
        with mock.patch("dispatcher.pyautogui.moveTo") as m_move, \
             mock.patch("dispatcher.pyautogui.doubleClick") as m_dbl:
            r = self.d.dispatch({"type": "left_double_click", "x": 10, "y": 20})

        m_move.assert_called_once_with(10, 20)
        m_dbl.assert_called_once_with(button="left")
        assert r == {"type": "ok"}

    def test_normal_no_coord(self):
        with mock.patch("dispatcher.pyautogui.moveTo") as m_move, \
             mock.patch("dispatcher.pyautogui.doubleClick"):
            r = self.d.dispatch({"type": "left_double_click"})

        m_move.assert_not_called()
        assert r == {"type": "ok"}

    def test_normal_with_modifiers(self):
        with mock.patch("dispatcher.pyautogui.moveTo"), \
             mock.patch("dispatcher.pyautogui.doubleClick"), \
             mock.patch("dispatcher.pyautogui.keyDown") as m_down, \
             mock.patch("dispatcher.pyautogui.keyUp") as m_up:
            r = self.d.dispatch({
                "type": "left_double_click", "x": 10, "y": 20,
                "modifiers": ["shift"],
            })

        m_down.assert_called_once_with("shift")
        m_up.assert_called_once_with("shift")
        assert r == {"type": "ok"}

    def test_normal_none_coord(self):
        with mock.patch("dispatcher.pyautogui.moveTo") as m_move, \
             mock.patch("dispatcher.pyautogui.doubleClick") as m_dbl:
            r = self.d.dispatch(
                {"type": "left_double_click", "x": None, "y": None}
            )

        m_move.assert_not_called()
        m_dbl.assert_called_once_with(button="left")
        assert r == {"type": "ok"}

    def test_invalid_partial_coord(self):
        with pytest.raises(ValueError):
            self.d.dispatch({"type": "left_double_click", "x": 10})
        with pytest.raises(ValueError):
            self.d.dispatch({"type": "left_double_click", "y": 20})

    @pytest.mark.parametrize("x,y", [(0, 0), (1920, 1080), (99999, 99999)])
    def test_edge_coord(self, x, y):
        with mock.patch("dispatcher.pyautogui.moveTo") as m_move, \
             mock.patch("dispatcher.pyautogui.doubleClick"):
            r = self.d.dispatch({"type": "left_double_click", "x": x, "y": y})

        m_move.assert_called_once_with(x, y)
        assert r == {"type": "ok"}

    def test_edge_modifiers_empty(self):
        with mock.patch("dispatcher.pyautogui.doubleClick"), \
             mock.patch("dispatcher.pyautogui.keyDown") as m_down:
            r = self.d.dispatch({
                "type": "left_double_click", "x": 1, "y": 1, "modifiers": [],
            })

        m_down.assert_not_called()
        assert r == {"type": "ok"}

    def test_edge_modifiers_case(self):
        with mock.patch("dispatcher.pyautogui.doubleClick"), \
             mock.patch("dispatcher.pyautogui.keyDown") as m_down:
            r = self.d.dispatch({
                "type": "left_double_click", "x": 1, "y": 1, "modifiers": ["Ctrl"],
            })

        m_down.assert_called_once_with("ctrl")
        assert r == {"type": "ok"}

    @pytest.mark.parametrize("bad", [
        {"x": "10", "y": 20},
        {"x": True, "y": False},
        {"x": 1, "y": 1, "modifiers": "ctrl"},
        {"x": 1, "y": 1, "modifiers": [1, 2]},
        {"x": 1, "y": 1, "modifiers": ["unknown"]},
    ])
    def test_invalid(self, bad):
        with pytest.raises((TypeError, ValueError)):
            self.d.dispatch({"type": "left_double_click", **bad})


# ============================================================
# _do_scroll
# ============================================================
class TestScroll:

    def setup_method(self):
        self.d = ActionDispatcher()

    @pytest.mark.parametrize("direction,amount,method,arg", [
        ("up",    1, "scroll",  1),
        ("up",    5, "scroll",  5),
        ("down",  1, "scroll", -1),
        ("down",  5, "scroll", -5),
        ("left",  1, "hscroll", -1),
        ("right", 1, "hscroll",  1),
    ])
    def test_normal(self, direction, amount, method, arg):
        with mock.patch(f"dispatcher.pyautogui.{method}") as m:
            r = self.d.dispatch({
                "type": "scroll", "direction": direction, "amount": amount,
            })

        m.assert_called_once_with(arg)
        assert r == {"type": "ok"}

    def test_normal_default_amount(self):
        with mock.patch("dispatcher.pyautogui.scroll") as m:
            r = self.d.dispatch({"type": "scroll", "direction": "up"})

        m.assert_called_once_with(1)
        assert r == {"type": "ok"}

    def test_normal_with_coord(self):
        with mock.patch("dispatcher.pyautogui.moveTo") as m_move, \
             mock.patch("dispatcher.pyautogui.scroll"):
            r = self.d.dispatch({
                "type": "scroll", "direction": "down", "amount": 3,
                "x": 10, "y": 20,
            })

        m_move.assert_called_once_with(10, 20)
        assert r == {"type": "ok"}

    @pytest.mark.parametrize("amount", [0, 1000, 999999])
    def test_edge_amount(self, amount):
        with mock.patch("dispatcher.pyautogui.scroll") as m:
            r = self.d.dispatch({
                "type": "scroll", "direction": "down", "amount": amount,
            })

        m.assert_called_once_with(-amount)
        assert r == {"type": "ok"}

    @pytest.mark.parametrize("amount", ["big", None])
    def test_invalid_amount(self, amount):
        with pytest.raises(TypeError):
            self.d.dispatch({"type": "scroll", "direction": "down", "amount": amount})

    @pytest.mark.parametrize("direction", ["diagonal", 123])
    def test_invalid_direction(self, direction):
        with pytest.raises(ValueError):
            self.d.dispatch({"type": "scroll", "direction": direction})

    def test_missing_direction(self):
        with pytest.raises(ValueError):
            self.d.dispatch({"type": "scroll"})

    def test_invalid_partial_coord(self):
        with pytest.raises(ValueError):
            self.d.dispatch({"type": "scroll", "direction": "down", "x": 10})


# ============================================================
# _do_left_click_drag
# ============================================================
class TestLeftClickDrag:

    def setup_method(self):
        self.d = ActionDispatcher()

    def test_normal(self):
        with mock.patch("dispatcher.pyautogui.moveTo") as m_move, \
             mock.patch("dispatcher.pyautogui.mouseDown") as m_down, \
             mock.patch("dispatcher.pyautogui.mouseUp") as m_up:
            r = self.d.dispatch({
                "type": "left_click_drag",
                "start_x": 0, "start_y": 0, "end_x": 100, "end_y": 200,
            })

        assert m_move.call_args_list == [mock.call(0, 0), mock.call(100, 200)]
        m_down.assert_called_once_with(button="left")
        m_up.assert_called_once_with(button="left")
        assert r == {"type": "ok"}

    def test_normal_no_start(self):
        # 不给起点 → 用当前位置
        with mock.patch("dispatcher.pyautogui.position", return_value=(5, 6)) as m_pos, \
             mock.patch("dispatcher.pyautogui.moveTo") as m_move, \
             mock.patch("dispatcher.pyautogui.mouseDown"), \
             mock.patch("dispatcher.pyautogui.mouseUp"):
            r = self.d.dispatch({
                "type": "left_click_drag", "end_x": 100, "end_y": 200,
            })

        m_pos.assert_called_once()
        assert m_move.call_args_list == [mock.call(5, 6), mock.call(100, 200)]
        assert r == {"type": "ok"}

    def test_normal_with_modifiers(self):
        with mock.patch("dispatcher.pyautogui.moveTo"), \
             mock.patch("dispatcher.pyautogui.mouseDown"), \
             mock.patch("dispatcher.pyautogui.mouseUp"), \
             mock.patch("dispatcher.pyautogui.keyDown") as m_down, \
             mock.patch("dispatcher.pyautogui.keyUp") as m_up:
            r = self.d.dispatch({
                "type": "left_click_drag",
                "start_x": 0, "start_y": 0, "end_x": 10, "end_y": 10,
                "modifiers": ["shift"],
            })

        m_down.assert_called_once_with("shift")
        m_up.assert_called_once_with("shift")
        assert r == {"type": "ok"}

    def test_edge_same_point(self):
        with mock.patch("dispatcher.pyautogui.moveTo") as m_move, \
             mock.patch("dispatcher.pyautogui.mouseDown"), \
             mock.patch("dispatcher.pyautogui.mouseUp"):
            r = self.d.dispatch({
                "type": "left_click_drag",
                "start_x": 10, "start_y": 10, "end_x": 10, "end_y": 10,
            })

        assert m_move.call_args_list == [mock.call(10, 10), mock.call(10, 10)]
        assert r == {"type": "ok"}

    @pytest.mark.parametrize("start,end", [
        ((0, 0), (100, 200)),
        ((99999, 99999), (0, 0)),
    ])
    def test_edge_coord(self, start, end):
        with mock.patch("dispatcher.pyautogui.moveTo") as m_move, \
             mock.patch("dispatcher.pyautogui.mouseDown"), \
             mock.patch("dispatcher.pyautogui.mouseUp"):
            r = self.d.dispatch({
                "type": "left_click_drag",
                "start_x": start[0], "start_y": start[1],
                "end_x": end[0], "end_y": end[1],
            })

        assert m_move.call_args_list == [
            mock.call(start[0], start[1]), mock.call(end[0], end[1]),
        ]
        assert r == {"type": "ok"}

    def test_edge_modifiers_empty(self):
        with mock.patch("dispatcher.pyautogui.moveTo"), \
             mock.patch("dispatcher.pyautogui.mouseDown"), \
             mock.patch("dispatcher.pyautogui.mouseUp"), \
             mock.patch("dispatcher.pyautogui.keyDown") as m_down:
            r = self.d.dispatch({
                "type": "left_click_drag",
                "start_x": 0, "start_y": 0, "end_x": 1, "end_y": 1,
                "modifiers": [],
            })

        m_down.assert_not_called()
        assert r == {"type": "ok"}

    def test_edge_modifiers_case(self):
        with mock.patch("dispatcher.pyautogui.moveTo"), \
             mock.patch("dispatcher.pyautogui.mouseDown"), \
             mock.patch("dispatcher.pyautogui.mouseUp"), \
             mock.patch("dispatcher.pyautogui.keyDown") as m_down:
            r = self.d.dispatch({
                "type": "left_click_drag",
                "start_x": 0, "start_y": 0, "end_x": 1, "end_y": 1,
                "modifiers": ["Ctrl"],
            })

        m_down.assert_called_once_with("ctrl")
        assert r == {"type": "ok"}

    @pytest.mark.parametrize("bad", [
        {"end_x": "100", "end_y": 200},
        {"end_x": None, "end_y": None},
        {"end_x": True, "end_y": False},
        {"end_x": 1, "end_y": 1, "modifiers": "ctrl"},
        {"end_x": 1, "end_y": 1, "modifiers": [1, 2]},
        {"end_x": 1, "end_y": 1, "modifiers": ["unknown"]},
    ])
    def test_invalid(self, bad):
        with pytest.raises((TypeError, ValueError)):
            self.d.dispatch({"type": "left_click_drag", **bad})

    @pytest.mark.parametrize("action", [
        {"type": "left_click_drag"},
        {"type": "left_click_drag", "end_y": 100},
        {"type": "left_click_drag", "end_x": 100},
    ])
    def test_missing_end(self, action):
        with pytest.raises(ValueError):
            self.d.dispatch(action)

    def test_invalid_partial_start(self):
        with pytest.raises(ValueError):
            self.d.dispatch({
                "type": "left_click_drag", "start_x": 0,
                "end_x": 100, "end_y": 200,
            })
        with pytest.raises(ValueError):
            self.d.dispatch({
                "type": "left_click_drag", "start_y": 0,
                "end_x": 100, "end_y": 200,
            })


# ============================================================
# mouse down / up
# ============================================================
class TestMouseDownUp:

    def setup_method(self):
        self.d = ActionDispatcher()

    @pytest.mark.parametrize("atype,method,button", [
        ("left_mouse_down",   "mouseDown", "left"),
        ("left_mouse_up",     "mouseUp",   "left"),
        ("right_mouse_down",  "mouseDown", "right"),
        ("right_mouse_up",    "mouseUp",   "right"),
        ("middle_mouse_down", "mouseDown", "middle"),
        ("middle_mouse_up",   "mouseUp",   "middle"),
    ])
    def test_normal(self, atype, method, button):
        with mock.patch(f"dispatcher.pyautogui.{method}") as m:
            r = self.d.dispatch({"type": atype})

        m.assert_called_once_with(button=button)
        assert r == {"type": "ok"}

    @pytest.mark.parametrize("atype,method,button", [
        ("left_mouse_down",   "mouseDown", "left"),
        ("right_mouse_down",  "mouseDown", "right"),
        ("middle_mouse_down", "mouseDown", "middle"),
    ])
    def test_edge_double_down(self, atype, method, button):
        with mock.patch(f"dispatcher.pyautogui.{method}") as m:
            self.d.dispatch({"type": atype})
            self.d.dispatch({"type": atype})

        assert m.call_count == 2
        m.assert_called_with(button=button)

    @pytest.mark.parametrize("atype,method,button", [
        ("left_mouse_up",   "mouseUp", "left"),
        ("right_mouse_up",  "mouseUp", "right"),
        ("middle_mouse_up", "mouseUp", "middle"),
    ])
    def test_edge_orphan_up(self, atype, method, button):
        with mock.patch(f"dispatcher.pyautogui.{method}") as m:
            self.d.dispatch({"type": atype})

        m.assert_called_once_with(button=button)


# ============================================================
# _do_key_press
# ============================================================
class TestKeyPress:

    def setup_method(self):
        self.d = ActionDispatcher()

    def test_normal_single(self):
        with mock.patch("dispatcher.pyautogui.press") as m_press:
            r = self.d.dispatch({"type": "key_press", "key": ["a"]})

        m_press.assert_called_once_with("a")
        assert r == {"type": "ok"}

    def test_normal_single_str(self):
        # str 形式也接受
        with mock.patch("dispatcher.pyautogui.press") as m_press:
            r = self.d.dispatch({"type": "key_press", "key": "a"})

        m_press.assert_called_once_with("a")
        assert r == {"type": "ok"}

    def test_normal_multi(self):
        with mock.patch("dispatcher.pyautogui.press") as m_press, \
             mock.patch("dispatcher.pyautogui.keyDown") as m_down, \
             mock.patch("dispatcher.pyautogui.keyUp") as m_up:
            r = self.d.dispatch({"type": "key_press", "key": ["ctrl", "c"]})

        m_press.assert_not_called()
        m_down.assert_any_call("ctrl")
        m_down.assert_any_call("c")
        m_up.assert_any_call("ctrl")
        m_up.assert_any_call("c")
        assert r == {"type": "ok"}

    def test_normal_function_key(self):
        with mock.patch("dispatcher.pyautogui.press") as m_press:
            r = self.d.dispatch({"type": "key_press", "key": ["f5"]})

        m_press.assert_called_once_with("f5")
        assert r == {"type": "ok"}

    def test_edge_duplicate_key(self):
        with mock.patch("dispatcher.pyautogui.press"), \
             mock.patch("dispatcher.pyautogui.keyDown") as m_down, \
             mock.patch("dispatcher.pyautogui.keyUp") as m_up:
            r = self.d.dispatch({"type": "key_press", "key": ["a", "a"]})

        assert m_down.call_count == 2
        assert m_up.call_count == 2
        assert r == {"type": "ok"}

    def test_edge_case(self):
        # 归一化为小写
        with mock.patch("dispatcher.pyautogui.press") as m_press:
            r = self.d.dispatch({"type": "key_press", "key": ["ENTER"]})

        m_press.assert_called_once_with("enter")
        assert r == {"type": "ok"}

    @pytest.mark.parametrize("key", [None, 123])
    def test_invalid_type(self, key):
        with pytest.raises((TypeError, ValueError)):
            self.d.dispatch({"type": "key_press", "key": key})

    def test_invalid_empty_list(self):
        with pytest.raises(ValueError):
            self.d.dispatch({"type": "key_press", "key": []})

    def test_invalid_unknown_key(self):
        with pytest.raises(ValueError):
            self.d.dispatch({"type": "key_press", "key": ["nokey"]})

    def test_missing(self):
        with pytest.raises(ValueError):
            self.d.dispatch({"type": "key_press"})


# ============================================================
# _do_key_down / _do_key_up
# ============================================================
class TestKeyDownUp:

    def setup_method(self):
        self.d = ActionDispatcher()

    @pytest.mark.parametrize("atype,method", [
        ("key_down", "keyDown"),
        ("key_up",   "keyUp"),
    ])
    def test_normal(self, atype, method):
        with mock.patch(f"dispatcher.pyautogui.{method}") as m:
            r = self.d.dispatch({"type": atype, "key": "a"})

        m.assert_called_once_with("a")
        assert r == {"type": "ok"}

    @pytest.mark.parametrize("atype,method", [
        ("key_down", "keyDown"),
        ("key_up",   "keyUp"),
    ])
    def test_normal_function_key(self, atype, method):
        with mock.patch(f"dispatcher.pyautogui.{method}") as m:
            r = self.d.dispatch({"type": atype, "key": "enter"})

        m.assert_called_once_with("enter")
        assert r == {"type": "ok"}

    @pytest.mark.parametrize("atype,method", [
        ("key_down", "keyDown"),
        ("key_up",   "keyUp"),
    ])
    def test_edge_continuous(self, atype, method):
        with mock.patch(f"dispatcher.pyautogui.{method}") as m:
            self.d.dispatch({"type": atype, "key": "a"})
            self.d.dispatch({"type": atype, "key": "a"})

        assert m.call_count == 2

    @pytest.mark.parametrize("atype,method", [
        ("key_down", "keyDown"),
        ("key_up",   "keyUp"),
    ])
    def test_edge_case(self, atype, method):
        # 归一化为小写
        with mock.patch(f"dispatcher.pyautogui.{method}") as m:
            r = self.d.dispatch({"type": atype, "key": "ENTER"})

        m.assert_called_once_with("enter")
        assert r == {"type": "ok"}

    @pytest.mark.parametrize("atype,method", [
        ("key_down", "keyDown"),
        ("key_up",   "keyUp"),
    ])
    @pytest.mark.parametrize("key", [123, ["a", "b"]])
    def test_invalid(self, atype, method, key):
        with pytest.raises(TypeError):
            self.d.dispatch({"type": atype, "key": key})

    @pytest.mark.parametrize("atype,method", [
        ("key_down", "keyDown"),
        ("key_up",   "keyUp"),
    ])
    def test_invalid_none(self, atype, method):
        with pytest.raises(ValueError):
            self.d.dispatch({"type": atype, "key": None})

    @pytest.mark.parametrize("atype,method", [
        ("key_down", "keyDown"),
        ("key_up",   "keyUp"),
    ])
    def test_missing(self, atype, method):
        with pytest.raises(ValueError):
            self.d.dispatch({"type": atype})


# ============================================================
# _do_type_text
# ============================================================
class TestTypeText:

    def setup_method(self):
        self.d = ActionDispatcher()

    def test_normal(self):
        with mock.patch("dispatcher.pyautogui.write") as m:
            r = self.d.dispatch({"type": "type_text", "text": "hello world"})

        m.assert_called_once_with("hello world")
        assert r == {"type": "ok"}

    def test_normal_mixed_case(self):
        with mock.patch("dispatcher.pyautogui.write") as m:
            r = self.d.dispatch({"type": "type_text", "text": "Hello World 123"})

        m.assert_called_once_with("Hello World 123")
        assert r == {"type": "ok"}

    def test_edge_chinese_emoji(self):
        with mock.patch("dispatcher.pyautogui.write") as m:
            r = self.d.dispatch({"type": "type_text", "text": "中文表情😀"})

        m.assert_called_once_with("中文表情😀")
        assert r == {"type": "ok"}

    def test_edge_newline_tab(self):
        with mock.patch("dispatcher.pyautogui.write") as m:
            r = self.d.dispatch({"type": "type_text", "text": "line1\nline2\tTab"})

        m.assert_called_once_with("line1\nline2\tTab")
        assert r == {"type": "ok"}

    @pytest.mark.parametrize("text", [None])
    def test_invalid_none(self, text):
        with pytest.raises(ValueError):
            self.d.dispatch({"type": "type_text", "text": text})

    @pytest.mark.parametrize("text", [123, ["a"]])
    def test_invalid_type(self, text):
        with pytest.raises(TypeError):
            self.d.dispatch({"type": "type_text", "text": text})

    def test_invalid_empty(self):
        with pytest.raises(ValueError):
            self.d.dispatch({"type": "type_text", "text": ""})

    def test_missing(self):
        with pytest.raises(ValueError):
            self.d.dispatch({"type": "type_text"})