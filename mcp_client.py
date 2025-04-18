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


def reset_state():
    """Reset all global variables to their initial state"""
    global last_response, iteration, iteration_response
    last_response = None
    iteration = 0
    iteration_response = []


async def main():
    reset_state()  # Reset at the start of main
    print("Starting main execution...")
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
                print(f"Successfully retrieved {len(tools)} tools")

                # Create system prompt with available tools
                print("Creating system prompt...")
                print(f"Number of tools: {len(tools)}")

                try:
                    tools_description = []
                    for i, tool in enumerate(tools):
                        try:
                            # Get tool properties
                            params = tool.inputSchema

                            desc = getattr(
                                tool, "description", "No description available"
                            )
                            name = getattr(tool, "name", f"tool_{i}")

                            if name == "show_reasoning":
                                # import code

                                # code.interact(local=locals())

                                tool_desc = get_reasoning_tool_description(
                                    tool_number=i + 1
                                )
                                tools_description.append(tool_desc)
                                print(f"Added description for tool: {tool_desc}")
                                continue

                            # Format the input schema in a more readable way
                            if "properties" in params:
                                param_details = []
                                for param_name, param_info in params[
                                    "properties"
                                ].items():
                                    param_type = param_info.get("type", "unknown")
                                    param_details.append(f"{param_name}: {param_type}")
                                params_str = ", ".join(param_details)
                            else:
                                params_str = "no parameters"

                            tool_desc = f"{i+1}. {name}({params_str}) - {desc}"
                            tools_description.append(tool_desc)
                            print(f"Added description for tool: {tool_desc}")
                        except Exception as e:
                            print(f"Error processing tool {i}: {e}")
                            tools_description.append(f"{i+1}. Error processing tool")

                    tools_description = "\n".join(tools_description)
                    print("Successfully created tools description")
                except Exception as e:
                    print(f"Error creating tools description: {e}")
                    tools_description = "Error loading tools"

                print("Created system prompt...")

                system_prompt = f"""
{general_instructions}

Here is a list of all the tools available at your disposal:
{tools_description}

{special_instructions}

{fallback_handling}

{response_instruction}

"""

                query = """
TASK:
--------------------------------
You are given a cylindrical rod of length 10 cm and diameter 5 cm. You need to turn the rod to a diameter of 3 cm without altering the length of the rod. You need to come up with a program to do this. Remember turning is done in the XZ plane.

Once you have the code to perform this operation, visualize the answer in a paint tool.
                """
                print("Starting iteration loop...")

                # Use global iteration variables
                global iteration, last_response

                while iteration < max_iterations:

                    import code

                    code.interact(local=locals())

                    # Introduce a sleep to be generous to the cloud provider
                    # For free tier, we have a max of 15 requests per minute
                    await asyncio.sleep(3)
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

                        # Call the tool with the provided arguments
                        # Wrap arguments in the appropriate input schema
                        if function_call.tool_name.value == "show_reasoning":
                            arguments = {
                                "input": {
                                    "reasoning": function_call.arguments["reasoning"]
                                }
                            }
                        else:
                            arguments = function_call.arguments

                        result = await session.call_tool(
                            function_call.tool_name.value,
                            arguments=arguments,
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
        reset_state()  # Reset at the end of main


if __name__ == "__main__":
    asyncio.run(main())
