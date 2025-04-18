from pydantic import BaseModel, Field
from sub_prompts import *
from utils import perception_response_dict


class PerceptionObject(BaseModel):
    task: str = Field(..., description="User's complete task in short")
    start_state: str = Field(
        ...,
        description="If the user provides a task, what is the start state of the object on which the machining needs to be done",
    )
    material_info: str | None = Field(
        ...,
        description="If the user has asked to perform an operation on a certain thing, what is the material that the thing is made of, what are it's properties etc. Do not guess the material. Just say null if the material is not specified",
    )
    dimension_info: dict = Field(
        ..., description="Extract all the dimensions mentioned in the task."
    )
    operations: str = Field(
        ...,
        description="If there are any machine operations mentioned by the user in the task, then extract those operations.",
    )
    end_state: str = Field(
        ...,
        description="If the user provides a task, what is the end state of the object on which the machining needs to be done after performing all the operations",
    )


def build_perception_prompt(tools_description, user_query) -> str:
    perception_prompt = f"""
    {general_instructions}

    Here is a list of all the tools available at your disposal:
    {tools_description}

    {special_instructions}

    {fallback_handling}

    {perception_response_instruction}

    {user_query}
    """

    return perception_prompt
