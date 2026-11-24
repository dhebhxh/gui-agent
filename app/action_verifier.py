
from state import AgentState
import cv2
import numpy as np


class ActionVerifier:

    def verify(self, state: AgentState) -> dict:
        last_action = state.get("last_action")

        if state.get("old_resized_screenshot") is None:
            return self._result("skipped", "No previous screenshot")

        if not last_action:
            return self._result("error", "Missing last_action")

        action_type = last_action.get("type")

        dispatch = {
            "LeftSingleClickAction": self.verify_left_single_click,
            "RightSingleClickAction": self.verify_right_single_click,
            "LeftDoubleClickAction": self.verify_left_double_click,
            "LeftClickDragAction": self.verify_left_click_drag,
            "TypeTextAction": self.verify_type_text,
            "ScrollAction": self.verify_scroll,
        }

        verifier = dispatch.get(action_type)

        if verifier is None:
            return self._result("uncertain", "Unsupported action")

        return verifier(state)

    # =========================================================
    # Common Helpers
    # =========================================================

    def _decode_screenshots(self, state, resize_mismatch=True):
        """Decode old and new screenshots into grayscale images."""

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
                return None, None, "Screenshot dimensions do not match"

            new_img = cv2.resize(
                new_img,
                (old_img.shape[1], old_img.shape[0]),
                interpolation=cv2.INTER_AREA
            )

        return old_img, new_img, None

    @staticmethod
    def _get_image_diff(old_img, new_img, threshold=25):
        """Calculate image differences and extract changed regions."""

        diff = cv2.absdiff(old_img, new_img)

        mask = diff > threshold

        changed_ratio = np.count_nonzero(mask) / mask.size
        mean_diff = float(np.mean(diff))

        binary_mask = mask.astype(np.uint8) * 255

        contours, _ = cv2.findContours(
            binary_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        changed_regions = []

        for contour in contours:
            area = cv2.contourArea(contour)

            if area < 20:
                continue

            x, y, w, h = cv2.boundingRect(contour)

            changed_regions.append({
                "bbox": [x, y, x + w, y + h],
                "area": area
            })

        return {
            "diff": diff,
            "mask": binary_mask,
            "changed_ratio": float(changed_ratio),
            "mean_diff": mean_diff,
            "changed_regions": changed_regions
        }

    @staticmethod
    def _get_roi(img, x, y, radius_x, radius_y=None):
        """Extract a bounded ROI around a given position."""

        if radius_y is None:
            radius_y = radius_x

        h, w = img.shape

        x1 = max(0, int(x) - radius_x)
        y1 = max(0, int(y) - radius_y)
        x2 = min(w, int(x) + radius_x)
        y2 = min(h, int(y) + radius_y)

        return img[y1:y2, x1:x2], (x1, y1, x2, y2)

    @staticmethod
    def _get_click_bbox(x, y, elements):
        """Find the smallest UI element containing the click position."""

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
    def _convert_regions_to_global(regions, offset_x, offset_y):
        """Convert ROI-relative bounding boxes to screen coordinates."""

        global_regions = []

        for region in regions:
            x1, y1, x2, y2 = region["bbox"]

            global_regions.append({
                "bbox": [
                    x1 + offset_x,
                    y1 + offset_y,
                    x2 + offset_x,
                    y2 + offset_y
                ],
                "area": region["area"]
            })

        return global_regions

    @staticmethod
    def _result(status, reason):
        return {
            "type": "verification",
            "status": status,
            "reason": reason,
        }

    # =========================================================
    # Action Verifiers
    # =========================================================

    def verify_left_single_click(self, state):

        action = state.get("last_action", {})
        x, y = action["x"], action["y"]

        old_img, new_img, error = self._decode_screenshots(
            state,
            resize_mismatch=False
        )

        if error:
            return self._result("uncertain", error)

        old_elements = state.get("old_elements", [])

        h, w = old_img.shape

        # Find the clicked element
        clicked_bbox = self._get_click_bbox(x, y, old_elements)

        # Use a default ROI if no element is found
        if clicked_bbox is None:
            radius = 50
            x1, y1 = x - radius, y - radius
            x2, y2 = x + radius, y + radius
        else:
            x1, y1, x2, y2 = clicked_bbox

        # Add padding and clip to image boundaries
        padding = 10

        x1 = max(0, int(x1) - padding)
        y1 = max(0, int(y1) - padding)
        x2 = min(w, int(x2) + padding)
        y2 = min(h, int(y2) + padding)

        if x1 >= x2 or y1 >= y2:
            return self._result("uncertain", "Invalid ROI")

        # Calculate local and global differences
        local_result = self._get_image_diff(
            old_img[y1:y2, x1:x2],
            new_img[y1:y2, x1:x2]
        )

        global_result = self._get_image_diff(old_img, new_img)

        local_ratio = local_result["changed_ratio"]
        global_ratio = global_result["changed_ratio"]

        if local_ratio > 0.02 or global_ratio > 0.01:
            return self._result(
                "success",
                (
                    f"Visual changes detected. "
                    f"Local changed ratio: {local_ratio:.4f}, "
                    f"Local mean difference: {local_result['mean_diff']:.2f}, "
                    f"Global changed ratio: {global_ratio:.4f}, "
                    f"Global mean difference: {global_result['mean_diff']:.2f}"
                )
            )

        return self._result(
            "uncertain",
            (
                f"No significant visual changes detected. "
                f"Local changed ratio: {local_ratio:.4f}, "
                f"Global changed ratio: {global_ratio:.4f}"
            )
        )

    def verify_right_single_click(self, state):

        action = state.get("last_action", {})
        x, y = action["x"], action["y"]

        old_img, new_img, error = self._decode_screenshots(state)

        if error:
            return self._result("uncertain", error)

        old_elements = state.get("old_elements", [])

        h, w = old_img.shape

        # Find the clicked element
        clicked_bbox = self._get_click_bbox(x, y, old_elements)

        # Define local ROI
        if clicked_bbox is not None:
            x1, y1, x2, y2 = clicked_bbox
        else:
            radius = 50
            x1, y1 = x - radius, y - radius
            x2, y2 = x + radius, y + radius

        padding = 10

        x1 = max(0, int(x1) - padding)
        y1 = max(0, int(y1) - padding)
        x2 = min(w, int(x2) + padding)
        y2 = min(h, int(y2) + padding)

        if x1 >= x2 or y1 >= y2:
            return self._result("uncertain", "Invalid ROI")

        # Calculate local and global differences
        local_result = self._get_image_diff(
            old_img[y1:y2, x1:x2],
            new_img[y1:y2, x1:x2]
        )

        global_result = self._get_image_diff(old_img, new_img)

        local_ratio = local_result["changed_ratio"]
        global_ratio = global_result["changed_ratio"]

        local_regions = self._convert_regions_to_global(
            local_result["changed_regions"],
            x1,
            y1
        )

        if local_ratio > 0.02 or global_ratio > 0.01:
            status = "success"
            reason = "Visual changes detected after right-click"
        else:
            status = "uncertain"
            reason = "No significant visual changes detected after right-click"

        return self._result(
            status,
            {
                "reason": reason,
                "local_changed_ratio": local_ratio,
                "local_mean_diff": local_result["mean_diff"],
                "global_changed_ratio": global_ratio,
                "global_mean_diff": global_result["mean_diff"],
                "local_changed_regions": local_regions,
                "global_changed_regions": global_result["changed_regions"],
                "used_element_bbox": clicked_bbox is not None
            }
        )

    def verify_left_double_click(self, state):

        old_img, new_img, error = self._decode_screenshots(state)

        if error:
            return self._result("uncertain", error)

        # Compare the entire screen
        global_result = self._get_image_diff(old_img, new_img)

        global_ratio = global_result["changed_ratio"]

        if global_ratio > 0.01:
            status = "success"
            reason = "Significant visual changes detected after double-click"
        else:
            status = "uncertain"
            reason = "No significant visual changes detected after double-click"

        return self._result(
            status,
            {
                "reason": reason,
                "global_changed_ratio": global_ratio,
                "global_mean_diff": global_result["mean_diff"],
                "global_changed_regions": global_result["changed_regions"]
            }
        )

    def verify_left_click_drag(self, state):

        action = state.get("last_action", {})

        required_coords = [
            "start_x", "start_y", "end_x", "end_y"
        ]

        if not isinstance(action, dict):
            return self._result("uncertain", "Invalid action")

        if not all(k in action for k in required_coords):
            return self._result("uncertain", "Missing drag coordinates")

        old_img, new_img, error = self._decode_screenshots(state)

        if error:
            return self._result("uncertain", error)

        start_x = action["start_x"]
        start_y = action["start_y"]
        end_x = action["end_x"]
        end_y = action["end_y"]

        # Extract start and end ROIs
        radius = 50

        old_start, _ = self._get_roi(
            old_img, start_x, start_y, radius
        )
        new_start, _ = self._get_roi(
            new_img, start_x, start_y, radius
        )

        old_end, _ = self._get_roi(
            old_img, end_x, end_y, radius
        )
        new_end, _ = self._get_roi(
            new_img, end_x, end_y, radius
        )

        if old_start.size == 0 or old_end.size == 0:
            return self._result("uncertain", "Invalid drag coordinates")

        # Calculate local and global differences
        start_result = self._get_image_diff(old_start, new_start)
        end_result = self._get_image_diff(old_end, new_end)
        global_result = self._get_image_diff(old_img, new_img)

        start_ratio = start_result["changed_ratio"]
        end_ratio = end_result["changed_ratio"]
        global_ratio = global_result["changed_ratio"]

        if start_ratio > 0.02 and end_ratio > 0.02:
            status = "success"
            reason = "Visual changes detected around both drag positions"
        elif global_ratio > 0.01:
            status = "uncertain"
            reason = "Global visual changes detected, but drag effect is unclear"
        else:
            status = "uncertain"
            reason = "No significant visual changes detected after dragging"

        return self._result(
            status,
            {
                "reason": reason,
                "start_changed_ratio": start_ratio,
                "end_changed_ratio": end_ratio,
                "global_changed_ratio": global_ratio,
                "start_changed_regions": start_result["changed_regions"],
                "end_changed_regions": end_result["changed_regions"],
                "global_changed_regions": global_result["changed_regions"]
            }
        )

    def verify_type_text(self, state):

        action = state.get("last_action", {})
        x, y = action["x"], action["y"]

        old_img, new_img, error = self._decode_screenshots(state)

        if error:
            return self._result("uncertain", error)

        # Extract local ROI around the input position
        old_roi, (x1, y1, _, _) = self._get_roi(
            old_img, x, y, radius_x=150, radius_y=50
        )

        new_roi, _ = self._get_roi(
            new_img, x, y, radius_x=150, radius_y=50
        )

        if old_roi.size == 0:
            return self._result("uncertain", "Invalid input coordinates")

        # Calculate local and global differences
        local_result = self._get_image_diff(old_roi, new_roi)
        global_result = self._get_image_diff(old_img, new_img)

        local_ratio = local_result["changed_ratio"]
        global_ratio = global_result["changed_ratio"]

        if local_ratio > 0.02:
            status = "success"
            reason = "Visual changes detected around the input field"
        else:
            status = "uncertain"
            reason = "No significant visual changes detected around the input field"

        return self._result(
            status,
            {
                "reason": reason,
                "local_changed_ratio": local_ratio,
                "local_mean_diff": local_result["mean_diff"],
                "global_changed_ratio": global_ratio,
                "global_mean_diff": global_result["mean_diff"],
                "local_changed_regions": self._convert_regions_to_global(
                    local_result["changed_regions"],
                    x1,
                    y1
                ),
                "global_changed_regions": global_result["changed_regions"]
            }
        )

    def verify_scroll(self, state):

        action = state.get("last_action", {})
        x, y = action["x"], action["y"]

        old_img, new_img, error = self._decode_screenshots(state)

        if error:
            return self._result("uncertain", error)

        # Extract scrolling region
        old_roi, (x1, y1, _, _) = self._get_roi(
            old_img, x, y, radius_x=300, radius_y=200
        )

        new_roi, _ = self._get_roi(
            new_img, x, y, radius_x=300, radius_y=200
        )

        if old_roi.size == 0:
            return self._result("uncertain", "Invalid scroll coordinates")

        # Calculate local and global differences
        local_result = self._get_image_diff(old_roi, new_roi)
        global_result = self._get_image_diff(old_img, new_img)

        local_ratio = local_result["changed_ratio"]
        global_ratio = global_result["changed_ratio"]

        if local_ratio > 0.02:
            status = "success"
            reason = "Visual changes detected in the scrolling region"
        else:
            status = "uncertain"
            reason = "No significant visual changes detected in the scrolling region"

        return self._result(
            status,
            {
                "reason": reason,
                "local_changed_ratio": local_ratio,
                "local_mean_diff": local_result["mean_diff"],
                "global_changed_ratio": global_ratio,
                "global_mean_diff": global_result["mean_diff"],
                "local_changed_regions": self._convert_regions_to_global(
                    local_result["changed_regions"],
                    x1,
                    y1
                ),
                "global_changed_regions": global_result["changed_regions"]
            }
        )
