import pygame
from math import sqrt, sin, cos, radians
from numpy import clip
from glob import glob
from os import path, remove
from time import time
from json import dumps, loads

FPS = 150
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

gates = []
wires = {}

gateCount = 0

binImage = pygame.image.load("bin.png")

class Gate:
    def __init__(self, gateType):
        self.gateType = gateType
        self.position = [50,50]
        self.drag = False
        self.inputs = {1:{"angle":180, "active":False,}} if gateType == "NOT" else {1:{"angle":180+inputSpread, "active":False}, 2:{"angle":180-inputSpread, "active":False}}
        self.output = False
        global gateCount
        self.id = gateCount
        gateCount += 1
    
    def touching(self, pos):
        a = abs(pos[0] - self.position[0])
        b = abs(pos[1] - self.position[1])
        c = sqrt((a*a)+(b*b))
        return c < gateSize
    
    def tick(self):
        global wires
        global gates
        for inputID in self.inputs:
            key = dumps({"gateID":self.id, "inputID":inputID})
            if key in wires:
                self.inputs[inputID]["active"] = [gate for gate in gates if gate.id == wires[key]["gateID"]][0].output
        self.output = self.inputs[1]["active"] and self.inputs[2]["active"] if self.gateType == "AND" else self.inputs[1]["active"] or self.inputs[2]["active"] if self.gateType == "OR" else self.inputs[1]["active"] != self.inputs[2]["active"] if self.gateType == "XOR" else not self.inputs[1]["active"]



dragging = False
drawing = False
drawingfrompoint = False

inventoryGates = []

fpstimer = time()
fpscount = 0
fps = FPS

font = pygame.font.SysFont('Consolas', 15)

gateIOLocations = {}

while running:
    fpscount += 1
    if fpscount == 75:
        fpscount = 0
        fps = 1/((time()-fpstimer)/75)
        fpstimer = time()
    
    for gate in gates: gate.tick()

    # COMPUTE
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB and not dragging and not drawing:
            dragging = True
            inventoryGates = [Gate(gateType) for gateType in gateTypes]
            x,y = pygame.mouse.get_pos()
            for gate in inventoryGates:
                angle = radians((inventoryGates.index(gate)/len(inventoryGates))*360)
                gate.position = [(inventoryRadius * cos(angle))+x, (inventoryRadius * sin(angle))+y]
        
        elif event.type == pygame.KEYUP and event.key == pygame.K_TAB and not drawing:
            for gate in inventoryGates:
                if gate.touching(pygame.mouse.get_pos()):
                    gates.insert(0, gate)
            inventoryGates.clear()
            dragging = False
            
        else:
            gateIOLocations = {}

            for gate in gates:
                gate.tick()
                
                gateIOLocations[gate.id] = {
                    "inputs":{InputID:[(gateSize * cos(radians(Input["angle"])))+gate.position[0], (gateSize * sin(radians(Input["angle"])))+gate.position[1]] for InputID, Input in gate.inputs.items()},
                    "output":[(gateSize * cos(0))+gate.position[0], (gateSize * sin(0))+gate.position[1]]
                    }

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and not dragging:
                    for InputID, Input in gate.inputs.items():
                        angle = radians(Input["angle"])
                        location = [(gateSize * cos(angle))+gate.position[0], (gateSize * sin(angle))+gate.position[1]]
                        a = abs(event.pos[0] - location[0])
                        b = abs(event.pos[1] - location[1])
                        c = sqrt((a*a)+(b*b))
                        if c < portSelectionSize:
                            drawing = True
                            drawingfrompoint = {"gateID":gate.id, "inputID": InputID}
                        
                        if not drawingfrompoint:
                            angle = 0
                            location = [(gateSize * cos(angle))+gate.position[0], (gateSize * sin(angle))+gate.position[1]]
                            a = abs(event.pos[0] - location[0])
                            b = abs(event.pos[1] - location[1])
                            c = sqrt((a*a)+(b*b))
                            if c < portSelectionSize:
                                drawing = True
                                drawingfrompoint = {"gateID":gate.id, "inputID": False}

                            
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 3 and drawing:
                    drawnTo = False

                    for InputID, Input in gate.inputs.items():
                        angle = radians(Input["angle"])
                        location = [(gateSize * cos(angle))+gate.position[0], (gateSize * sin(angle))+gate.position[1]]
                        a = abs(event.pos[0] - location[0])
                        b = abs(event.pos[1] - location[1])
                        c = sqrt((a*a)+(b*b))
                        if c < portSelectionSize:
                            drawnTo = {"gateID":gate.id, "inputID": InputID}
                            break
                    if not drawnTo:
                        angle = 0
                        location = gateIOLocations[gate.id]["output"]
                        a = abs(event.pos[0] - location[0])
                        b = abs(event.pos[1] - location[1])
                        c = sqrt((a*a)+(b*b))
                        if c < portSelectionSize:
                            drawnTo = {"gateID":gate.id, "inputID": False}
                    if drawnTo and bool(drawingfrompoint["inputID"]) != bool(drawnTo["inputID"]) and drawingfrompoint["gateID"] != drawnTo["gateID"]:
                        if drawingfrompoint["inputID"] == False:
                            wires[dumps(drawnTo)] = drawingfrompoint
                        else:
                            wires[dumps(drawingfrompoint)] = drawnTo
                    

                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not dragging:
                    if gate.touching(event.pos):
                        dragging = True
                        gate.drag = True
                        mouse_x, mouse_y = event.pos
                        gate.offset_x = gate.position[0] - mouse_x
                        gate.offset_y = gate.position[1] - mouse_y
                
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and gate.drag:
                    gate.drag = False
                    if 0 <= gate.position[0] <= 100 and pygame.display.get_surface().get_size()[1] >= gate.position[1] >= pygame.display.get_surface().get_size()[1]-105 and dragging:
                        gates.remove(gate)
                    dragging = False

                elif event.type == pygame.MOUSEMOTION and gate.drag:
                    mouse_x, mouse_y = event.pos
                    gate.position[0] = mouse_x + gate.offset_x
                    gate.position[1] = mouse_y + gate.offset_y

            if not dragging and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for gate in gates:
                    mouse_x, mouse_y = event.pos
                    gate.drag = True
                    gate.offset_x = gate.position[0] - mouse_x
                    gate.offset_y = gate.position[1] - mouse_y
        
        if event.type == pygame.MOUSEBUTTONUP and event.button == 3 and drawing:
            drawing = False
            drawingfrompoint = False
            


    # RENDER

    screen.fill(backgroundColour)

    for gate in gates[::-1]+inventoryGates:
        # SHADOW
        pygame.draw.circle(screen, gateShadowColour, gate.position, gateSize+2)
        pygame.draw.circle(screen, gateShadowColour, [value + 3 for value in gate.position], gateSize)

        # MAIN
        pygame.draw.circle(screen, gateColour, gate.position, gateSize)
        
        # IMAGE
        image = gateImages[gate.gateType]
        imageLocation = [value - gateSize/2 for value in gate.position]
        imageLocation[0] -= 15 # X ADJUSTMENT
        imageLocation[1] += 5 # Y ADJUSTMENT
        screen.blit(image, imageLocation)

        # INPUTS
        for InputID, Input in gate.inputs.items():
            angle = radians(Input["angle"])
            location = [(gateSize * cos(angle))+gate.position[0], (gateSize * sin(angle))+gate.position[1]]
            pygame.draw.circle(screen, portBorderColour, location, portSize+2)
            pygame.draw.circle(screen, portColour, location, portSize)
        
        # OUTPUT
        location = [(gateSize * cos(0))+gate.position[0], (gateSize * sin(0))+gate.position[1]]
        pygame.draw.circle(screen, portBorderColour, location, portSize+2)
        pygame.draw.circle(screen, portColour, location, portSize)

    if drawingfrompoint:
        gate = [gate for gate in gates if gate.id == drawingfrompoint["gateID"]][0]
        angle = radians(gate.inputs[drawingfrompoint["inputID"]]["angle"] if drawingfrompoint["inputID"] else 0)
        location = [(gateSize * cos(angle))+gate.position[0], (gateSize * sin(angle))+gate.position[1]]

        pygame.draw.line(screen, (255,255,255), location, pygame.mouse.get_pos())

    # WIRES
    for wireInput,wireOutput in wires.items():
            wireInputLoaded = loads(wireInput)
            pygame.draw.line(screen, wireOnColour if [gate for gate in gates if gate.id == wireOutput["gateID"]][0].output == True else wireOffColour,
            gateIOLocations[wireInputLoaded["gateID"]]["inputs"][wireInputLoaded["inputID"]],
            gateIOLocations[wireOutput["gateID"]]["output"]
        )

    # BIN
    screen.blit(binImage, (0, pygame.display.get_surface().get_size()[1]-105))
    
    #FPS COUNT
    if displayFPS: screen.blit(font.render(f'FPS: {round(fps)}', False, (255, 255, 255)),(0,0))

    pygame.display.flip()

    clock.tick(FPS)

pygame.quit()
