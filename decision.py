from memory import Memory
from sub_prompts import *
from utils import get_description_from_tools, generate_with_timeout, FunctionCall
from openai import OpenAI
from logging import Logger
from typing import List
from mcp import Tool

class Decision:
    """
    The Decision class is responsible for making decisions about which tools to execute
    based on the current state and memory. It forms the third step in the
    Perception -> Memory -> Decision -> Action framework.

    The Decision class:
    1. Constructs prompts for the LLM based on available tools and memory
    2. Makes decisions about which tool to execute next
    3. Validates the decisions before they are executed
    4. Ensures decisions align with the overall task goals

    Attributes:
        memory (Memory): Reference to the Memory instance for accessing history
        client (OpenAI): OpenAI client for making LLM calls
        logger (Logger): Logger instance for logging decision details
    """

    def __init__(
        self,
        memory: Memory,
        client: OpenAI,
        logger: Logger,
    ):
        """
        Initialize the Decision class with necessary dependencies.

        Args:
            memory (Memory): Reference to the Memory instance
            client (OpenAI): OpenAI client for LLM calls
            logger (Logger): Logger instance for logging
        """
        self.memory = memory
        self.client = client
        self.logger = logger

    def _get_base_prompt(self, tools) -> str:
        """
        Construct the base prompt for decision making.

        This method:
        1. Gets tool descriptions
        2. Combines general instructions, tool descriptions, and special instructions
        3. Creates a comprehensive prompt for the LLM

        Args:
            tools (list): List of available tools

        Returns:
            str: The complete base prompt for decision making
        """
        tools_description = get_description_from_tools(tools)
        system_prompt = f"""
{general_instructions}

Here is a list of all the tools available at your disposal:
{tools_description}

{special_instructions}

{fallback_handling}

{decision_response_instruction}
"""
        return system_prompt

    async def decide(self, session_id: str, query: str, tools: List[Tool]) -> FunctionCall:
        """
        Make a decision about which tool to execute next.

        This method:
        1. Constructs the complete prompt including history and current query
        2. Gets the LLM's response
        3. Validates the response as a FunctionCall
        4. Returns the validated decision

        Args:
            session_id (str): Unique identifier for the current session
            query (str): The current task query
            tools (list): List of available tools

        Returns:
            FunctionCall: The validated decision about which tool to execute
        """
        # Construct the base prompt
        what_i_need_to_ask = self._get_base_prompt(tools)

        # Add the task that is asked for by the user
        what_i_need_to_ask += f"\nUser Query:\n{query}"

        # Add the things which I have already done in the past based on the memory
        history = self.memory.recall(session_id, include_preferences=True)
        what_i_need_to_ask += f"\n{history}\n"

        what_i_need_to_ask += "What should I do next?"

        import code

        code.interact(local=locals())

        try:
            response_text = await generate_with_timeout(
                self.client, what_i_need_to_ask, 60
            )
            self.logger.info(f"Decision Step Response: {response_text}")

            # Validate the model output
            function_call = FunctionCall.model_validate_json(response_text)
            self.logger.info(f"Validated the Decision Step response")
        except Exception as e:
            function_call = f"Error in parsing {response_text}\nCould not validate the function call output because {str(e)}"
            self.logger.error(f"Decision step response could not be validated")

        return function_call
