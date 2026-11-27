
from state import AgentState
import cv2
import numpy as np


class ActionVerifier:

    def verify(self, state: AgentState) -> dict:
        last_action = state.get("last_action")

        if state.get("old_resized_screenshot") is None:
            return self._result("skipped", "No previous screenshot")

        if not isinstance(last_action, dict):
            return self._result("error", "Missing last_action")

        action_type = last_action.get("type")

        dispatch = {
            "left_single_click": self.verify_left_single_click,
            "right_single_click": self.verify_right_single_click,
            "left_double_click": self.verify_left_double_click,
            "left_click_drag": self.verify_left_click_drag,
            "type_text": self.verify_type_text,
            "scroll": self.verify_scroll,
        }

        verifier = dispatch.get(action_type)

        if verifier is None:
            return self._result("uncertain", "Unsupported action")

        return verifier(state)

    # =========================================================
    # Common Helpers
    # =========================================================

    def _decode_screenshots(self, state, resize_mismatch=True):
        old_screenshot = state.get("old_resized_screenshot")
        new_screenshot = state.get("resized_screenshot")

        if old_screenshot is None or new_screenshot is None:
            return None, None, "Missing screenshots"

        old_img = cv2.imdecode(
            np.frombuffer(old_screenshot, np.uint8),
            cv2.IMREAD_GRAYSCALE
        )

        new_img = cv2.imdecode(
            np.frombuffer(new_screenshot, np.uint8),
            cv2.IMREAD_GRAYSCALE
        )

        if old_img is None or new_img is None:
            return None, None, "Failed to decode screenshots"

        if old_img.shape != new_img.shape:
            if not resize_mismatch:
                return None, None, "Screenshot dimensions mismatch"

            new_img = cv2.resize(
                new_img,
                (old_img.shape[1], old_img.shape[0]),
                interpolation=cv2.INTER_AREA
            )

        return old_img, new_img, None

    @staticmethod
    def _get_image_diff(old_img, new_img, threshold=25):
        diff = cv2.absdiff(old_img, new_img)
        mask = diff > threshold

        return {
            "changed_ratio": float(np.mean(mask)),
            "mean_diff": float(np.mean(diff))
        }

    @staticmethod
    def _get_roi(img, x, y, radius_x, radius_y=None):
        if radius_y is None:
            radius_y = radius_x

        h, w = img.shape

        x1 = max(0, int(x) - radius_x)
        y1 = max(0, int(y) - radius_y)
        x2 = min(w, int(x) + radius_x)
        y2 = min(h, int(y) + radius_y)

        return img[y1:y2, x1:x2]

    @staticmethod
    def _get_click_bbox(x, y, elements):
        clicked_bbox = None
        smallest_area = float("inf")

        for element in elements:
            bbox = element.get("bbox")

            if not bbox or len(bbox) != 4:
                continue

            x1, y1, x2, y2 = bbox

            if x1 <= x <= x2 and y1 <= y <= y2:
                area = (x2 - x1) * (y2 - y1)

                if area < smallest_area:
                    clicked_bbox = bbox
                    smallest_area = area

        return clicked_bbox

    @staticmethod
    def _result(status, reason):
        return {
            "type": "verification",
            "status": status,
            "reason": reason
        }

    @staticmethod
    def _compare(old_img, new_img):
        return ActionVerifier._get_image_diff(old_img, new_img)

    # =========================================================
    # Action Verifiers
    # =========================================================

    def verify_left_single_click(self, state):
        action = state["last_action"]
        x, y = action["x"], action["y"]

        old_img, new_img, error = self._decode_screenshots(
            state,
            resize_mismatch=False
        )

        if error:
            return self._result("uncertain", error)

        h, w = old_img.shape

        clicked_bbox = self._get_click_bbox(
            x, y, state.get("old_elements", [])
        )

        if clicked_bbox is not None:
            x1, y1, x2, y2 = clicked_bbox
        else:
            x1, y1 = x - 50, y - 50
            x2, y2 = x + 50, y + 50

        padding = 10

        x1 = max(0, int(x1) - padding)
        y1 = max(0, int(y1) - padding)
        x2 = min(w, int(x2) + padding)
        y2 = min(h, int(y2) + padding)

        if x1 >= x2 or y1 >= y2:
            return self._result("uncertain", "Invalid click region")

        local = self._compare(
            old_img[y1:y2, x1:x2],
            new_img[y1:y2, x1:x2]
        )

        global_diff = self._compare(old_img, new_img)

        if local["changed_ratio"] > 0.02 or global_diff["changed_ratio"] > 0.01:
            return self._result("success", "Visible change after left click")

        return self._result("failure", "No visible change after left click")

    def verify_right_single_click(self, state):
        action = state["last_action"]
        x, y = action["x"], action["y"]

        old_img, new_img, error = self._decode_screenshots(state)

        if error:
            return self._result("uncertain", error)

        h, w = old_img.shape

        clicked_bbox = self._get_click_bbox(
            x, y, state.get("old_elements", [])
        )

        if clicked_bbox is not None:
            x1, y1, x2, y2 = clicked_bbox
        else:
            x1, y1 = x - 50, y - 50
            x2, y2 = x + 50, y + 50

        padding = 10

        x1 = max(0, int(x1) - padding)
        y1 = max(0, int(y1) - padding)
        x2 = min(w, int(x2) + padding)
        y2 = min(h, int(y2) + padding)

        if x1 >= x2 or y1 >= y2:
            return self._result("uncertain", "Invalid click region")

        local = self._compare(
            old_img[y1:y2, x1:x2],
            new_img[y1:y2, x1:x2]
        )

        global_diff = self._compare(old_img, new_img)

        if local["changed_ratio"] > 0.02 or global_diff["changed_ratio"] > 0.01:
            return self._result("success", "Visible change after right click")

        return self._result("failure", "No visible change after right click")

    def verify_left_double_click(self, state):
        old_img, new_img, error = self._decode_screenshots(state)

        if error:
            return self._result("uncertain", error)

        global_diff = self._compare(old_img, new_img)

        if global_diff["changed_ratio"] > 0.01:
            return self._result("success", "Visible change after double click")

        return self._result("failure", "No visible change after double click")

    def verify_left_click_drag(self, state):
        action = state["last_action"]

        required_coords = [
            "start_x", "start_y", "end_x", "end_y"
        ]

        if not all(k in action for k in required_coords):
            return self._result("uncertain", "Missing drag coordinates")

        old_img, new_img, error = self._decode_screenshots(state)

        if error:
            return self._result("uncertain", error)

        radius = 50

        old_start = self._get_roi(
            old_img, action["start_x"], action["start_y"], radius
        )
        new_start = self._get_roi(
            new_img, action["start_x"], action["start_y"], radius
        )

        old_end = self._get_roi(
            old_img, action["end_x"], action["end_y"], radius
        )
        new_end = self._get_roi(
            new_img, action["end_x"], action["end_y"], radius
        )

        if old_start.size == 0 or old_end.size == 0:
            return self._result("uncertain", "Invalid drag coordinates")

        start_diff = self._compare(old_start, new_start)
        end_diff = self._compare(old_end, new_end)
        global_diff = self._compare(old_img, new_img)

        if (
            start_diff["changed_ratio"] > 0.02
            and end_diff["changed_ratio"] > 0.02
        ):
            return self._result("success", "Visible changes around drag positions")

        if global_diff["changed_ratio"] > 0.01:
            return self._result("uncertain", "Screen changed but drag effect is unclear")

        return self._result("failure", "No visible change after drag")

    def verify_type_text(self, state):
        action = state["last_action"]
        x, y = action["x"], action["y"]

        old_img, new_img, error = self._decode_screenshots(state)

        if error:
            return self._result("uncertain", error)

        old_roi = self._get_roi(
            old_img, x, y, radius_x=150, radius_y=50
        )

        new_roi = self._get_roi(
            new_img, x, y, radius_x=150, radius_y=50
        )

        if old_roi.size == 0:
            return self._result("uncertain", "Invalid input coordinates")

        local_diff = self._compare(old_roi, new_roi)

        if local_diff["changed_ratio"] > 0.02:
            return self._result("success", "Visible change around input field")

        return self._result("failure", "No visible change around input field")

    def verify_scroll(self, state):
        action = state["last_action"]
        x, y = action["x"], action["y"]

        old_img, new_img, error = self._decode_screenshots(state)

        if error:
            return self._result("uncertain", error)

        old_roi = self._get_roi(
            old_img, x, y, radius_x=300, radius_y=200
        )

        new_roi = self._get_roi(
            new_img, x, y, radius_x=300, radius_y=200
        )

        if old_roi.size == 0:
            return self._result("uncertain", "Invalid scroll coordinates")

        local_diff = self._compare(old_roi, new_roi)

        if local_diff["changed_ratio"] > 0.02:
            return self._result("success", "Visible change in scroll region")

        return self._result("failure", "No visible change in scroll region")
