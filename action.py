from utils import FunctionCall, FunctionName
from mcp import ClientSession


class Action:
    """
    The Action class is responsible for executing tool calls and managing their results.
    It forms the final step in the Perception -> Memory -> Decision -> Action framework.

    The Action class:
    1. Executes tool calls based on decisions made by the Decision class
    2. Handles tool execution results and formats them appropriately
    3. Stores execution results in memory for future reference
    4. Manages the continuation state of the agent's execution

    Attributes:
        tools (list): List of available tools that can be executed
        memory (Memory): Reference to the Memory instance for storing execution history
        logger (Logger): Logger instance for logging execution details
    """

    def __init__(self, tools, memory, logger):
        """
        Initialize the Action class with necessary dependencies.

        Args:
            tools (list): List of available tools that can be executed
            memory (Memory): Reference to the Memory instance
            logger (Logger): Logger instance for logging
        """
        self.tools = tools
        self.memory = memory
        self.logger = logger

    async def execute_action(
        self,
        function_call: FunctionCall,
        session: ClientSession,
        session_id: str,
        iteration: int,
    ) -> bool:
        """
        Execute a tool call based on the function_call decision.

        This method:
        1. Validates the tool call
        2. Executes the tool with provided arguments
        3. Processes and formats the result
        4. Stores the execution details in memory
        5. Determines if execution should continue

        Args:
            function_call (FunctionCall): The decision to execute a specific tool
            session: The MCP session for executing tools
            session_id (str): Unique identifier for the current session
            iteration (int): Current iteration number

        Returns:
            bool: True if execution should continue, False if it should stop
        """
        # Handle the function call based on its type
        if function_call.tool_name == FunctionName.FINAL_ANSWER:
            self.logger.info("Agent execution completed!")
            return False

        tool = next(
            (t for t in self.tools if t.name == function_call.tool_name.value),
            None,
        )

        if not tool:
            self.logger.error(f"Available tools: {[t.name for t in self.tools]}")
            raise ValueError(f"Unknown tool: {function_call.tool_name.value}")

        self.logger.debug(f"Found tool: {tool.name}")
        self.logger.debug(f"Tool schema: {tool.inputSchema}")

        result = await session.call_tool(
            function_call.tool_name.value,
            arguments=function_call.arguments,
        )

        self.logger.debug(f"Raw result: {result}")

        # Get the full result content
        if hasattr(result, "content"):
            self.logger.debug("Result has content attribute")
            # Handle multiple content items
            if isinstance(result.content, list):
                iteration_result = [
                    (item.text if hasattr(item, "text") else str(item))
                    for item in result.content
                ]
            else:
                iteration_result = str(result.content)
        else:
            self.logger.debug("Result has no content attribute")
            iteration_result = str(result)

        self.logger.debug(f"Final iteration result: {iteration_result}")

        # Format the response based on result type
        if isinstance(iteration_result, list):
            result_str = f"[{', '.join(iteration_result)}]"
        else:
            result_str = str(iteration_result)

        # Add the tool call, execution result and the return value of the function to the memory
        self.memory.session[session_id].append(
            f"In iteration {iteration} you called {function_call.tool_name.value} with {function_call.arguments} parameters, "
            f"and the function returned {result_str}.\n"
        )

        return True
