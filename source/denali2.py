import pygame
from numpy import array, transpose, dot
from os import path
from math import sin, cos, pi, sqrt, asin

# Constant Variables
IMAGES_DIRECTORY = "assets\\images"

INITIAL_WINDOW_SIZE = (900, 900)

TARGET_FPS = 150

BACKGROUND_COLOUR = (31, 32, 38)
GATE_SIZE = 50
GATE_COLOUR = (112, 119, 130)
GATE_SHADOW_COLOUR = (92, 99, 110)

PORT_SIZE = 7
PORT_SELECTION_SIZE=15
PORT_COLOUR = (127, 127, 133)
PORT_BORDER_COLOUR = (152, 152, 158)
INPUT_PORT_SPREAD = (5 * pi) / 18

WIRE_THICKNESS = 5
WIRE_DELETE_SIZE = 10
WIRE_OFF_COLOUR = (66,111,122)
WIRE_ON_COLOUR = (124,178,191)

BIN_SIZE = 35

INVENTORY_RADIUS = 115
INVENTORY_ANGLE_OFFSET = pi/2

GATE_TYPES = ["AND", "OR", "XOR", "NOT", "IO"]

INPUT_OUTPUT_LIGHT_SIZE=30

# Lambda Functions
getDistance = lambda pos1, pos2: sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

# Load Images
gateImages = {
    gateType: pygame.image.load(path.join(IMAGES_DIRECTORY, "gates", gateType.lower()+".png"))
    for gateType in ["AND", "OR", "XOR", "NOT"]
    }
binImage = pygame.image.load(path.join(IMAGES_DIRECTORY,"bin.png"))
denaliImage = pygame.image.load(path.join(IMAGES_DIRECTORY, "denali.png"))

# Boolean Logic Functions for Gate Tick
tickFunctions = {
    "AND" : lambda inputs: inputs[0].state and inputs[1].state,
    "OR" : lambda inputs: inputs[0].state or inputs[1].state,
    "XOR" : lambda inputs: inputs[0].state ^ inputs[1].state,
    "NOT" : lambda inputs: not inputs[0].state
}

# Visual Offsets for Gate Elements
inputOffsets = [
    [
        [-GATE_SIZE, 0]
    ],
    [
        [-(cos(INPUT_PORT_SPREAD) * GATE_SIZE), -(sin(INPUT_PORT_SPREAD) * GATE_SIZE)],
        [-(cos(INPUT_PORT_SPREAD) * GATE_SIZE), sin(INPUT_PORT_SPREAD) * GATE_SIZE]
    ]
    ]

outputOffset = [GATE_SIZE, 0]

class NullInput:
    def __init__(self):
        self.state = False

falseInput = NullInput()

class Gate:
    def __init__(self, gateType, position):
        self.position = position

        self.type = gateType
        self.state = False
        self.inputs = [falseInput for i in range(1 if gateType == "NOT" else 2)]
        self.tickFunction = tickFunctions[gateType]

        self.dragging = False
        self.delete = False

    def tick(self):
        self.state = self.tickFunction(self.inputs)

class InputOutput:
    def __init__(self,position):
        self.position = position

        self.differentiated = False
        self.state = False
        self.inputs = [falseInput]

        self.dragging = False
        self.delete = False
    
    def tick(self):
        if self.differentiated == "Output":
            self.state = self.inputs[0].state
        
        elif self.inputs[0].__class__ != NullInput:
            self.differentiated = "Output"

# Setup pygame
pygame.init()
pygame.font.init()
screen = pygame.display.set_mode(INITIAL_WINDOW_SIZE, pygame.RESIZABLE)
pygame.display.set_caption("Denali LOGIC v2")
pygame.display.set_icon(denaliImage)
clock = pygame.time.Clock()
font = pygame.font.SysFont('Consolas', 15)

# Setup Logic Simulator Variables
gates = []
inventoryGates = []

running = True

flags = {
    "viewDrag": False,
    "gateDrag": False,
    "wireDeleteDrag": False,
    "inventoryDisplayed": False,
    }

initialCursorPosition = array(pygame.mouse.get_pos())
viewOffset = array([0,0])
initialViewOffset = viewOffset
gateDragOffset = array([0,0])

wireOrigin = None

while running:
    actualCursorPosition = array(pygame.mouse.get_pos())
    cursorPosition = array(pygame.mouse.get_pos()) - viewOffset

    # Compute
    if flags["viewDrag"]: viewOffset = initialViewOffset + actualCursorPosition - initialCursorPosition

    for gate in gates:
        gate.tick()
        
        # Move gate if dragging gate
        if gate.dragging:
            gate.position = cursorPosition + gateDragOffset
            if not flags["gateDrag"]:
                gate.dragging = False
                if getDistance(actualCursorPosition, (50, pygame.display.get_surface().get_size()[1]-55)) < BIN_SIZE: gate.delete = True

        # Delete gate if marked for deletion
        if gate.delete: gates.remove(gate)

        # Delete Wires Near Cursor  
        if flags["wireDeleteDrag"]:
            for index, gateInput in enumerate(gate.inputs):
                if gateInput.__class__ != NullInput:
                    startPoint = array(gateInput.position) + array(outputOffset)
                    endPoint = array(gate.position) + array(inputOffsets[len(gate.inputs)-1][index])

                    lineDistance = getDistance(startPoint, endPoint)

                    yDiffDistanceRatio = (((startPoint[1] - endPoint[1]) / lineDistance) * (-1 if startPoint[0] <= endPoint[0] else 1))
                    
                    rotationMatrix = array([
                        [cos(asin(yDiffDistanceRatio)), yDiffDistanceRatio],
                        [-yDiffDistanceRatio, cos(asin(yDiffDistanceRatio))]
                        ])
                    
                    transformedCursorPosition = dot(rotationMatrix,  transpose(cursorPosition-(0.5 * (endPoint + startPoint))))
                    
                    if -(lineDistance/2) < transformedCursorPosition[0] < (lineDistance/2) and -(WIRE_DELETE_SIZE/2) < transformedCursorPosition[1] < (WIRE_DELETE_SIZE/2):
                        gate.inputs[index] = falseInput

    for event in pygame.event.get():
        if event.type == pygame.QUIT: running = False
        if event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
            # Inventory
            if event.key == pygame.K_TAB:
                if event.type == pygame.KEYDOWN and not any(flags.values()):
                    flags["inventoryDisplayed"] = True
                    for index, gateType in enumerate(GATE_TYPES):
                        rotationAngle = ((2*pi*index) / len(GATE_TYPES)) + INVENTORY_ANGLE_OFFSET
                        rotationMatrix = array([
                            [cos(rotationAngle), sin(rotationAngle)],
                            [-sin(rotationAngle), cos(rotationAngle)]
                            ])
                        position = transpose(transpose(array([cursorPosition])) + dot(rotationMatrix, array([[INVENTORY_RADIUS], [0]])))[0]
                        inventoryGates.append(Gate(gateType, position) if gateType != "IO" else InputOutput(position))
                if event.type == pygame.KEYUP:
                    flags["inventoryDisplayed"] = False
                    for index, gate in enumerate(inventoryGates):
                        if getDistance(cursorPosition, gate.position) < GATE_SIZE:
                            gates.append(inventoryGates.pop(index))
                            break
                    inventoryGates.clear()

        elif event.type == pygame.MOUSEBUTTONDOWN and not any(flags.values()):
            if event.button == 3:
                # Create Wire Origin
                for gate in gates:
                    outputPosition = array(gate.position) + array(outputOffset)
                    if getDistance(cursorPosition, outputPosition) < PORT_SELECTION_SIZE:
                        wireOrigin = {"Start":False, "Gate": gate, "GateInputIndex": None}
                    else:
                        for gateInputIndex in range(len(gate.inputs)):
                            inputPosition = array(gate.position) + array(inputOffsets[len(gate.inputs)-1][gateInputIndex])
                            if getDistance(cursorPosition, inputPosition) < PORT_SELECTION_SIZE:
                                wireOrigin = {"Start":True, "Gate": gate, "GateInputIndex": gateInputIndex}
                                break
                    if wireOrigin: break

                # Activate Wire Delete Drag
                if not wireOrigin: flags["wireDeleteDrag"] = True
            
            elif event.button == 1:
                # Activate View Drag
                if not any([getDistance(cursorPosition, gate.position) < GATE_SIZE for gate in gates]):
                    flags["viewDrag"] = True
                    initialCursorPosition = actualCursorPosition
                    initialViewOffset = viewOffset
                # Activate Gate Drag
                else:
                    for index, gate in enumerate(gates):
                        if getDistance(cursorPosition, gate.position) < GATE_SIZE:
                            if gate.__class__ == InputOutput and gate.differentiated == "Input" and getDistance(cursorPosition, gate.position) < INPUT_OUTPUT_LIGHT_SIZE:
                                gate.state = not gate.state
                                break
                            flags["gateDrag"] = True
                            gate.dragging = True
                            gateDragOffset = array(gate.position) - cursorPosition
                            gates.append(gates.pop(index))
                            break

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3:
                # Create Wire
                if wireOrigin:
                    if wireOrigin["Start"]:
                        for gate in gates:
                            outputPosition = array(gate.position) + array(outputOffset)
                            if getDistance(cursorPosition, outputPosition) < PORT_SELECTION_SIZE:
                                if gate == wireOrigin["Gate"]: break
                                wireOrigin["Gate"].inputs[wireOrigin["GateInputIndex"]] = gate
                                        
                                # Differentiate Input / Output
                                if gate.__class__ == InputOutput: gate.differentiated = "Input"

                                break
                    else:
                        for gate in gates:
                            for gateInputIndex in range(len(gate.inputs)):
                                inputPosition = array(gate.position) + array(inputOffsets[len(gate.inputs)-1][gateInputIndex])
                                if getDistance(cursorPosition, inputPosition) < PORT_SELECTION_SIZE:
                                    if gate == wireOrigin["Gate"]: break
                                    gate.inputs[gateInputIndex] = wireOrigin["Gate"]

                                    # Differentiate Input / Output
                                    if wireOrigin["Gate"].__class__ == InputOutput: wireOrigin["Gate"].differentiated = "Input"

                                    break
                    wireOrigin = None
                # Deactivate Wire Delete Drag
                elif flags["wireDeleteDrag"]: flags["wireDeleteDrag"] = False

            if event.button == 1:
                # Deactivate View Drag
                if flags["viewDrag"]: flags["viewDrag"] = False
                # Deactivate Gate Drag
                else: flags["gateDrag"] = False
        
                    
            


    # Render
    screen.fill(BACKGROUND_COLOUR)

    for gate in gates + inventoryGates:
            
        # Render Gate Shadow
        pygame.draw.circle(screen, GATE_SHADOW_COLOUR, gate.position + viewOffset, GATE_SIZE+2)
        pygame.draw.circle(screen, GATE_SHADOW_COLOUR, [value + 3 for value in gate.position + viewOffset], GATE_SIZE)

        # Render Gate Main Body
        pygame.draw.circle(screen, GATE_COLOUR, gate.position + viewOffset, GATE_SIZE)

        # Input / Output Gates Only
        if gate.__class__ == InputOutput:
            # Render Input / Output Centre
            pygame.draw.circle(screen, GATE_SHADOW_COLOUR, gate.position + viewOffset, INPUT_OUTPUT_LIGHT_SIZE+2)
            pygame.draw.circle(screen, WIRE_ON_COLOUR if gate.state else WIRE_OFF_COLOUR, gate.position + viewOffset, INPUT_OUTPUT_LIGHT_SIZE)

        # Logical Gates Only
        else:
            # Render Gate Image
            image = gateImages[gate.type]
            imageLocation = array([value - (GATE_SIZE/2) for value in gate.position + viewOffset]) + array([-15,5])
            screen.blit(image, imageLocation)

        # Render Gate Ports
        if gate.__class__ == Gate or gate.differentiated != "Input":
            for offset in inputOffsets[len(gate.inputs)-1]:
                inputPosition = array(gate.position + viewOffset) + array(offset)
                pygame.draw.circle(screen, PORT_BORDER_COLOUR, inputPosition, PORT_SIZE+2)
                pygame.draw.circle(screen, PORT_COLOUR, inputPosition, PORT_SIZE)

        if gate.__class__ == Gate or gate.differentiated != "Output":
            outputPosition = array(gate.position + viewOffset) + array(outputOffset)
            pygame.draw.circle(screen, PORT_BORDER_COLOUR, outputPosition, PORT_SIZE+2)
            pygame.draw.circle(screen, PORT_COLOUR, outputPosition, PORT_SIZE)

        for index, inputGate in enumerate(gate.inputs):
            if inputGate.__class__ != NullInput:
                # Null Deleted Inputs
                if inputGate.delete:
                    gate.inputs[index] = falseInput
                    continue
                # Render Wires
                pygame.draw.line(screen, WIRE_ON_COLOUR if inputGate.state else WIRE_OFF_COLOUR,
                                array(inputGate.position) + array(outputOffset) + viewOffset,
                                array(gate.position) + array(inputOffsets[len(gate.inputs)-1][index]) + viewOffset, WIRE_THICKNESS)

    # Render Drawn Wire
    if wireOrigin:
        startPosition = (array(wireOrigin["Gate"].position)
                        + array(outputOffset if not wireOrigin["Start"] else inputOffsets[len(wireOrigin["Gate"].inputs)-1][wireOrigin["GateInputIndex"]])
                        + viewOffset)
        pygame.draw.line(screen, WIRE_ON_COLOUR if not wireOrigin["Start"] and wireOrigin["Gate"].state else WIRE_OFF_COLOUR,
                        startPosition,
                        actualCursorPosition, WIRE_THICKNESS)

    # Bin
    screen.blit(binImage, (0, pygame.display.get_surface().get_size()[1]-105))
    
    clock.tick(TARGET_FPS)
    pygame.display.flip()

pygame.quit()
