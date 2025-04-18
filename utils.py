from pydantic import BaseModel, Field
from enum import Enum
import json, asyncio

system_prompt = """
You are an expert CNC agent who has a PhD. in the engineering discipline of Manufacturing Sciences. You are a very hands on agent and have practical knowledge about the working of a CNC (Compute Numeric Controlled (Lathe)).
"""

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


decision_response_dict = {
    "what_was_done_in_previous_step": "<str> A brief description of what action was taken in the previous step",
    "what_needs_to_be_done_next": "<str> Looking at the plan of action, what is the next action that I need to take so that the user's task can be accomplished",
    "tool_name": f"<str>: Can be one of these function names: {', '.join([x.value for x in FunctionName])}",
    "arguments": f"<dict>: Suitable arguments based on the tool name as provided in the list of tools available to you",
}

perception_response_dict = {
    "task": "<str> A brief description of what user wants to do",
    "start_state": "<str> If the user provides a task, what is the start state of the object on which the machining needs to be done",
    "material_info": "<str>|None: If the user has asked to perform an operation on a certain thing, what is the material that the thing is made of, what are it's properties etc. Do not guess the material. Just say null if the material is not specified",
    "dimension_info": "<dict>: All the dimensions mentioned in the task",
    "operations": "<str> If there are any machine operations mentioned by the user in the task, then extract those operations",
    "end_state": "<str> If the user provides a task, what is the end state of the object on which the machining needs to be done after performing all the operations",
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


async def generate_with_timeout(client, prompt, timeout=60):
    """Generate content with a timeout"""
    print("Starting LLM generation...")
    try:
        # Convert the synchronous chat.completions.create call to run in a thread
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt,
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,
                    max_tokens=1000,
                    response_format={"type": "json_object"},
                ),
            ),
            timeout=timeout,
        )
        print("LLM generation completed")
        return response.choices[0].message.content
    except TimeoutError:
        print("LLM generation timed out!")
        raise
    except Exception as e:
        print(f"Error in LLM generation: {e}")
        raise


def get_description_from_tools(tools):
    try:
        tools_description = []
        for i, tool in enumerate(tools):
            try:
                tool_desc = f"{i+1}. {tool.name}\n{tool.description}"
                tools_description.append(tool_desc)
            except Exception as e:
                print(f"Error processing tool {i}: {e}")
                tools_description.append(f"{i+1}. Error processing tool")

        tools_description = "\n".join(tools_description)
        print("Successfully created tools description")
    except Exception as e:
        print(f"Error creating tools description: {e}")
        tools_description = "Error loading tools"

    return tools_description


if __name__ == "__main__":
    import code

    code.interact(local=dict(globals(), **locals()))
    print(json.dumps(FunctionCall.model_json_schema(), indent=2))
