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

# Load environment variables from .env file
load_dotenv("../.env")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize rich console
console = Console()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)
logger = logging.getLogger("mcp_client")

max_iterations = 10
last_response = None
iteration = 0
iteration_response = []


async def generate_with_timeout(prompt, timeout=10):
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
                            "content": "You are an expert CNC agent who has a PhD. in the engineering discipline of Manufacturing Sciences. You are a very hands on agent and have practical knowledge about the working of a CNC (Compute Numeric Controlled (Lathe)).",
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
            command="python", args=["mcp_cnc_server.py"]
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

GENERAL INSTRUCTIONS:
--------------------------------
You are a CNC machining agent expert at solving problems in iterations. 
You can reason, you are capable of planning and thinking step by step. 
For any given problem, you first identify the problem, break it down into smaller steps, come up with a plan and then execute the plan only ONE STEP AT A TIME.
You can reason in multiple ways. Since you are good at CNC operations, you can use different modes of reasoning like spatial (Understading geometry, understanding the spatial relationships between the parts), algorithmic (sequence of operations, mixing and matching operations to perform complex tasks etc.), optimization (which code is more efficient, would lead to less wastage and give best results both from the life of tool, quality of the part, convenience of the operator etc.), safety (safety of the operator, safety of the machine, safety of the part etc.), other (Any miscellaneous thought or reasoning that you may think and feel is relevant). It will help you to first identify the kind of reasoning you would like to use (one or multiple) before coming up with the plan. 
You have access to various tools to perform different operations on the CNC machine. 
Additionally, you also have access to a paint tool. Use it like a notepad. Gather all the commands obtained from the iterations and stitch them together to form a comprehensive program that can be run on the CNC machine. This is what the paint tool needs to show to the user i.e. the final program. Do not forget to add comments to the program to make it understandable to the user.

Here is a list of all the tools available at your disposal:
{tools_description}

SPECIAL INSTRUCTIONS:
--------------------------------
- Be conservative while calling the tools. 
    - Only call a tool if you are sure that it will help you solve the problem. 
    - Do not call the same tool with the same parameters multiple times unless necessary.
- Only give FINAL_ANSWER when you have completed all necessary calculations
- If you are asked to display the answer in a paint tool, you must first use the paint tool and do that before giving out the final answer.
- For any given problem, ALWAYS THINK ALL THE STEPS THROUGH in the first pass and display the reasoning to the user.
- After each arithmetic operation that you perform, you MUST VERIFY if the last performed step is correct or not. This function can be called multiple times. Just don't call it in succession. Call if after every arithmetic operation. IFF the verification is dubious or can be interpreted in different ways, you are allowed to call it in succession.

FALLBACK HANDLING:
--------------------------------
- If a tool fails to return a valid response, analyze the failure using internal reasoning and retry with modified parameters or skip to an alternative step as you deem necessary.
- If you are uncertain about a step, clearly state the uncertainty and explain why. Use `verify_step()` tool.
- If unable to generate a full solution, output a partial result and clearly state what’s missing and why. Use `final_answer` with a status message; mention the reason why failure has happened very explicitly and is it the lack of tools, lack of your ability to comprehend the task or lack of clarity in terms of the user's instruction that is the primary cause why the request cannot be fulfilled completely.

You must respond with a json object which abides to the following schema:
```json
{json.dumps(response_dict, indent=2)}
```

Please note that the argument dict in the above schema MUST contain the necessary arguments of the tool call which is provided in the list of tools available at your disposal above.
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

                    import code

                    code.interact(local=dict(globals(), **locals()))

                    try:
                        response_text = await generate_with_timeout(prompt)
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
                        result = await session.call_tool(
                            function_call.tool_name.value,
                            arguments=function_call.arguments,
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
