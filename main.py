import math
from mpi4py import MPI

class Earth:
    attackPower = 2
    maxHealth = 18
    healingRate = 3
    attackPattern = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    damageReduction = 0.5
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 18
        self.attacking = 0
        
    def attack(self, grid):
        target_positions = []
        for direction in self.attackPattern:
            new_y = self.y + direction[0]
            new_x = self.x + direction[1]
            if new_y < N and new_y >= 0 and new_x < N and new_x >= 0 and grid[new_y][new_x] != ".":
                target_positions.append((new_y, new_x, self.attackPower))
        return target_positions
        
class Fire:
    maxAttackPower = 6
    maxHealth = 12
    healingRate = 1
    attackPattern = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 12
        self.attack = 4
        self.attacking = 0
        
        
        
class Water:
    attack = 3
    maxHealth = 14
    healingRate = 2
    attackPattern = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 14
        self.attacking = 0
    
    def flood():
        pass
        
        
class Air:
    attack = 2
    maxHealth = 10
    healingRate = 2
    attackAndMovePattern = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 10
        self.attacking = 0
    
    def move(self, grid):
        current_nearby_units = self.count_nearby_units(grid, self.y, self.x)
        next_y = self.y
        next_x = self.x
        for direction in self.attackAndMovePattern:
            new_y = self.y + direction[0]
            new_x = self.x + direction[1]
            if new_y < N and new_y >= 0 and new_x < N and new_x >= 0:
                new_nearby_units = self.count_nearby_units(grid, new_y, new_x)
                if new_nearby_units > current_nearby_units:
                    current_nearby_units = new_nearby_units
                    next_y = new_y
                    next_x = new_x
                if new_nearby_units == current_nearby_units:
                    if new_y < next_y:
                        next_y = new_y
                        next_x = new_x
                    # elif new_x < next_x:
                    #     next_y = new_y
                    #     next_x = new_x
        return next_y, next_x
                    
    def count_nearby_units(self, grid, y, x):
        num_units = 0
        for direction in self.attackAndMovePattern:
            new_y = y + direction[0]
            new_x = x + direction[1]
            if new_y < N and new_y >= 0 and new_x < N and new_x >= 0 and grid[new_y][new_x] != "." and not isinstance(grid[new_y][new_x], Air):
                num_units += 1
        return num_units
    
    
# Read a wave from the file and update the grid
def read_wave(file, grid):
    line = file.readline()
    for _ in range(4):
        line = file.readline()
        positions = line.split(":")[1].split(",")
        for position in positions:
            y = int(position[1])
            x = int(position[3])
            if line[0] == 'E':
                if grid[y][x] != ".":
                    print("Error: Earth on Earth")
                else:
                    grid[y][x] = (Earth(x, y))
            elif line[0] == 'F':
                if grid[y][x] != ".":
                    print("Error: Fire on Fire")
                else:
                    grid[y][x] = (Fire(x, y))
            elif line[0] == 'W':
                if grid[y][x] != ".":
                    print("Error: Water on Water")
                else:
                    grid[y][x] = (Water(x, y))
            elif line[0] == 'A':
                if grid[y][x] != ".":
                    print("Error: Air on Air")
                else:
                    grid[y][x] = (Air(x, y))        
        
def print_grid(grid):
    for y in range(len(grid)):
        for x in range(len(grid[y])):
            if grid[y][x] != ".":
                print(grid[y][x].y, grid[y][x].x, grid[y][x].health, y, x)

# Read the parameters from the file
file = open("input1.txt")
parameters = file.readline().split()
N = int(parameters[0]) # Grid Size
W = int(parameters[1]) # Number of Waves
T = int(parameters[2]) # Number of units per faction per wave
R = int(parameters[3]) # Number of rounds per wave

# Reading the grid
grid = [["." for i in range(N)] for j in range(N)]
    
# # read as many waves as there are
# for _ in range(W):

read_wave(file, grid)
# print_grid(grid)


# Initialize MPI
comm = MPI.COMM_WORLD

rank = comm.Get_rank()

num_workers = comm.Get_size() - 1

size_per_rank = int(N // math.sqrt(num_workers))

# stores working partitions assigned to each worker. {{start_index_y, start_index_x, offset}, ...}
worker_partitions = {}

workers_per_row = int(math.sqrt(num_workers))
# Checkered partitioning
if rank == 0:
    for worker_rank in range(1, num_workers + 1):
        start_index_y = size_per_rank * ((worker_rank - 1) // workers_per_row)
        start_index_x = size_per_rank * ((worker_rank - 1) % workers_per_row)
        offset = size_per_rank
        worker_partition = (start_index_y, start_index_x, offset)
        worker_partitions[worker_rank] = worker_partition
        
        # send each partition to the corresponding worker
        comm.send(worker_partition, dest=worker_rank)
else:
    worker_partition = comm.recv(source=0)

comm.Barrier()

# Movement phase
if rank != 0:
    start_index_y, start_index_x, offset = worker_partition
    for y in range(start_index_y, start_index_y + offset):
        for x in range(start_index_x, start_index_x + offset):
            if isinstance(grid[y][x], Air):
                new_y, new_x = grid[y][x].move(grid)
                if new_y < start_index_y + offset and new_y >= start_index_y and new_x < start_index_x + offset and new_x >= start_index_x:
                    if grid[new_y][new_x] == ".":
                        print("Air is moving to", new_y, new_x)
                        grid[y][x].y = new_y
                        grid[y][x].x = new_x
                        grid[new_y][new_x] = grid[y][x]
                        grid[y][x] = "."
                    else:
                        print("Air is merging at ", new_y, new_x)
                        grid[new_y][new_x].health = min(grid[new_y][new_x].health + grid[y][x].health, 10)
                        grid[new_y][new_x].attack += grid[y][x].attack
                        grid[y][x] = "."
                else:
                    pass
                    # comm.send(next_position, dest=0)
                print_grid(grid)

comm.Barrier()            
# Attack phase
attackQueue = []
if rank != 0:
    start_index_y, start_index_x, offset = worker_partition
    unitAttackQueue = []
    for y in range(start_index_y, start_index_y + offset):
        for x in range(start_index_x, start_index_x + offset):
            if grid[y][x] != "." and isinstance(grid[y][x], Earth):
                if grid[y][x].health < grid[y][x].maxHealth / 2:
                    grid[y][x].attacking = 0
                    print("Earth is healing")
                else:
                    print("Earth is attacking")
                    grid[y][x].attacking = 1
                    unitAttackQueue += grid[y][x].attack(grid)
    comm.send(unitAttackQueue, dest=0)
else:
    attackQueue += comm.recv(source=1)
    print(attackQueue)

file.close()