from mpi4py import MPI

class Earth:
    attack = 2
    healingRate = 3
    attackPattern = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    damageReduction = 0.5
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 18
        
        
class Fire:
    maxAttack = 6
    healingRate = 1
    attackPattern = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 12
        self.attack = 4
        
        
class Water:
    attack = 3
    healingRate = 2
    attackPattern = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 14
    
    def flood():
        pass
        
        
class Air:
    attack = 2
    healingRate = 2
    attackPattern = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 10
    
    def move():
        pass
        
        
# file = open("input.txt")
# parameters = file.readline().split()
# N = int(parameters[0]) # Grid Size
# W = int(parameters[1]) # Number of Waves
# T = int(parameters[2]) # Number of units per faction per wave
# R = int(parameters[3]) # Number of rounds per wave

# # Reading the grid
# grid = [["." for i in range(N)] for j in range(N)]
# while True:
#     line = file.readline().split(":")
#     if not line:
#         break
#     if line[0] == "Wave 1" or line[0] == "":
#         continue
#     positions = [1].strip().split(",")    
#     for position in positions:
#         x = int(position[0])
#         y = int(position[2])
#         if line[0] == 'E':
#             grid[y][x] = (Earth(x, y))
#         elif line[0] == 'F':
#             grid[y][x] = (Fire(x, y))
#         elif line[0] == 'W':
#             grid[y][x] = (Water(x, y))
#         elif line[0] == 'A':
#             grid[y][x] = (Air(x, y))
    

# Initialize MPI
# comm = MPI.COMM_WORLD
# rank = comm.Get_rank()
# N = 12
# sizePerRank = N // 3
# # Checkered partitioning
# if rank != 0:
#     for x in range(N):
#         for y in range(N):
#             if ((x // sizePerRank) + (y // sizePerRank)) % N == rank:
#                 print("I am rank", rank," looking", y, x) 