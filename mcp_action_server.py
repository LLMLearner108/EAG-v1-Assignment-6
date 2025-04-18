# basic import
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base
from mcp.types import TextContent
import sys
from use_paint_preview_with_mac import *
from utils import ReasoningStep

# instantiate an MCP server client
mcp = FastMCP("Calculator")

# DEFINE TOOLS


@mcp.tool()
def set_units_and_mode() -> list[str]:
    """
    Sets the CNC machine to use metric units, absolute positioning,
    feed per revolution mode, and selects the XZ plane.

    Returns:
        list[str]: A list of strings that contain the G-code commands to set the units and mode
    """
    return [
        "G21",  # Units in mm
        "G90",  # Absolute positioning
        "G95",  # Feed per revolution
        "G18",  # XZ plane selection
    ]


@mcp.tool()
def select_tool_and_start_spindle(
    tool_number: int, offset: int, spindle_speed: int
) -> list[str]:
    """
    Selects the tool and starts the spindle at a given speed.

    Args:
        tool_number: Tool number (e.g., 1 for T0101)
        offset: Tool offset number
        spindle_speed: Spindle speed in RPM

    Returns:
        list[str]: A list of strings that contain the G-code commands to select the tool and start the spindle
    """
    return [
        f"T{tool_number:02d}{offset:02d}",  # Tool selection
        f"G97 S{spindle_speed} M03",  # Spindle on clockwise with RPM
    ]


@mcp.tool()
def move_to_safe_start(x: float, z: float) -> list[str]:
    """
    Moves the tool to a safe starting position before cutting.

    Args:
        x: X-coordinate in mm
        z: Z-coordinate in mm

    Returns:
        list[str]: A list of strings that contain the G-code commands to move the tool to a safe starting position
    """
    return [f"G0 X{x} Z{z}"]


@mcp.tool()
def face_stock(z_face: float, feed_rate: float) -> list[str]:
    """
    Faces the end of the stock to ensure it's flat.

    Args:
        z_face: Final Z position to face to (usually 0)
        feed_rate: Feed rate for facing

    Returns:
        list[str]: A list of strings that contain the G-code commands to face the end of the stock
    """
    return [
        f"G1 Z{z_face} F{feed_rate}",  # Feed to face
        "G0 Z2",  # Retract after facing
    ]

@mcp.tool()
def do_turning(
    start_diameter: float, final_diameter: float, length: float, feed_rate: float
) -> list[str]:
    """
    Turns along the full length of the cylinder to reduce its diameter uniformly.

    Args:
        start_diameter: Initial diameter of the rod in mm
        final_diameter: Final diameter after turning in mm
        length: Length of the cut along Z-axis in mm
        feed_rate: Feed rate in mm/rev

    Returns:
        list[str]: A list of strings that contain the G-code commands to cut along the full length of the cylinder to reduce its diameter uniformly
    """
    return [
        f"G0 X{start_diameter} Z0",  # Rapid to start position
        f"G1 X{final_diameter} Z-{length} F{feed_rate}",  # Turning pass
    ]


@mcp.tool()
def retract_and_end_program(
    retract_x: float = 100, retract_z: float = 100
) -> list[str]:
    """
    Retracts the tool to a safe position and ends the program.

    Args:
        retract_x: X-coordinate for safe retract
        retract_z: Z-coordinate for safe retract

    Returns:
        list[str]: A list of strings that contain the G-code commands to retract the tool to a safe position and end the program
    """
    return [
        f"G0 X{retract_x} Z{retract_z}",  # Retract tool
        "M05",  # Stop spindle
        "M30",  # End of program
    ]


@mcp.tool()
async def add_text_in_paint(text: str) -> dict:
    """Given a text, take that text, create a new image, open it in mac preview, create a rectangle on the image and add the text to the rectangle

    Args:
        text (str): Text to add to the image

    Returns:
        dict: A message indicating if the text was added succesully or not and a helpful error message if it wasn't added successfully
    """
    try:
        open_paint_with_text_mac(text)
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Text:'{text}' added successfully to the paint application",
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Could not add the text to paint application. Error: {str(e)}.",
                )
            ]
        }


@mcp.tool()
def show_reasoning(reasoning: list[ReasoningStep]) -> dict:
    """Figures out the reasoning for solving a particular problem and displays it to the user

    Args:
        reasoning (list[ReasoningStep]): A list of strings that contain the reasoning for solving a particular problem

        Each ReasoningStep object has the following attributes:
            - step_text: A string that contains the reasoning for solving a particular problem
            - type_of_reasoning: A list of strings that contain the type of reasoning for solving a particular problem. This can only be one of the following: spatial, algorithmic, optimization, safety, other
            - reasoning_issues: A string that contains the issues in the reasoning for solving a particular problem
            - are_there_any_issues_in_reasoning: A boolean that contains whether there are any issues in the reasoning for solving a particular problem

    Returns:
        dict: A message showing the reasoning for solving a particular problem
    """
    return {
        "content": [
            TextContent(
                type="text",
                text=f"Reasoning:\n'{reasoning}'successfully determined and displayed to the user",
            )
        ]
    }


@mcp.tool()
def verify_step(verification: str) -> dict:
    """This tool is used by the LLM Agent to verify if the last performed step is correct or not.

    Args:
        verification (str): A string that contains justification or verification of the last performed step

    Returns:
        dict: A message showing the verification of the last performed step
    """
    return {
        "content": [
            TextContent(
                type="text",
                text=f"Verification:\n'{verification}' done for the last performed step",
            )
        ]
    }


# DEFINE RESOURCES


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    print("CALLED: get_greeting(name: str) -> str:")
    return f"Hello, {name}!"


# DEFINE AVAILABLE PROMPTS
@mcp.prompt()
def review_code(code: str) -> str:
    return f"Please review this code:\n\n{code}"
    print("CALLED: review_code(code: str) -> str:")


@mcp.prompt()
def debug_error(error: str) -> list[base.Message]:
    return [
        base.UserMessage("I'm seeing this error:"),
        base.UserMessage(error),
        base.AssistantMessage("I'll help debug that. What have you tried so far?"),
    ]


if __name__ == "__main__":
    # Check if running with mcp dev command
    print("STARTING")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution
