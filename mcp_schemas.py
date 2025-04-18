from pydantic import BaseModel
from typing import List, Optional
from utils import ReasoningStep

# Input Schemas
class SetUnitsAndModeInput(BaseModel):
    pass

class SelectToolAndStartSpindleInput(BaseModel):
    tool_number: str
    offset: int
    spindle_speed: int

class MoveToSafeStartInput(BaseModel):
    x: float
    z: float

class FaceStockInput(BaseModel):
    z_face: float
    feed_rate: float

class DoTurningInput(BaseModel):
    start_diameter: float
    final_diameter: float
    length: float
    feed_rate: float

class RetractAndEndProgramInput(BaseModel):
    retract_x: float = 100
    retract_z: float = 100

class AddTextInPaintInput(BaseModel):
    text: str

class ShowReasoningInput(BaseModel):
    reasoning: List[ReasoningStep]

class VerifyStepInput(BaseModel):
    verification: str

# Output Schemas
class GCodeOutput(BaseModel):
    result: List[str]

class TextContentOutput(BaseModel):
    result: List[dict]

class GreetingOutput(BaseModel):
    result: str

class CodeReviewOutput(BaseModel):
    result: str

class DebugErrorOutput(BaseModel):
    result: List[dict] 