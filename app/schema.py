from pydantic import BaseModel, Field, model_validator, field_validator, ConfigDict
from typing import Annotated, Optional, List, Literal, Union
from enum import Enum


# ---------------------------------------------------------
# 1. Action type enum (covers all Dispatcher operations)
# ---------------------------------------------------------
class ActionType(str, Enum):
    # SCREENSHOT = "screenshot"
    # CURSOR_POSITION = "cursor_position"
    # MOUSE_MOVE = "mouse_move"

    LEFT_SINGLE_CLICK = "left_single_click"
    RIGHT_SINGLE_CLICK = "right_single_click"
    # MIDDLE_CLICK = "middle_click"
    LEFT_DOUBLE_CLICK = "left_double_click"

    LEFT_CLICK_DRAG = "left_click_drag"

    # LEFT_MOUSE_DOWN = "left_mouse_down"
    # LEFT_MOUSE_UP = "left_mouse_up"
    # RIGHT_MOUSE_DOWN = "right_mouse_down"
    # RIGHT_MOUSE_UP = "right_mouse_up"
    # MIDDLE_MOUSE_DOWN = "middle_mouse_down"
    # MIDDLE_MOUSE_UP = "middle_mouse_up"

    # KEY_PRESS = "key_press"
    # KEY_DOWN = "key_down"
    # KEY_UP = "key_up"

    TYPE_TEXT = "type_text"
    SCROLL = "scroll"
    FINISH = "finish"


# ---------------------------------------------------------
# 2. Base action: shared fields, strict config, coord guard
# ---------------------------------------------------------
class BaseAction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @field_validator("x", "y", "start_x", "start_y", "end_x", "end_y", check_fields=False)
    @classmethod
    def coords_must_not_be_bool(cls, v):
        if isinstance(v, bool):
            raise ValueError("Coordinates must be integers, not booleans.")
        return v


# ---------------------------------------------------------
# 3. Action models
# ---------------------------------------------------------
# # 未加入最终可选择动作列表
# class ScreenshotAction(BaseAction):
#     type: Literal[ActionType.SCREENSHOT] = ActionType.SCREENSHOT

# # 未加入最终可选择动作列表
# class CursorPositionAction(BaseAction):
#     type: Literal[ActionType.CURSOR_POSITION] = ActionType.CURSOR_POSITION

# # 未加入最终可选择动作列表
# class MouseMoveAction(BaseAction):
#     type: Literal[ActionType.MOUSE_MOVE] = ActionType.MOUSE_MOVE
#     x: int = Field(description="Target X coordinate of the cursor.")
#     y: int = Field(description="Target Y coordinate of the cursor.")


class LeftSingleClickAction(BaseAction):
    type: Literal[ActionType.LEFT_SINGLE_CLICK] = ActionType.LEFT_SINGLE_CLICK
    x: int = Field(description="X coordinate to click.")
    y: int = Field(description="Y coordinate to click.")
    modifiers: Optional[List[str]] = Field(
        default=None,
        description="Modifier keys held during the click, e.g. ['ctrl', 'shift'].",
    )

class RightSingleClickAction(BaseAction):
    type: Literal[ActionType.RIGHT_SINGLE_CLICK] = ActionType.RIGHT_SINGLE_CLICK
    x: int = Field(description="X coordinate to click.")
    y: int = Field(description="Y coordinate to click.")
    modifiers: Optional[List[str]] = Field(
        default=None,
        description="Modifier keys held during the click, e.g. ['ctrl', 'shift'].",
    )
    
class LeftDoubleClickAction(BaseAction):
    type: Literal[ActionType.LEFT_DOUBLE_CLICK] = ActionType.LEFT_DOUBLE_CLICK
    x: int = Field(description="X coordinate to double click.")
    y: int = Field(description="Y coordinate to double click.")
    modifiers: Optional[List[str]] = Field(
        default=None,
        description="Modifier keys held during the double click, e.g. ['ctrl', 'shift'].",
    )

# # 未加入最终可选择动作列表
# class MouseButtonAction(BaseAction):
#     type: Literal[
#         ActionType.LEFT_MOUSE_DOWN, ActionType.LEFT_MOUSE_UP,
#         ActionType.RIGHT_MOUSE_DOWN, ActionType.RIGHT_MOUSE_UP,
#         ActionType.MIDDLE_MOUSE_DOWN, ActionType.MIDDLE_MOUSE_UP,
#     ]

class LeftClickDragAction(BaseAction):
    type: Literal[ActionType.LEFT_CLICK_DRAG] = ActionType.LEFT_CLICK_DRAG
    start_x: int = Field(description="Drag start X coordinate.")
    start_y: int = Field(description="Drag start Y coordinate.")
    end_x: int = Field(description="Drag end X coordinate.")
    end_y: int = Field(description="Drag end Y coordinate.")
    modifiers: Optional[List[str]] = Field(
        default=None,
        description="Modifier keys held during the drag.",
    )

class TypeTextAction(BaseAction):
    type: Literal[ActionType.TYPE_TEXT] = ActionType.TYPE_TEXT
    x: int = Field(description="X coordinate of the input field to focus before typing.")
    y: int = Field(description="Y coordinate of the input field to focus before typing.")
    text: str = Field(description="Text to type. Supports unicode and newlines. Must not be empty.")

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, v):
        if v == "":
            raise ValueError("text must not be empty.")
        return v

# # 未加入最终可选择动作列表
# class KeyAction(BaseAction):
#     type: Literal[
#         ActionType.KEY_PRESS,
#         ActionType.KEY_DOWN,
#         ActionType.KEY_UP,
#     ]
#     key: Union[str, List[str]] = Field(
#         description="A single key or a list of keys for a combination, e.g. 'enter' or ['ctrl', 'c']."
#     )

#     @model_validator(mode="after")
#     def key_not_empty(self):
#         if not self.key:
#             raise ValueError(f"{self.type.value}: key must not be empty.")
#         if isinstance(self.key, list) and len(self.key) == 0:
#             raise ValueError("key list must not be empty.")
#         return self


class ScrollAction(BaseAction):
    type: Literal[ActionType.SCROLL] = ActionType.SCROLL
    direction: Literal["up", "down", "left", "right"] = Field(
        description="Scroll direction."
    )
    amount: Optional[int] = Field(default=1, description="Scroll amount in wheel steps.")
    x: int = Field(description="X coordinate of the scroll position.")
    y: int = Field(description="Y coordinate of the scroll position.")

class FinishAction(BaseAction):
    type: Literal[ActionType.FINISH] = ActionType.FINISH

# ---------------------------------------------------------
# 4. Discriminated union + top-level output schema
# ---------------------------------------------------------
Action = Annotated[
    Union[
        LeftSingleClickAction,
        RightSingleClickAction,
        LeftDoubleClickAction,
        LeftClickDragAction,
        TypeTextAction,
        ScrollAction,
        FinishAction,
    ],
    Field(discriminator="type"),
]

class AgentOutputSchema(BaseModel):
    thought: str = Field(
        description=(
            "Analyze the current situation and explain your decision:\n"
            "1. What the previous action attempted to do.\n"
            "2. What the verification result indicates.\n"
            "3. What the current screen shows.\n"
            "4. Whether the previous action achieved its expected result.\n"
            "5. Whether the user's final goal has been achieved.\n"
            "6. Why the next action is appropriate, if another action is needed.\n"
        ),
    )

    expected_result: str = Field(
        description=(
            "Describe the concrete and observable screen change expected "
            "after executing the selected action. This result will be used "
            "by the Verifier and Planner in the next iteration to evaluate "
            "whether the action achieved its intended effect. "
            "For the finish action, return an empty string."
        ),
    )

    action: Action = Field(
        description="The action the agent decides to perform next."
    )