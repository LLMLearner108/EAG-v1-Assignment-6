# basic import
from mcp.server.fastmcp import FastMCP
import sys
from use_paint_preview_with_mac import *
from mcp_schemas import *

# instantiate an MCP server client
mcp = FastMCP("CNC Simulator")

# DEFINE TOOLS


@mcp.tool()
def set_units_and_mode() -> GCodeOutput:
    """
    Sets the CNC machine to use metric units, absolute positioning,
    feed per revolution mode, and selects the XZ plane.

    Returns:
        GcodeOutput (list of strings): A list of G-code commands to set the units and mode
    """
    return GCodeOutput(
        result=[
            "G21",  # Units in mm
            "G90",  # Absolute positioning
            "G95",  # Feed per revolution
            "G18",  # XZ plane selection
        ]
    )


@mcp.tool()
def select_tool_and_start_spindle(input: SelectToolAndStartSpindleInput) -> GCodeOutput:
    """
    Selects the tool and starts the spindle at a given speed.

    Args:
        input (SelectToolAndStartSpindleInput): Input parameters containing:
            - tool_number (str): Tool number (e.g. T0101)
            - offset (int): Tool offset number
            - spindle_speed (int): Spindle speed in RPM

    Returns:
        GCodeOutput (list of strings): A list of G-code commands to select the tool and start the spindle
    """
    return GCodeOutput(
        result=[
            f"T{input.tool_number}{input.offset:02d}",  # Tool selection
            f"G97 S{input.spindle_speed} M03",  # Spindle on clockwise with RPM
        ]
    )


@mcp.tool()
def move_to_safe_start(input: MoveToSafeStartInput) -> GCodeOutput:
    """
    Moves the tool to a safe starting position before cutting.

    Args:
        input (MoveToSafeStartInput): Input parameters containing:
            - x (float): X-coordinate in mm
            - z (float): Z-coordinate in mm

    Returns:
        GcodeOutput (list of strings): A list of G-code commands to move the tool to a safe starting position
    """
    return GCodeOutput(result=[f"G0 X{input.x} Z{input.z}"])


@mcp.tool()
def face_stock(input: FaceStockInput) -> GCodeOutput:
    """
    Faces the end of the stock to ensure it's flat.

    Args:
        input (FaceStockInput): Input parameters containing:
            - z_face (float): Final Z position to face to (usually 0)
            - feed_rate (float): Feed rate for facing

    Returns:
        GcodeOutput (list of strings): A list of G-code commands to face the end of the stock
    """
    return GCodeOutput(
        result=[
            f"G1 Z{input.z_face} F{input.feed_rate}",  # Feed to face
            "G0 Z2",  # Retract after facing
        ]
    )


@mcp.tool()
def do_turning(input: DoTurningInput) -> GCodeOutput:
    """
    Turns along the full length of the cylinder to reduce its diameter uniformly.

    Args:
        input (DoTurningInput): Input parameters containing:
            - start_diameter (float): Initial diameter of the rod in mm
            - final_diameter (float): Final diameter after turning in mm
            - length (float): Length of the cut along Z-axis in mm
            - feed_rate (float): Feed rate in mm/rev

    Returns:
        GcodeOutput (list of strings)A list of G-code commands to cut along the full length of the cylinder
    """
    return GCodeOutput(
        result=[
            f"G0 X{input.start_diameter} Z0",  # Rapid to start position
            f"G1 X{input.final_diameter} Z-{input.length} F{input.feed_rate}",  # Turning pass
        ]
    )


@mcp.tool()
def retract_and_end_program(input: RetractAndEndProgramInput) -> GCodeOutput:
    """
    Retracts the tool to a safe position and ends the program.

    Args:
        input (RetractAndEndProgramInput): Input parameters containing:
            - retract_x (float): X-coordinate for safe retract (default: 100)
            - retract_z (float): Z-coordinate for safe retract (default: 100)

    Returns:
        GcodeOutput (list of strings): A list of G-code commands to retract the tool and end the program
    """
    return GCodeOutput(
        result=[
            f"G0 X{input.retract_x} Z{input.retract_z}",  # Retract tool
            "M05",  # Stop spindle
            "M30",  # End of program
        ]
    )


@mcp.tool()
async def add_text_in_paint(input: AddTextInPaintInput) -> TextContentOutput:
    """
    Creates a new image, opens it in Mac Preview, creates a rectangle on the image and adds the text to the rectangle.

    Args:
        input (AddTextInPaintInput): Input parameters containing:
            - text: Text to add to the image

    Returns:
        TextContentOutput: A message indicating if the text was added successfully or not
    """
    try:
        open_paint_with_text_mac(input.text)
        return TextContentOutput(
            result=[
                {
                    "type": "text",
                    "text": f"Text:'{input.text}' added successfully to the paint application",
                }
            ]
        )
    except Exception as e:
        return TextContentOutput(
            result=[
                {
                    "type": "text",
                    "text": f"Could not add the text to paint application. Error: {str(e)}.",
                }
            ]
        )


@mcp.tool()
def show_reasoning(input: ShowReasoningInput) -> TextContentOutput:
    """
    Displays the reasoning for solving a particular problem to the user.

    Args:
        input (ShowReasoningInput): Input parameters containing:
            - reasoning: A list of ReasoningStep objects containing:
                - step_text (str): The reasoning text
                - type_of_reasoning list(str): Type of reasoning (spatial, algorithmic, optimization, safety, other)
                - reasoning_issues (str): Issues in the reasoning
                - are_there_any_issues_in_reasoning (bool): Boolean indicating if there are issues

    Returns:
        TextContentOutput: A message showing the reasoning for solving the problem
    """
    return TextContentOutput(
        result=[
            {
                "type": "text",
                "text": f"Reasoning:\n'{input.reasoning}' successfully determined and displayed to the user",
            }
        ]
    )


@mcp.tool()
def verify_step(input: VerifyStepInput) -> TextContentOutput:
    """
    Verifies if the last performed step is correct or not.

    Args:
        input (VerifyStepInput): Input parameters containing:
            - verification: Justification or verification of the last performed step

    Returns:
        TextContentOutput: A message showing the verification of the last performed step
    """
    return TextContentOutput(
        result=[
            {
                "type": "text",
                "text": f"Verification:\n'{input.verification}' done for the last performed step",
            }
        ]
    )


# DEFINE RESOURCES


@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> GreetingOutput:
    """Get a personalized greeting"""
    print("CALLED: get_greeting(name: str) -> str:")
    return GreetingOutput(result=f"Hello, {name}!")


# DEFINE AVAILABLE PROMPTS
@mcp.prompt()
def review_code(code: str) -> CodeReviewOutput:
    return CodeReviewOutput(result=f"Please review this code:\n\n{code}")
    print("CALLED: review_code(code: str) -> str:")


@mcp.prompt()
def debug_error(error: str) -> DebugErrorOutput:
    return DebugErrorOutput(
        result=[
            {"role": "user", "content": "I'm seeing this error:"},
            {"role": "user", "content": error},
            {
                "role": "assistant",
                "content": "I'll help debug that. What have you tried so far?",
            },
        ]
    )


if __name__ == "__main__":
    # Check if running with mcp dev command
    print("STARTING")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution
