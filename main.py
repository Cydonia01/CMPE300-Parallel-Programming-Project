import math
from mpi4py import MPI

# superclass for all units
class Unit:
    def __init__(self, x, y, unitName):
        self.x = x
        self.y = y
        self.healing = 0
        self.unitName = unitName
           
    def attack(self, grid):
        target_positions = []
        
        for direction in self.attackPattern:
            target_y = self.y + direction[0]
            target_x = self.x + direction[1]
            
            if target_y < N and target_y >= 0 and target_x < N and target_x >= 0 and grid[target_y][target_x] != "." and not isinstance(grid[target_y][target_x], type(self)):
                target_positions.append((self.y, self.x, target_y, target_x, self.attackPower, self.unitName))
                
        return target_positions
    
    def applyDamage(self, damage):
        self.health -= damage
    
    def heal(self):
        self.health = min(self.health + self.healingRate, self.maxHealth)
        self.healing = 0

class Earth(Unit):
    # constants
    attackPower = 2
    maxHealth = 18
    healingRate = 3
    damageReduction = 0.5
    attackPattern = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    
    def __init__(self, x, y, unitName):
        super().__init__(x, y, unitName)
        self.health = 18
        
    def applyDamage(self, damage):
        self.health -= int(damage * self.damageReduction)
        
        
class Fire(Unit):
    # constants
    maxAttackPower = 6
    maxHealth = 12
    healingRate = 1
    attackPattern = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    
    def __init__(self, x, y, unitName):
        super().__init__(x, y, unitName)
        self.health = 12
        self.attackPower = 4
        
    def increaseAttack(self):
        self.attackPower = min(self.attackPower + 1, self.maxAttackPower)
        
    def resetAttack(self):
        self.attackPower = 4
    
        
class Water(Unit):
    # constants
    attackPower = 3
    maxHealth = 14
    healingRate = 2
    attackPattern = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    adjacentCells = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, -1)]
    
    def __init__(self, x, y, unitName):
        super().__init__(x, y, unitName)
        self.health = 14
    
    def flood(self):
        for direction in self.adjacentCells:
            target_y = self.y + direction[0]
            target_x = self.x + direction[1]
            if target_y < N and target_y >= 0 and target_x < N and target_x >= 0:
                if grid[target_y][target_x] == ".":
                    grid[target_y][target_x] = Water(target_x, target_y, "Water")
                    break
        
class Air(Unit):
    # constants
    attackPower = 2
    maxHealth = 10
    healingRate = 2
    attackAndMovePattern = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]
    
    def __init__(self, x, y, unitName):
        super().__init__(x, y, unitName)
        self.health = 10
    
    
    # returns the coordinates of the units that can be attacked. Also, it is used for counting the number of attackable units
    def attack(self, grid):
        target_positions = []
        for direction in self.attackAndMovePattern:
            target_y = self.y + direction[0]
            target_x = self.x + direction[1]
            for _ in range(2):
                if target_y < N and target_y >= 0 and target_x < N and target_x >= 0:
                    if grid[target_y][target_x] == ".":
                        target_y += direction[0]
                        target_x += direction[1]
                    elif not isinstance(grid[target_y][target_x], Air):
                        target_positions.append((self.y, self.x, target_y, target_x, self.attackPower, "Air"))
                        break

        return target_positions
    
    def move(self, worker_grid, neighbor_grids):
        current_nearby_units = self.count_attackable_units(worker_grid, neighbor_grids, self.y, self.x)
        new_positions = [(current_nearby_units, self.y, self.x)]
        
        for direction in self.attackAndMovePattern:
            new_y = self.y + direction[0]
            new_x = self.x + direction[1]
            print("direction y, x", direction[0], direction[1])
            if new_y < offset and new_y >= 0 and new_x < offset and new_x >= 0 :
                if worker_grid[new_y][new_x] == ".":
                    new_nearby_units = self.count_attackable_units(worker_grid, neighbor_grids, new_y, new_x)
                    if new_nearby_units > current_nearby_units:
                        new_positions.append((new_nearby_units, new_y, new_x))
                    
            else:
                glob_new_y = new_y + glob_index_y
                glob_new_x = new_x + glob_index_x
                if glob_new_y < N and glob_new_y >= 0 and glob_new_x < N and glob_new_x >= 0:
                    new_nearby_units = self.count_attackable_units(worker_grid, neighbor_grids, glob_new_y, glob_new_x)
                    if new_nearby_units > current_nearby_units:
                        new_positions.append((new_nearby_units, new_y, new_x))
        
        sorted_new_positions = sorted(new_positions, key=lambda pos: (-pos[0], pos[1], pos[2]))
        next_y = sorted_new_positions[0][1]
        next_x = sorted_new_positions[0][2]
        print(sorted_new_positions)
        return next_y, next_x

    def count_attackable_units(self, worker_grid, neighbor_grids, y, x):
        num_units = 0
        print("y, x", y, x)
        for direction in self.attackAndMovePattern:
            new_y = y + direction[0]
            new_x = x + direction[1]
            print("new y, x", new_y, new_x)
            for _ in range(2):
                if new_y < offset and new_y >= 0 and new_x < offset and new_x >= 0:
                    if worker_grid[new_y][new_x] == ".":
                        new_y += direction[0]
                        new_x += direction[1]
                        
                    elif not isinstance(worker_grid[new_y][new_x], Air):
                        num_units += 1
                        break
                elif new_y < N and new_y >= 0 and new_x < N and new_x >= 0:
                    worker = None
                    
                    for worker_num in worker_partitions:
                        worker_start_y, worker_start_x, worker_offset = worker_partitions[worker_num]
                        if new_y >= worker_start_y and new_y < worker_start_y + worker_offset and new_x >= worker_start_x and new_x < worker_start_x + worker_offset:
                            worker = worker_num
                            
                    neighbor_start_y, neighbor_start_x, neighbor_offset = worker_partitions[worker]
                    
                    if rank == worker:
                        neighbor_grid = worker_grid
                    else:
                        neighbor_grid = neighbor_grids[worker]
                    
                    local_y = new_y - neighbor_start_y
                    local_x = new_x - neighbor_start_x
                    
                    if neighbor_grid[local_y][local_x] == ".":
                        new_y += direction[0]
                        new_x += direction[1]
                    elif not isinstance(neighbor_grid[local_y][local_x], Air):
                        num_units += 1
                        break
        return num_units

    
# Read a wave from the file and update the grid
#!!! clean at the end!!!
def read_wave(file):
    line = file.readline()
    unit_data = []
    for _ in range(4):
        line = file.readline()
        positions = line.split(":")[1].split(",")
        for position in positions:
            y = int(position[1])
            x = int(position[3])
            unit_data.append((line[0], y, x))
    return unit_data    
        
def print_grid(grid):
    for y in range(len(grid)):
        for x in range(len(grid[y])):
            if grid[y][x] != ".":
                print(grid[y][x].health, end=" ")
                continue
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
        start_index_x, start_index_y, offset = worker_partitions[worker_rank]
        for y in range(start_index_y, start_index_y + offset):
            for x in range(start_index_x, start_index_x + offset):
                grid[y][x] = sub_grid[y - start_index_y][x - start_index_x]

def send_grid_to_neighbor(worker_grid):
    neighbors = []
    current_worker = rank
    for neighbor_worker, neighbor_partition in worker_partitions.items():
        current_worker_y, current_worker_x, offset = worker_partitions[current_worker]
        neighbor_y, neighbor_x, neighbor_offset = neighbor_partition
        if abs(neighbor_y - current_worker_y) == offset or abs(neighbor_x - current_worker_x) == offset:
            neighbors.append(neighbor_worker)
    return neighbors

# Read the parameters from the file
file = open("input1.txt")
parameters = file.readline().split()
N = int(parameters[0]) # Grid Size
W = int(parameters[1]) # Number of Waves
T = int(parameters[2]) # Number of units per faction per wave
R = int(parameters[3]) # Number of rounds per wave

# Initialize MPI
comm = MPI.COMM_WORLD

rank = comm.Get_rank()

num_workers = comm.Get_size() - 1

size_per_rank = int(N // math.sqrt(num_workers))

# stores working partitions assigned to each worker. {{start_index_y, start_index_x, offset}, ...}
worker_partitions = {}
workers_per_row = int(math.sqrt(num_workers))

# checkered partitioning
if rank == 0:
    grid = [["." for _ in range(N)] for _ in range(N)]
    
    for worker_rank in range(1, num_workers + 1):
        start_index_y = size_per_rank * ((worker_rank - 1) // int(math.sqrt(num_workers)))
        start_index_x = size_per_rank * ((worker_rank - 1) % int(math.sqrt(num_workers)))
        offset = size_per_rank
        worker_partition = (start_index_y, start_index_x, offset)
        worker_partitions[worker_rank] = worker_partition
        
        worker_grid = [["." for _ in range(size_per_rank)] for _ in range(size_per_rank)]
        
        comm.send(worker_grid, dest=worker_rank, tag=1)
        
        global_indexes = (start_index_y, start_index_x, offset)
        
        comm.send(global_indexes, dest=worker_rank, tag=2)
    
    
    for worker_rank in range(1, num_workers + 1):
        comm.send(worker_partitions, dest=worker_rank, tag=3)
    
else:
    worker_grid = comm.recv(source=0, tag=1)
    global_indexes = comm.recv(source=0, tag=2)
    worker_partitions = comm.recv(source=0, tag=3)
    glob_index_y, glob_index_x, offset = global_indexes
    # print("rank", rank, "received", worker_partitions, worker_grid, global_indexes)
      
for _ in range(1):
    if rank == 0:
        unit_data = read_wave(file)

        for worker, partition in worker_partitions.items():
            worker_y, worker_x, offset = partition
            worker_unit_partition = []
    
            for unit in unit_data:
                unit_type, y, x = unit
                if y >= worker_y and y < worker_y + offset and x >= worker_x and x < worker_x + offset:
                    worker_unit_partition.append((unit_type, y, x))
            comm.send(worker_unit_partition, dest=worker, tag=4)
    else:
        unit_data = comm.recv(source=0, tag=4)
        
        # print("Rank", rank, "received", unit_data)
        
    comm.Barrier()
    
    # place the units on the grid
    if rank != 0:
        for unit in unit_data:
            unit_type, y, x = unit
            local_y = y - glob_index_y
            local_x = x - glob_index_x
            if worker_grid[local_y][local_x] == ".":
                if unit_type == "E":
                    worker_grid[local_y][local_x] = Earth(local_x, local_y, "Earth")
                elif unit_type == "F":
                    worker_grid[local_y][local_x] = Fire(local_x, local_y, "Fire")
                elif unit_type == "W":
                    worker_grid[local_y][local_x] = Water(local_x, local_y, "Water")
                elif unit_type == "A":
                    worker_grid[local_y][local_x] = Air(local_x, local_y, "Air")
                
        # print("Rank", rank, "updated grid")
        # print_grid(worker_grid)
    
    comm.Barrier()

    #!! 4 olacak!!
    for _ in range(1):
        # Movement phase
        if rank != 0:
            # print("rank", rank, "global indexes", glob_index_y, glob_index_x, offset)
            
            current_worker_neighbor = send_grid_to_neighbor(worker_grid)
            neighbor_grids = {}
            
            for neighbor in current_worker_neighbor:
                comm.send(worker_grid, dest=neighbor)
                neighbor_grids[neighbor] = (comm.recv(source=neighbor)) 
                               
            # print("Rank", rank, "received neighbor grids")
            
            # for neighbor in neighbor_grids:
            #     print("rank ", rank, "neighbor grid", neighbor)
            #     print_grid(neighbor_grids[neighbor])
            # print("Rank", rank, "neighbors", current_worker_neighbor)
            movements = []
            for y in range(offset):
                for x in range(offset):
                    if isinstance(worker_grid[y][x], Air):
                        air_unit = worker_grid[y][x]
                        new_y, new_x = air_unit.move(worker_grid, neighbor_grids)
                        movements.append((y, x, new_y, new_x))
                
                # for movement in movements:
                #     y, x, new_y, new_x = movement
                #     if new_y < offset and new_y >= 0 and new_x < offset and new_x >= 0:
                #         next_pos = worker_grid[new_y][new_x]
                        
                #         if new_y == y and new_x == x:
                #             pass
                        
                #         elif next_pos == ".":
                #             print("Air is moving to", new_y, new_x)
                #             air_unit.y = new_y
                #             air_unit.x = new_x
                #             worker_grid[new_y][new_x] = air_unit
                #             worker_grid[y][x] = "."
                        
                #         elif isinstance(next_pos, Air):
                #             print("Air is merging at ", new_y, new_x)
                #             next_pos.health = min(next_pos.health + air_unit.health, 10)
                #             next_pos.attackPower += air_unit.attackPower
                #             worker_grid[y][x] = "."
                #     else:
                #         glob_new_y = new_y + glob_index_y
            # print("Rank", rank, "movements", movements)
            # print_grid(worker_grid)
        #     send_sub_grid()
        # else:
        #     recv_sub_grids(grid)
            
    comm.Barrier()
    
    #     # Attack phase
    #     attackQueue = []

    #     if rank == 0:
    #         for worker_rank in range(1, num_workers + 1):
    #             comm.send(grid, dest=worker_rank)

    #             attackQueue += comm.recv(source=worker_rank)
    #     else:
    #         grid = comm.recv(source=0)

    #         unitAttackQueue = []
    #         for y in range(start_index_y, start_index_y + offset):
    #             for x in range(start_index_x, start_index_x + offset):
    #                 if grid[y][x] != ".":
    #                     unit = grid[y][x]
    #                     temp = unit.attack(grid)
                        
    #                     if unit.health < unit.maxHealth / 2:
    #                         unit.healing = 1
    #                     elif len(temp) == 0:
    #                         unit.healing = 1
    #                     else:
    #                         unitAttackQueue += temp
    #         comm.send(unitAttackQueue, dest=0)

    #     comm.Barrier()

    #     # Resolution phase
    #     if rank == 0:
    #         for worker_rank in range(1, num_workers + 1):
    #             workerAttackQueue = []
    #             for attack in attackQueue:
    #                 dest_y, dest_x = attack[2], attack[3]
    #                 worker_y = worker_partitions[worker_rank][0]
    #                 worker_x = worker_partitions[worker_rank][1]
                    
    #                 # check if the damage is within the worker's partition and send the data accordingly
    #                 if dest_y >= worker_y and dest_y < worker_y + worker_partitions[worker_rank][2] and dest_x >= worker_x and dest_x < worker_x + worker_partitions[worker_rank][2]:
    #                     workerAttackQueue.append(attack)
    #             comm.send(workerAttackQueue, dest=worker_rank)
            
    #         recv_sub_grids(grid)
    #     else:
    #         workerAttackQueue = comm.recv(source=0)
            
    #         for attack_instance in workerAttackQueue:
    #             source_y, source_x, dest_y, dest_x, damage, attacker = attack_instance
    #             attacked_unit = grid[dest_y][dest_x]
    #             attacked_unit.applyDamage(damage)
            
    #         for attack_instance in workerAttackQueue:
    #             source_y, source_x, dest_y, dest_x, damage, attacker = attack_instance
    #             attacked_unit = grid[dest_y][dest_x]
    #             attacker_unit = grid[source_y][source_x]                
    #             if grid[dest_y][dest_x] != "." and attacked_unit.health <= 0:
    #                 grid[dest_y][dest_x] = "."
    #                 if isinstance(attacker_unit, Fire):
    #                     attacker_unit.increaseAttack()
                
    #         send_sub_grid()
            
    #     comm.Barrier()


    #     # healing phase
    #     if rank == 0:
    #         for worker_rank in range(1, num_workers + 1):
    #             comm.send(grid, dest=worker_rank)
                
    #         recv_sub_grids(grid)
        
    #     else:
    #         grid = comm.recv(source=0)
            
    #         for y in range(start_index_y, start_index_y + offset):
    #             for x in range(start_index_x, start_index_x + offset):
    #                 if grid[y][x] != ".":
    #                     unit = grid[y][x]
    #                     if unit.healing == 1:
    #                         unit.heal()
            
    #         send_sub_grid()
        

    # comm.Barrier()
    
    # # threadler arası komünikasyon lazım. 4 ten 2 ye geçiyor parentı iptal et.
    # # Wave ending
    # if rank == 0:
    #     print_grid(grid)
    #     for worker_rank in range(1, num_workers + 1):
    #         comm.send(grid, dest=worker_rank)
        
    #     recv_sub_grids(grid)

    # else:
    #     grid = comm.recv(source=0)
    #     for y in range(start_index_y, start_index_y + offset):
    #         for x in range(start_index_x, start_index_x + offset):
    #             if isinstance(grid[y][x], Fire):
    #                 grid[y][x].resetAttack()
    #             if isinstance(grid[y][x], Water):
    #                 grid[y][x].flood()
    #     send_sub_grid()
        
    # comm.Barrier()
    # if rank == 0:
    #     for worker_rank in range(1, num_workers + 1):
    #         comm.send(grid, dest=worker_rank)
    # else:
    #     grid = comm.recv(source=0)
    
    # comm.Barrier()

    
file.close()