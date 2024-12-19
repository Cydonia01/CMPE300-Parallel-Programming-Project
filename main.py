import math
from mpi4py import MPI

class Unit:
    def __init__(self, x, y, unitName):
        self.x = x
        self.y = y
        self.healing = 0
        self.unitName = unitName     
           
    def attack(self, grid):
        pass
    
    def applyDamage(self, damage):
        pass
    
    def heal(self):
        pass

class Earth:
    # Constants
    attackPower = 2
    maxHealth = 18
    healingRate = 3
    damageReduction = 0.5
    attackPattern = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    
    def __init__(self, x, y, unitName):
        super().__init__(x, y, unitName)
        self.health = 18
        
    def attack(self, grid):
        target_positions = []
        for direction in self.attackPattern:
            target_y = self.y + direction[0]
            target_x = self.x + direction[1]
            if target_y < N and target_y >= 0 and target_x < N and target_x >= 0 and grid[target_y][target_x] != "." and not isinstance(grid[target_y][target_x], Earth):
                target_positions.append((self.y, self.x, target_y, target_x, self.attackPower, "Earth"))
        return target_positions
    
    def applyDamage(self, damage):
        self.health -= int(damage * self.damageReduction)
        
    def heal(self):
        self.health = min(self.health + self.healingRate, self.maxHealth)
        self.healing = 0
                
        
class Fire:
    maxAttackPower = 6
    maxHealth = 12
    healingRate = 1
    attackPattern = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 12
        self.attackPower = 4
        self.healing = 0
        
    def attack(self, grid):
        target_positions = []
        for direction in self.attackPattern:
            target_y = self.y + direction[0]
            target_x = self.x + direction[1]
            if target_y < N and target_y >= 0 and target_x < N and target_x >= 0 and grid[target_y][target_x] != "." and not isinstance(grid[target_y][target_x], Fire):
                target_positions.append((self.y, self.x, target_y, target_x, self.attackPower, "Fire"))
        return target_positions
        
    def increaseAttack(self):
        self.attackPower = min(self.attackPower + 1, self.maxAttackPower)
        
    def resetAttack(self):
        self.attackPower = 4
        
    def applyDamage(self, damage):
        self.health -= damage
        
    def heal(self):
        self.health = min(self.health + self.healingRate, self.maxHealth)
        self.healing = 0
        
class Water:
    attackPower = 3
    maxHealth = 14
    healingRate = 2
    attackPattern = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    adjacentCells = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, -1)]
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 14
        self.healing = 0
    
    def flood(self):
        for direction in self.adjacentCells:
            target_y = self.y + direction[0]
            target_x = self.x + direction[1]
            if target_y < N and target_y >= 0 and target_x < N and target_x >= 0:
                if grid[target_y][target_x] == ".":
                    grid[target_y][target_x] = Water(target_x, target_y)
                    break

    def attack(self, grid):
        target_positions = []
        for direction in self.attackPattern:
            target_y = self.y + direction[0]
            target_x = self.x + direction[1]
            if target_y < N and target_y >= 0 and target_x < N and target_x >= 0 and grid[target_y][target_x] != "." and not isinstance(grid[target_y][target_x], Water):
                target_positions.append((self.y, self.x,target_y, target_x, self.attackPower, "Water"))
        return target_positions
    
    def applyDamage(self, damage):
        self.health -= damage
    
    def heal(self):
        self.health = min(self.health + self.healingRate, self.maxHealth)
        self.healing = 0
        
class Air:
    attackPower = 2
    maxHealth = 10
    healingRate = 2
    attackAndMovePattern = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 10
        self.healing = 0
    
    def attack(self, grid):
        target_positions = []
        for direction in self.attackAndMovePattern:
            target_y = self.y + direction[0]
            target_x = self.x + direction[1]
            while target_y < N and target_y >= 0 and target_x < N and target_x >= 0:
                if grid[target_y][target_x] == ".":
                    target_y += direction[0]
                    target_x += direction[1]
                else:
                    if not isinstance(grid[target_y][target_x], Air):
                        target_positions.append((self.y, self.x, target_y, target_x, self.attackPower, "Air"))
                    break

        return target_positions
    
    def move(self, grid):
        current_nearby_units = self.count_attackable_units(grid, self.y, self.x)
        new_positions = [(self.y, self.x)]
        for direction in self.attackAndMovePattern:
            new_y = self.y + direction[0]
            new_x = self.x + direction[1]
            if new_y < N and new_y >= 0 and new_x < N and new_x >= 0:
                new_nearby_units = self.count_attackable_units(grid, new_y, new_x)
                if new_nearby_units > current_nearby_units:
                    new_positions.append((new_y, new_x))
        
        sorted_new_positions = sorted(new_positions, key=lambda pos: (pos[0], pos[1]))
        next_y = sorted_new_positions[0][0]
        next_x = sorted_new_positions[0][1]
        return next_y, next_x
                    
    def count_attackable_units(self, grid, y, x):
        num_units = 0
        for direction in self.attackAndMovePattern:
            new_y = y + direction[0]
            new_x = x + direction[1]
            while new_y < N and new_y >= 0 and new_x < N and new_x >= 0:
                if grid[new_y][new_x] == ".":
                    new_y += direction[0]
                    new_x += direction[1]
                else:
                    if not isinstance(grid[new_y][new_x], Air):
                        num_units += 1
                    break
        return num_units
    
    def applyDamage(self, damage):
        self.health -= damage
    
    def heal(self):
        self.health = min(self.health + self.healingRate, self.maxHealth)
        self.healing = 0
        
    
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
                # print(grid[y][x].health, end=" ")
                if isinstance(grid[y][x], Earth):
                    print("E", end=" ")
                elif isinstance(grid[y][x], Fire):
                    print("F", end=" ")
                elif isinstance(grid[y][x], Water):
                    print("W", end=" ")
                elif isinstance(grid[y][x], Air):
                    print("A", end=" ")
            else:
                print(".", end=" ")
        print()
        
        
def send_sub_grid():
    sub_grid = []
    for y in range(start_index_y, start_index_y + offset):
        sub_grid.append(grid[y][start_index_x:start_index_x + offset])
    comm.send(sub_grid, dest=0)
        
        
def recv_sub_grids(grid):
    for worker_rank in range(1, num_workers + 1):
        sub_grid = comm.recv(source=worker_rank)
        start_index_y, start_index_x, offset = worker_partitions[worker_rank]
        for y in range(start_index_y, start_index_y + offset):
            for x in range(start_index_x, start_index_x + offset):
                grid[y][x] = sub_grid[y - start_index_y][x - start_index_x]


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



# Initialize MPI
comm = MPI.COMM_WORLD

rank = comm.Get_rank()

num_workers = comm.Get_size() - 1

size_per_rank = int(N // math.sqrt(num_workers))

# stores working partitions assigned to each worker. {{start_index_y, start_index_x, offset}, ...}
worker_partitions = {}

workers_per_row = int(math.sqrt(num_workers))

for _ in range(1):
    read_wave(file, grid)
    # Checkered partitioning
    for _ in range(4):
        if rank == 0:
            print_grid(grid)
            print()
            print()
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
                            if new_y == y and new_x == x:
                                pass
                            elif grid[new_y][new_x] == ".":
                                # print("Air is moving to", new_y, new_x)
                                grid[y][x].y = new_y
                                grid[y][x].x = new_x
                                grid[new_y][new_x] = grid[y][x]
                                grid[y][x] = "."
                            elif isinstance(grid[new_y][new_x], Air):
                                # print("Air is merging at ", new_y, new_x)
                                grid[new_y][new_x].health = min(grid[new_y][new_x].health + grid[y][x].health, 10)
                                grid[new_y][new_x].attackPower += grid[y][x].attackPower
                                grid[y][x] = "."
                        else:
                            pass
                            # comm.send(next_position, dest=0)
            
            send_sub_grid()
        else:
            recv_sub_grids(grid)
            
        comm.Barrier()
    
        # Attack phase
        attackQueue = []

        if rank == 0:
            for worker_rank in range(1, num_workers + 1):
                comm.send(grid, dest=worker_rank)

                attackQueue += comm.recv(source=worker_rank)
        else:
            grid = comm.recv(source=0)

            start_index_y, start_index_x, offset = worker_partition
            unitAttackQueue = []
            for y in range(start_index_y, start_index_y + offset):
                for x in range(start_index_x, start_index_x + offset):
                    if grid[y][x] != ".":
                        unit = grid[y][x]
                        if unit.health < unit.maxHealth / 2:
                            unit.healing = 1
                        else:
                            unitAttackQueue += unit.attack(grid)
            comm.send(unitAttackQueue, dest=0)

        comm.Barrier()

        # Resolution phase
        if rank == 0:
            for worker_rank in range(1, num_workers + 1):
                workerAttackQueue = []
                for attack in attackQueue:
                    dest_y, dest_x = attack[2], attack[3]
                    worker_y = worker_partitions[worker_rank][0]
                    worker_x = worker_partitions[worker_rank][1]
                    
                    # check if the damage is within the worker's partition and send the data accordingly
                    if dest_y >= worker_y and dest_y < worker_y + worker_partitions[worker_rank][2] and dest_x >= worker_x and dest_x < worker_x + worker_partitions[worker_rank][2]:
                        workerAttackQueue.append(attack)
                comm.send(workerAttackQueue, dest=worker_rank)
            
            
            recv_sub_grids(grid)
        else:
            workerAttackQueue = comm.recv(source=0)
            while len(workerAttackQueue) > 0:
                attack_instance = workerAttackQueue.pop(0)
                source_y, source_x, dest_y, dest_x, damage, attacker = attack_instance
                attacker_unit = grid[source_y][source_x]
                attacked_unit = grid[dest_y][dest_x]
                if attacked_unit != ".":
                    attacked_unit.applyDamage(damage)
                if attacker_unit == "Fire" and attacked_unit.health <= 0:
                    attacker_unit.increaseAttack()
                if attacked_unit != "." and attacked_unit.health <= 0:
                    grid[dest_y][dest_x] = "."
            send_sub_grid()
            
        comm.Barrier()

        if rank == 0:
            for worker_rank in range(1, num_workers + 1):
                comm.send(grid, dest=worker_rank)
            recv_sub_grids(grid)
        else:
            grid = comm.recv(source=0)
            start_index_y, start_index_x, offset = worker_partition
            for y in range(start_index_y, start_index_y + offset):
                for x in range(start_index_x, start_index_x + offset):
                    if grid[y][x] != ".":
                        unit = grid[y][x]
                        if unit.healing == 1:
                            unit.heal()
            
            send_sub_grid()

        comm.Barrier()

    # end phase
    if rank == 0:
        print("Wave completed")
        for y in range(N):
            for x in range(N):
                if isinstance(grid[y][x], Fire):
                    grid[y][x].resetAttack()
                if isinstance(grid[y][x], Water):
                    grid[y][x].flood()
                    
        for worker_rank in range(1, num_workers + 1):
            comm.send(grid, dest=worker_rank)
        print_grid(grid)
        print()
    else:
        grid = comm.recv(source=0)
        
    comm.Barrier()
file.close()