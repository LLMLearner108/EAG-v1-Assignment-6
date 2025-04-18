import os
import logging
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio
from openai import OpenAI
from concurrent.futures import TimeoutError
from utils import *
from rich.console import Console
from rich.panel import Panel
from rich.logging import RichHandler
from sub_prompts import *
from uuid import uuid4
from memory import *
from perception import *
from decision import *

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize rich console
console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger("mcp_client")

max_iterations = 10
last_response = None
iteration = 0
iteration_response = []


async def main(user_preferences):
    print("Starting main execution...")
    mem = Memory()
    session_id = str(uuid4())
    mem.session[session_id] = []

    # Ask the user preferences before beginning of the agentic workflow
    mem.preferences = user_preferences

    # User query
    query = """
TASK:
--------------------------------
You are given a cylindrical rod of length 10 cm and diameter 5 cm. You need to turn the rod to a diameter of 3 cm without altering the length of the rod. You need to come up with a program to do this. Remember turning is done in the XZ plane.

Once you have the code to perform this operation, visualize the answer in a paint tool.
"""

    try:
        # Create a single MCP server connection
        print("Establishing connection to MCP server...")
        server_params = StdioServerParameters(
            command="python", args=["mcp_action_server.py"]
        )

        async with stdio_client(server_params) as (read, write):
            print("Connection established, creating session...")
            async with ClientSession(read, write) as session:
                print("Session created, initializing...")
                await session.initialize()

                # Get available tools
                print("Requesting tool list...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                tools_description = get_description_from_tools(tools)

                # Create perception output
                perception_prompt = build_perception_prompt(tools_description, query)
                perception_response_text = await generate_with_timeout(
                    client, perception_prompt
                )

                # Validate the perceived output
                PerceptionObject.model_validate_json(perception_response_text)

                import code

                code.interact(local=locals())

                mem["session"][session_id].append(
                    f"I have percieved this information from the given query {perception_response_text}"
                )

                import code

                code.interact(local=locals())

                while iteration < max_iterations:

                    # Introduce a sleep to be generous to the cloud provider
                    # For free tier, we have a max of 15 requests per minute
                    await asyncio.sleep(3)

                    # Do a perception iteration

                    print(f"\n--- Iteration {iteration + 1} ---")
                    if last_response is None:
                        current_query = query
                    else:
                        current_query = (
                            current_query + "\n\n" + " ".join(iteration_response)
                        )
                        current_query = current_query + "  What should I do next?"

                    # Get model's response with timeout
                    print("Preparing to generate LLM response...")
                    prompt = f"{system_prompt}\n\nQuery: {current_query}"
                    print(prompt)

                    try:
                        response_text = await generate_with_timeout(client, prompt)
                        console.print(
                            Panel(
                                response_text,
                                title=f"Iteration {iteration + 1}",
                                border_style="blue",
                                title_align="left",
                            )
                        )

                        # Parse the response into a FunctionCall object
                        try:
                            function_call = FunctionCall.model_validate_json(
                                response_text
                            )
                            logger.debug(f"Parsed function call: {function_call}")
                        except Exception as e:
                            logger.error(
                                f"Failed to parse LLM response as FunctionCall: {e}"
                            )
                            break

                        # Handle the function call based on its type
                        if function_call.tool_name == FunctionName.FINAL_ANSWER:
                            console.print(
                                Panel(
                                    "Agent Execution Complete",
                                    title="Final Answer",
                                    border_style="green",
                                    title_align="left",
                                )
                            )
                            break

                        # Find the matching tool to get its input schema
                        tool = next(
                            (
                                t
                                for t in tools
                                if t.name == function_call.tool_name.value
                            ),
                            None,
                        )
                        if not tool:
                            logger.error(f"Available tools: {[t.name for t in tools]}")
                            raise ValueError(
                                f"Unknown tool: {function_call.tool_name.value}"
                            )

                        logger.debug(f"Found tool: {tool.name}")
                        logger.debug(f"Tool schema: {tool.inputSchema}")

                        result = await session.call_tool(
                            function_call.tool_name.value,
                            arguments=function_call.arg,
                        )

                        logger.debug(f"Raw result: {result}")

                        # Get the full result content
                        if hasattr(result, "content"):
                            logger.debug("Result has content attribute")
                            # Handle multiple content items
                            if isinstance(result.content, list):
                                iteration_result = [
                                    (item.text if hasattr(item, "text") else str(item))
                                    for item in result.content
                                ]
                            else:
                                iteration_result = str(result.content)
                        else:
                            logger.debug("Result has no content attribute")
                            iteration_result = str(result)

                        logger.debug(f"Final iteration result: {iteration_result}")

                        # Format the response based on result type
                        if isinstance(iteration_result, list):
                            result_str = f"[{', '.join(iteration_result)}]"
                        else:
                            result_str = str(iteration_result)

                        iteration_response.append(
                            f"In iteration {iteration + 1} you called {function_call.tool_name.value} with {function_call.arguments} parameters, "
                            f"and the function returned {result_str}.\n"
                        )
                        last_response = iteration_result

                    except Exception as e:
                        logger.error(f"Error details: {str(e)}")
                        logger.error(f"Error type: {type(e)}")
                        import traceback

                        traceback.print_exc()
                        iteration_response.append(
                            f"Error in iteration {iteration + 1}: {str(e)}"
                        )
                        break

                    iteration += 1

    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback

        traceback.print_exc()
    finally:
        pass


if __name__ == "__main__":
    preferences = input("Enter your user preferences please.\n\n")
    asyncio.run(main(preferences))
