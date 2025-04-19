# CNC Machining Task with MCP Client

This project implements an AI agent specialized in CNC (Computer Numerical Control) machining operations. The agent is designed to generate CNC programs for specific machining tasks using an iterative reasoning approach.

## Architecture

The agent follows a Perception -> Memory -> Decision -> Action framework:

1. **Perception**: The agent first understands the task requirements through the `PerceptionObject` class, which:
   - Captures task details, dimensions, and operations
   - Validates the understanding using Pydantic models
   - Provides structured input for decision making

2. **Memory**: The `Memory` class manages:
   - User preferences and session-specific information
   - History of tool executions and their results
   - Context for decision making
   - User preferences can be added at the start of execution through the `preferences` list

3. **Decision**: The `Decision` class:
   - Constructs prompts based on available tools and memory
   - Makes decisions about which tool to execute next
   - Validates decisions before execution
   - Ensures alignment with task goals
   - At present, `code.interact()` sits in the decision class basically to pause execution so that the user can gain visibility into what all has happened and what the Agent has interpreted so far. Feel free to comment this if you want to step out of debugging mode and use agent directly.

4. **Action**: The `Action` class:
   - Executes tool calls based on decisions
   - Handles tool execution results
   - Stores execution history in memory
   - Manages the continuation state

## Input/Output Validation

The project uses `mcp_schemas.py` to ensure consistent input and output validation:

1. **Input Schemas**: Each tool has a corresponding input schema (e.g., `ShowReasoningInput`, `DoTurningInput`) that:
   - Defines required parameters
   - Validates input types
   - Provides clear documentation

2. **Output Schemas**: Each tool has a corresponding output schema (e.g., `GCodeOutput`, `TextContentOutput`) that:
   - Standardizes output format
   - Ensures consistent response structure
   - Makes parsing easier for subsequent calls

## Prompt Management

Prompts are broken down into reusable components in `sub_prompts.py`:

1. **General Instructions**: Core agent capabilities and reasoning modes
2. **Special Instructions**: Tool usage guidelines and constraints
3. **Fallback Handling**: Error handling and recovery strategies
4. **Response Instructions**: Format requirements for different types of responses

There are two additional components for telling what output format the perception step should follow and what output format the decision step should follow. Perception and Decision are the only components which perform LLM Calls.

## Task Description

The agent is given a specific CNC machining task:
- Input: A cylindrical rod of length 10 cm and diameter 5 cm
- Output: A CNC program to turn the rod to a diameter of 3 cm while maintaining the original length
- Constraint: Turning operation must be performed in the XZ plane

## How to Run
1. Create a `.env` file in the parent directory

2. Add your OpenAI API key: `OPENAI_API_KEY=your_api_key_here`

3. Run the MCP client:
```bash
python mcp_client.py
```

4. If you have uv installed, then simply run
```bash
uv run mcp_client.py
```

The program will:
1. Connect to the MCP server
2. Initialize the CNC agent
3. Process the machining task through multiple iterations
4. Generate a CNC program
5. Visualize the final program using the paint tool

## Agent Capabilities

The CNC agent is designed with the following capabilities:
- Spatial reasoning for understanding geometry and spatial relationships
- Algorithmic reasoning for sequencing operations
- Optimization reasoning for efficient tool paths and material usage
- Safety considerations for operator, machine, and part
- Iterative problem-solving approach
- Ability to verify steps and handle failures gracefully

## Output

The agent will:
1. Break down the task into logical steps
2. Generate appropriate CNC commands
3. Verify each operation
4. Create a comprehensive CNC program with comments
5. Display the final program in the paint tool

## Error Handling

The agent includes fallback mechanisms:
- Retries operations with modified parameters if needed
- Clearly states uncertainties and reasons for them
- Provides partial solutions with explanations if a complete solution isn't possible
- Explicitly communicates the reasons for any failures