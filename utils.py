from pydantic import BaseModel, Field
from enum import Enum
import json

# # Old problem's function names
# class FunctionName(Enum):
#     ADD = "add"
#     LISTIFY = "listify_number"
#     CAN_LISTIFY = "can_I_listify_a_number"
#     SUMMIFY = "summify_list"
#     CHECK_EQUALITY = "check_integer_equality"
#     ADD_TEXT_IN_PAINT = "add_text_in_paint"
#     REASONING = "show_reasoning"
#     FINAL_ANSWER = "final_answer"


# New problem's function names
class FunctionName(Enum):
    SET_MACHINE = "set_units_and_mode"
    SELECT_TOOL_AND_START_SPINDLE = "select_tool_and_start_spindle"
    MOVE_TO_SAFE_START = "move_to_safe_start"
    FACE_STOCK = "face_stock"
    PERFORM_UNIFORM_TURNING = "do_turning"
    RETRACT_AND_END_PROGRAM = "retract_and_end_program"
    ADD_TEXT_IN_PAINT = "add_text_in_paint"
    REASONING = "show_reasoning"
    FINAL_ANSWER = "final_answer"


class FunctionCall(BaseModel):
    what_was_done_in_previous_step: str = Field(
        ..., description="A brief of what action was performed in the previous step"
    )
    what_needs_to_be_done_next: str = Field(
        ...,
        description="What is the next step that needs to be done as per the plan of action to complete the user's task",
    )
    tool_name: FunctionName
    arguments: dict | None


response_dict = {
    "what_was_done_in_previous_step": "<str> A brief description of what action was taken in the previous step",
    "what_needs_to_be_done_next": "<str> Looking at the plan of action, what is the next action that I need to take so that the user's task can be accomplished",
    "tool_name": f"<str>: Can be one of these function names: {', '.join([x.value for x in FunctionName])}",
    "arguments": f"<dict>: Suitable arguments based on the tool name as provided in the list of tools available to you",
}


class ReasoningType(Enum):
    SPATIAL = "spatial"
    ALGORITHMIC = "algorithmic"
    OPTIMIZATION = "optimization"
    SAFETY = "safety"
    OTHER = "other"


class ReasoningStep(BaseModel):
    step_text: str
    type_of_reasoning: list[ReasoningType]
    reasoning_issues: str | None
    are_there_any_issues_in_reasoning: bool


def get_reasoning_tool_description(tool_number: int):
    return f"""{tool_number}. show_reasoning(reasoning: list[ReasoningStep]) -
    This tool is used to come up with the reasoning for solving a particular problem.

    Args:
        list[ReasoningStep]: A list of ReasoningStep objects

        Each ReasoningStep object has the following attributes:
            - step_text: A string that contains the reasoning for solving a particular problem
            -   type_of_reasoning: A list of strings that contain the type of reasoning for solving a particular problem. This can only be one of the following: spatial, algorithmic, optimization, safety, other
            - reasoning_issues: A string that contains the issues in the reasoning for solving a particular problem
            - are_there_any_issues_in_reasoning: A boolean that contains whether there are any issues in the reasoning for solving a particular problem
    
    Returns:
        dict: A message showing the reasoning for solving a particular problem
    """


if __name__ == "__main__":
    import code

    code.interact(local=dict(globals(), **locals()))
    print(json.dumps(FunctionCall.model_json_schema(), indent=2))
