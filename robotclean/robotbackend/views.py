from django.shortcuts import render
import random
import copy
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers

GRID_SIZE = 32
VISION_RADIUS = 5

GRID = [["0" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
ROBOT_GRID = [["U" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

ROBOT_TARGETS = {} 

ROBOT_VIEWING = False
TRASH = (GRID_SIZE // 2, GRID_SIZE // 2)

NUM_TURN = 0
NUM_TRASH_COLLECTED = 0

# CODE FOR GRID CELLS :
# ------------------------------------------------------------
# 0 => EMPTY
# U => UNKNOWN
# UL => UNKNOWN CELL LOCKED ( an unknown cell locked by a robot )
# Z => TRASH_CAN
# R => ROBOT ( with no load )
# D => DISPOSABLE_TRASH ( a trash to collect )
# DL => LOCKED TRASH ( a trash locked by a robot )
# RL => LOCKED ROBOT ( a robot with a target )
# RDL => LOCKED ROBOT ON TRASH ( a robot with a trash under )
# ------------------------------------------------------------

class SetupSerializer(serializers.Serializer):
    nr = serializers.IntegerField(min_value=0)
    nd = serializers.IntegerField(min_value=0)
    i  = serializers.IntegerField(min_value=0, max_value=GRID_SIZE-1)
    j  = serializers.IntegerField(min_value=0, max_value=GRID_SIZE-1)


def get_free_pos():
    while True:
        x, y = random.randrange(GRID_SIZE), random.randrange(GRID_SIZE)
        if GRID[x][y] == "0":
            return x, y


class SetupView(APIView):
    # Initialize grid
    def post(self, request):
        global GRID, ROBOT_GRID, ROBOT_TARGETS, TRASH, NUM_TURN, NUM_TRASH_COLLECTED, ROBOT_VIEWING

        # Get 3 info to start number of robots, number of trashes to collect 
        # and trash position (i,j)
        s = SetupSerializer(data=request.data) 
      
        if not s.is_valid():
            return Response(s.errors, status=status.HTTP_400_BAD_REQUEST)

        data = s.validated_data
        nr, nd, i, j = data["nr"], data["nd"], data["i"], data["j"]

        GRID = [["0" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)] # all empty
        ROBOT_GRID = [["U" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)] # all unknown
        TRASH = (i, j)
        GRID[i][j] = "Z" # trash to get rid oj junk
        ROBOT_GRID[i][j] = "Z" # robots know where the trash is
        ROBOT_TARGETS = {}
        NUM_TURN = 0
        NUM_TRASH_COLLECTED = 0
        ROBOT_VIEWING = False

        for _ in range(nr):
            x, y = get_free_pos(); GRID[x][y] = "R" # a robot with no load
        for _ in range(nd):
            x, y = get_free_pos(); GRID[x][y] = "D" # a trash to dispose

        return Response({"message": "OK - starting cleanup", "grid": GRID},
                        status=status.HTTP_201_CREATED)


class GridView(APIView):
    # Switch to full grid view
    def get(self, request):
        global ROBOT_VIEWING
        ROBOT_VIEWING = False
        return Response({"grid": GRID})

class RobotView(APIView):
    # Switch to robot grid view
    def get(self, request):
        global ROBOT_VIEWING
        ROBOT_VIEWING = True
        NextView().updateRobotView()  # force update
        return Response({"grid": ROBOT_GRID})

class NextView(APIView):
    # Return the grid after one MOVE
    def get(self, request):
        global NUM_TURN
        global NUM_TRASH_COLLECTED
        global ROBOT_VIEWING
        if self.moveNext():
            NUM_TURN+=1
        if ROBOT_VIEWING:
            return Response({"grid": ROBOT_GRID, "discovered": self.mapDiscovered(), "cleaned": self.mapCleaned(), "num_it":NUM_TURN, "num_trash":NUM_TRASH_COLLECTED})
        else:
            return Response({"grid": GRID, "discovered": self.mapDiscovered(), "cleaned": self.mapCleaned(), "num_it":NUM_TURN, "num_trash":NUM_TRASH_COLLECTED})
    
    def moveNext(self):
        if self.mapDiscovered() and self.mapCleaned(): # game end
            return False
        self.updateRobotView()
        self.lockCloseTarget()
        self.exploreUnknown()
        self.move()
        self.updateRobotView() # after move
        return True
    
    def updateRobotView(self):
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                if GRID[i][j] == "R" or GRID[i][j] == "RL" or GRID[i][j] == "RDL":
                    for di in range(-VISION_RADIUS, VISION_RADIUS + 1):
                        for dj in range(-VISION_RADIUS, VISION_RADIUS + 1):
                            ni, nj = i + di, j + dj
                            if 0 <= ni < GRID_SIZE and 0 <= nj < GRID_SIZE:
                                ROBOT_GRID[ni][nj] = GRID[ni][nj]

    # Find the closest junk and assign robot
    def lockCloseTarget(self):
        global GRID, ROBOT_GRID, ROBOT_TARGETS
        # Lock a nearby junk
        d_positions = []
        r_positions = []

        # Collect D and R positions
        countAffected = 0
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                # junk or junk + robot (loaded) on it
                if ROBOT_GRID[i][j] == "D":
                    d_positions.append((i, j))
                elif ROBOT_GRID[i][j] == "R":
                    r_positions.append((i, j))
                elif ROBOT_GRID[i][j] == "RL" or ROBOT_GRID[i][j] == "RDL":
                    countAffected = countAffected + 1
        # security : be sure that there is at least one affectation when locked targets
        if countAffected == 0:
            for i in range(GRID_SIZE):
                for j in range(GRID_SIZE):
                    if ROBOT_GRID[i][j] == "DL":
                        d_positions.append((i, j))
                

        for d_i, d_j in d_positions:
            if not r_positions:
                break  # no more robot

            # find closest
            closest_robot = min(
                r_positions,
                key=lambda pos: abs(pos[0] - d_i) + abs(pos[1] - d_j)
            )

            r_i, r_j = closest_robot

            # set new values
            GRID[d_i][d_j] = "DL"
            GRID[r_i][r_j] = "RL"
            ROBOT_GRID[d_i][d_j] = "DL"
            ROBOT_GRID[r_i][r_j] = "RL"
            print("Active : Robot (", r_i, ",", r_j, ") locks junk (", d_i, ",", d_j,")")

            ROBOT_TARGETS[(r_i, r_j)] = (d_i, d_j)  # store destination target of the robot
            # Supprimer le robot de la liste pour qu'il ne soit pas réutilisé
            r_positions.remove(closest_robot)

    # If remaining robots, explore unknown
    def exploreUnknown(self):
        global GRID, ROBOT_GRID, ROBOT_TARGETS
        u_positions = []
        r_positions = []

        # Collect D and R positions
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                if ROBOT_GRID[i][j] == "U":
                    u_positions.append((i, j))
                elif ROBOT_GRID[i][j] == "R":
                    r_positions.append((i, j))

        for r_i, r_j in r_positions:
            if not u_positions:
                # no trash, no position, go anywhere not to stay static
                ROBOT_TARGETS[(r_i, r_j)] = get_free_pos()  # force move anywhere robot is useless
                GRID[r_i][r_j] = "R"
                ROBOT_GRID[r_i][r_j] = "R"
                print("Unactive : Robot (", r_i, ",", r_j, ") has no target.")
                continue  # unknown positions

            # Trouver la case inconnue la plus proche (distance de Manhattan)
            closest_unknown = min(
                u_positions,
                key=lambda pos: abs(pos[0] - r_i) + abs(pos[1] - r_j)
            )

            u_i, u_j = closest_unknown

            # Marquer les deux cases
            GRID[r_i][r_j] = "RL"
            ROBOT_GRID[u_i][u_j] = "UL"
            ROBOT_GRID[r_i][r_j] = "RL"
            print("Active Robot (", r_i, ",", r_j, ") locks unknown (", u_i, ",", u_j,")")

            ROBOT_TARGETS[(r_i, r_j)] = (u_i, u_j)  # store destination target of the robot
            # Supprimer le robot de la liste pour qu'il ne soit pas réutilisé
            u_positions.remove(closest_unknown)

    def move(self):
        # work on a grid copy
        global GRID, NUM_TRASH_COLLECTED
        global ROBOT_TARGETS
        new_grid = copy.deepcopy(GRID)
        new_targets = {} 
        occupied = set()  # keep occupied targets
        left = set()  # keep of released targets (leaving)

        for (r_i, r_j), (d_i, d_j) in ROBOT_TARGETS.items():
            # Vérifie que le robot est toujours présent
            if GRID[r_i][r_j] not in ("R", "RL", "RDL"):
                print("WARNING a Robot (", r_i, ",", r_j, ") should be here !")
                continue

            # Calcul de direction vers la cible
            di = d_i - r_i
            dj = d_j - r_j
            step_i = r_i + (1 if di > 0 else -1 if di < 0 else 0)
            step_j = r_j + (1 if dj > 0 else -1 if dj < 0 else 0)
            # destination ?
            if GRID[d_i][d_j] == "Z" and GRID[step_i][step_j] == "Z" and (step_i == r_i or step_j == r_j):
                # heading to trash, reach the trash, get rid of content
                new_grid[r_i][r_j] = "R"
                NUM_TRASH_COLLECTED += 1
                # to not add target, we have done yet
                print("--> Robot drops junk to trash and is now available (", r_i, ",", r_j, ")")
                continue
            # Vérifie si la case est occupée par un robot ou déjà prise par un autre déplacement
            if self.invalidMove(step_i, r_j, left, occupied):
                step_i =  r_i 
            if self.invalidMove(r_i, step_j, left, occupied):
                step_j =  r_j

            if step_i == r_i and step_j == r_j:
                print("(occupîed) Robot (", r_i, ",", r_j, ") can not move : choose randomly an available move")
                step_i, step_j = self.randomMoveUnblock(r_i, r_j, left, occupied)
                
                if step_i == r_i and step_j == r_j:
                    new_targets[(r_i, r_j)] = (d_i, d_j) 
                    print("(occupîed) Robot (", r_i, ",", r_j, ") can not move at all")
                    continue # can not move at all
            if step_i != r_i and step_j != r_j:
                # if can move horizonal and vertical choose using the bigest distance to cover
                if di > dj:
                    step_i = r_i
                else:
                    step_j = r_j

            # update leaving cell
            if GRID[r_i][r_j] == "RDL":
                new_grid[r_i][r_j] = "D"
            else:
                new_grid[r_i][r_j] = "0"

            # move
            if GRID[step_i][step_j] == "D":
                new_grid[step_i][step_j] = "RDL" 
            elif GRID[r_i][r_j] == "R":
                new_grid[step_i][step_j] = "R" # unaffected
            else:
                new_grid[step_i][step_j] = "RL" 
            # print("--> Robot moves (", r_i, ",", r_j, ") to (", step_i, ",", step_j, ")")
            left.add((r_i, r_j))
            # Marque la case comme occupée
            occupied.add((step_i, step_j))
            ## update ROBOT_TARGETS
            # destination reached ?
            if step_i == d_i and step_j == d_j:
                if GRID[d_i][d_j] == "0" or GRID[d_i][d_j] == "U" or GRID[d_i][d_j] == "UL":
                    print("--> Robot reached unknown and is now available (", step_i, ",", step_j, ")")
                    new_grid[step_i][step_j] = "R"
                else:
                    print("--> Robot reach junk and heading to trash (", r_i, ",", r_j, ") : ",GRID[d_i][d_j])
                    new_targets[(step_i, step_j)] = self.getTrash() 
                    if new_grid[step_i][step_j] == "RDL":
                        new_grid[step_i][step_j] = "RL"
            else:
                new_targets[(step_i, step_j)] = (d_i, d_j)

        trash_pos_i, trash_pos_j = self.getTrash()
        # Restore the trash if pos has been freed
        if (not new_grid[trash_pos_i][trash_pos_j] == 'R'
                and not new_grid[trash_pos_i][trash_pos_j]=='RL'
                and not new_grid[trash_pos_i][trash_pos_j]=='RDL'):
            new_grid[trash_pos_i][trash_pos_j] = "Z"

        GRID = new_grid
        ROBOT_TARGETS = new_targets

    def invalidMove(self, i, j, left, occupied):
        return ((i < 0)
                or (j < 0)
                or (i>= GRID_SIZE)
                or (j >= GRID_SIZE)
                or (GRID[i][j] in ("R", "RL", "RDL")
                    and not (i, j) in left)
                or (i, j) in occupied)

    def getTrash(self):
        global TRASH
        return TRASH
        
    # every cell discovered ?
    def mapDiscovered(self):
        global ROBOT_GRID
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                if ROBOT_GRID[i][j] == "U" or GRID[i][j] == "UL":
                    return False
        print("** Map discovered")
        return True
    
    # every junk cleared
    def mapCleaned(self):
        global GRID, ROBOT_TARGETS
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                if GRID[i][j] == "D" or GRID[i][j] == "DL" or GRID[i][j] == "RDL":
                    #print("** Map not cleaned (", i, ", ", j,") : ", GRID[i][j])
                    return False
        # any one heading to trash ?
        for (i, j), (d_i, d_j) in ROBOT_TARGETS.items():
            if (d_i, d_j) == self.getTrash():
                #print("** Map not cleaned , heading to trash(", i, ", ", j,") : ", GRID[d_i][d_j])
                return False

        print("** Map cleaned")
        return True

    # when block try random move in other direction
    def randomMoveUnblock(self, r_i, r_j, left, occupied):
        max = 10
        while max > 0:
            step_i = r_i + random.randrange(3) -1 # -1, 0 or 1 offset
            step_j = r_j + random.randrange(3) -1
            if self.invalidMove(step_i, r_j, left, occupied):
                step_i =  r_i
            else:
                break 
            if self.invalidMove(r_i, step_j, left, occupied):
                step_j =  r_j 
            else:
                break 
            max = max - 1
        return step_i, step_j