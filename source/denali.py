import pygame
from math import sqrt, sin, cos, radians
from numpy import clip
from glob import glob
from os import path, remove
from time import time
from json import dumps, loads

# store wires from inputs in gate instead?! good idea maybe!!!?

targetFPS = 150
displayFPS = True
backgroundColour = (31, 32, 38)
inventoryRadius = 100

portSize = 7
portSelectionSize=15
portColour = (127, 127, 133)
portBorderColour = [clip(value+25, 0, 255) for value in portColour]
inputSpread = 25

gateSize = 50
gateColour = (112, 119, 130)
gateShadowColour = [clip(value-20, 0, 255) for value in gateColour]

wireOffColour = (52, 99, 115)
wireOnColour = (89, 173, 201)

pygame.init()
pygame.font.init()
screen = pygame.display.set_mode((400,400), pygame.RESIZABLE)
pygame.display.set_caption("Denali LOGIC")
pygame.display.set_icon(pygame.image.load("denali.png"))
clock = pygame.time.Clock()
running = True

gateImages = {path.basename(image.removesuffix(".png")).upper():pygame.image.load(image) for image in glob("gates/*.png")}
gateTypes = list(gateImages.keys())

gates = {}
wires = {}

gateCount = 0

binImage = pygame.image.load("bin.png")

AND = lambda inputs:inputs[1]["active"] and inputs[2]["active"]
OR = lambda inputs: inputs[1]["active"] or inputs[2]["active"]
XOR = lambda inputs: inputs[1]["active"] != inputs[2]["active"]
NOT = lambda inputs: not inputs[1]["active"]

def createNewGate(gateType):
    gate = {
    "gateType": gateType,
    "position": [0,0],
    "drag": False,
    "inputs": {1:{"angle":180, "active":False,}} if gateType == "NOT" else {1:{"angle":180+inputSpread, "active":False}, 2:{"angle":180-inputSpread, "active":False}},
    "output": False,
    "tick": AND if gateType == "AND" else OR if gateType == "OR" else NOT if gateType == "NOT" else XOR if gateType == "XOR" else None
    }
    global gateCount
    gateID = gateCount
    gateCount += 1
    return gateID, gate

touchingPoint = lambda pos, pointPos, radius: sqrt(abs(pos[0] - pointPos[0])**2+abs(pos[1] - pointPos[1])**2) < radius
circlePointLocation = lambda pos, angle, radius: [(radius * cos(angle))+pos[0], (radius * sin(angle))+pos[1]]

dragging = False
drawing = False
drawingfrompoint = False

inventoryGates = {}

fpstimer = time()
fpscount = 0
fps = targetFPS
fpscountamount = 75

font = pygame.font.SysFont('Consolas', 15)

gateIOLocations = {}

while running:
    gatesToRemove = []
    wiresToRemove = []

    mouseX, mouseY = pygame.mouse.get_pos()

    fpscount += 1
    if fpscount == fpscountamount:
        fpscount = 0
        fps = 1/((time()-fpstimer)/fpscountamount)
        fpstimer = time()

    # COMPUTE
    for event in pygame.event.get():
        # End if window X is pressed
        if event.type == pygame.QUIT:
            running = False
        
        # Open Inventory
        if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB and not dragging and not drawing:
            dragging = True
            inventoryGates = {gateID:gate for gateID, gate in [createNewGate(gateType) for gateType in gateTypes]}
            for gateID, gate in inventoryGates.items():
                inventoryGates[gateID]["position"] = circlePointLocation((mouseX, mouseY), radians((list(inventoryGates.keys()).index(gateID)/len(inventoryGates))*360), inventoryRadius)
                gateIOLocations[gateID] = {
                    "inputs": {InputID:circlePointLocation(gate["position"], radians(Input["angle"]), gateSize) for InputID, Input in gate["inputs"].items()},
                    "output": circlePointLocation(gate["position"], 0, gateSize)
                }
        
        # Close Inventory And Choose Gate
        elif event.type == pygame.KEYUP and event.key == pygame.K_TAB and not drawing:
            for gateID, gate in inventoryGates.items():
                if touchingPoint((mouseX, mouseY), gate["position"], gateSize):
                    gates[gateID] = gate
            inventoryGates.clear()
            dragging = False

        for gateID, gate in gates.items():
            gateIOLocations[gateID] = {
                "inputs": {InputID:circlePointLocation(gate["position"], radians(Input["angle"]), gateSize) for InputID, Input in gate["inputs"].items()},
                "output": circlePointLocation(gate["position"], 0, gateSize)
            }

            gate["output"] = gate["tick"](gate["inputs"])

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 3:
                    for InputID, Input in gate["inputs"].items():
                        if touchingPoint((mouseX, mouseY), gateIOLocations[gateID]["inputs"][InputID], portSelectionSize):
                            drawing = True
                            drawingfrompoint = {"gateID":gateID, "inputID": InputID}
                            break
                    
                    if not drawing:
                        if touchingPoint((mouseX, mouseY), gateIOLocations[gateID]["output"], portSelectionSize):
                            drawing = True
                            drawingfrompoint = {"gateID":gateID, "inputID": False}
                
                elif event.button == 1 and not dragging:
                    if touchingPoint((mouseX, mouseY), gate["position"], gateSize):
                        dragging = True
                        gate["drag"] = True
                        gate["offsetX"] = gate["position"][0] - mouseX
                        gate["offsetY"] = gate["position"][1] - mouseY
                
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 3 and drawing:
                    drawnTo = False

                    for InputID, Input in gate["inputs"].items():
                        if touchingPoint((mouseX, mouseY), gateIOLocations[gateID]["inputs"][InputID], portSelectionSize):
                            drawnTo = {"gateID":gateID, "inputID": InputID}
                            break
                    
                    if not drawnTo:
                        if touchingPoint((mouseX, mouseY), gateIOLocations[gateID]["output"], portSelectionSize):
                            drawnTo = {"gateID":gateID, "inputID": False}
                    
                    if drawnTo and bool(drawingfrompoint["inputID"]) != bool(drawnTo["inputID"]) and drawingfrompoint["gateID"] != drawnTo["gateID"]:
                        if drawingfrompoint["inputID"] == False:
                            wires[dumps(drawnTo)] = drawingfrompoint
                        else:
                            wires[dumps(drawingfrompoint)] = drawnTo
                    
                elif event.button == 1 and gate["drag"]:
                    gate["drag"] = False
                    if 0 <= gate["position"][0] <= 100 and pygame.display.get_surface().get_size()[1] >= gate["position"][1] >= pygame.display.get_surface().get_size()[1]-105 and dragging:
                        gatesToRemove.append(gateID)
                    dragging = False

            elif event.type == pygame.MOUSEMOTION and gate["drag"]:
                gate["position"][0] = mouseX + gate["offsetX"]
                gate["position"][1] = mouseY + gate["offsetY"]
                gateIOLocations[gateID] = {
                    "inputs": {InputID:circlePointLocation(gate["position"], radians(Input["angle"]), gateSize) for InputID, Input in gate["inputs"].items()},
                    "output": circlePointLocation(gate["position"], 0, gateSize)
                }

        if not dragging and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for gateID, gate in gates.items():
                gate["drag"] = True
                gate["offsetX"] = gate["position"][0] - mouseX
                gate["offsetY"] = gate["position"][1] - mouseY
    
    if event.type == pygame.MOUSEBUTTONUP and event.button == 3 and drawing:
        drawing = False
        drawingfrompoint = False
    
    for gateID in gatesToRemove:
        gates.pop(gateID)

    for wireInput,wireOutput in wires.items():
        wireInputLoaded = loads(wireInput)
        if wireInputLoaded["gateID"] in gatesToRemove or wireOutput["gateID"] in gatesToRemove:
            wiresToRemove.append(wireInput)
        else:
            gates[wireInputLoaded["gateID"]]["inputs"][wireInputLoaded["inputID"]]["active"] = gates[wireOutput["gateID"]]["output"]
    
    for wireInput in wiresToRemove:
        wires.pop(wireInput)


    # RENDER

    screen.fill(backgroundColour)

    allGates = gates|inventoryGates
    for gateID, gate in allGates.items():
        # SHADOW
        pygame.draw.circle(screen, gateShadowColour, gate["position"], gateSize+2)
        pygame.draw.circle(screen, gateShadowColour, [value + 3 for value in gate["position"]], gateSize)

        # MAIN
        pygame.draw.circle(screen, gateColour, gate["position"], gateSize)
        
        # IMAGE
        image = gateImages[gate["gateType"]]
        imageLocation = [value - gateSize/2 for value in gate["position"]]
        imageLocation[0] -= 15 # X ADJUSTMENT
        imageLocation[1] += 5 # Y ADJUSTMENT
        screen.blit(image, imageLocation)

        # INPUTS
        for InputID, Input in gate["inputs"].items():
            location = gateIOLocations[gateID]["inputs"][InputID]
            pygame.draw.circle(screen, portBorderColour, location, portSize+2)
            pygame.draw.circle(screen, portColour, location, portSize)
        
        # OUTPUT
        location = gateIOLocations[gateID]["output"]
        pygame.draw.circle(screen, portBorderColour, location, portSize+2)
        pygame.draw.circle(screen, portColour, location, portSize)

    if drawingfrompoint:
        gate = gates[drawingfrompoint["gateID"]]
        location = circlePointLocation(gate["position"], radians(gate["inputs"][drawingfrompoint["inputID"]]["angle"] if drawingfrompoint["inputID"] else 0), gateSize)
        pygame.draw.line(screen, wireOffColour if drawingfrompoint["inputID"]!=False else gates[drawingfrompoint["gateID"]]["output"], location, pygame.mouse.get_pos()) # add on/off colours rather than just WHITE

    # WIRES
    for wireInput,wireOutput in wires.items():
        wireInputLoaded = loads(wireInput)
        pygame.draw.line(screen, wireOnColour if gates[wireOutput["gateID"]]["output"] == True else wireOffColour,
            gateIOLocations[wireInputLoaded["gateID"]]["inputs"][wireInputLoaded["inputID"]],
            gateIOLocations[wireOutput["gateID"]]["output"]
        )

    # BIN
    screen.blit(binImage, (0, pygame.display.get_surface().get_size()[1]-105))
    
    #FPS COUNT
    if displayFPS: screen.blit(font.render(f'FPS: {round(fps)}', False, (255, 255, 255)),(0,0))

    pygame.display.flip()

    clock.tick(targetFPS)

pygame.quit()
