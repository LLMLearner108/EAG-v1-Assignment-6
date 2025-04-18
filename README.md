# CNC Machining Task with MCP Client

This project implements an AI agent specialized in CNC (Computer Numerical Control) machining operations. The agent is designed to generate CNC programs for specific machining tasks using an iterative reasoning approach.

## Task Description

The agent is given a specific CNC machining task:
- Input: A cylindrical rod of length 10 cm and diameter 5 cm
- Output: A CNC program to turn the rod to a diameter of 3 cm while maintaining the original length
- Constraint: Turning operation must be performed in the XZ plane

## How to Run
1. Create a `.env` file in the parent directory

2. Add your OpenAI API key: `OPENAI_API_KEY=your_api_key_here`

3. Navigate to the `modified_assignment_4` directory:
```bash
cd modified_assignment_4
```

4. Run the MCP client:
```bash
python mcp_client.py
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

## Notes

- The agent uses GPT-4o for reasoning and program generation
- Each iteration is limited to 10 steps
- The program includes a 3-second delay between iterations to respect API rate limits
- The paint tool is used as a notepad to display the final CNC program