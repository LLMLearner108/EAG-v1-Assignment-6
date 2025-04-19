from pydantic import BaseModel, Field
from sub_prompts import *
from utils import perception_response_dict


class PerceptionObject(BaseModel):
    """
    The PerceptionObject class represents the structured understanding of a task.
    It forms the first step in the Perception -> Memory -> Decision -> Action framework.

    This class:
    1. Captures the essential elements of a task
    2. Provides a structured format for task understanding
    3. Validates the perception using Pydantic models
    4. Serves as input for subsequent decision making

    Attributes:
        task (str): User's complete task in short
        start_state (str): Initial state of the object to be machined
        material_info (str | None): Material properties if specified
        dimension_info (dict): All dimensions mentioned in the task
        operations (str): Machine operations mentioned in the task
        end_state (str): Desired final state after operations
    """

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


def build_perception_prompt(tools_description: str, user_query: str) -> str:
    """
    Build a comprehensive prompt for the perception phase.

    This function:
    1. Combines general instructions with tool descriptions
    2. Adds special instructions and fallback handling
    3. Includes the perception response schema
    4. Appends the user's query

    Args:
        tools_description (str): Description of available tools
        user_query (str): The user's task query

    Returns:
        str: A complete prompt for the perception phase
    """
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
