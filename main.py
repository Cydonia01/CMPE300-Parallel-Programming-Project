import math
from mpi4py import MPI

# superclass for all units
class Unit:
    def __init__(self, x, y, unitName):
        self.x = x
        self.y = y
        self.healing = 0
        self.unitName = unitName

    def attack(self, worker_grid, neighbor_grids):
        target_positions = []
        glob_y = self.y + glob_index_y
        glob_x = self.x + glob_index_x

        for direction in self.attackPattern:
            target_y = glob_y + direction[0]
            target_x = glob_x + direction[1]
            cell = self.get_cell(target_y, target_x, worker_partitions, worker_grid, neighbor_grids)

            if cell is None:
                continue
            elif cell == ".":
                continue
            elif not isinstance(cell, self.__class__):
                target_positions.append((glob_y, glob_x, target_y, target_x, self.attackPower, self.unitName))

        return target_positions

    def applyDamage(self, damage):
        self.health -= damage

    def heal(self):
        self.health = min(self.health + self.healingRate, self.maxHealth)
        self.healing = 0

    def get_cell(self, glob_y, glob_x, worker_partitions, worker_grid, neighbor_grid):
        if glob_y < 0 or glob_y >= N or glob_x < 0 or glob_x >= N:
            return None

        for worker, (start_y, start_x, offset) in worker_partitions.items():
            if glob_y >= start_y and glob_y < start_y + offset and glob_x >= start_x and glob_x < start_x + offset:
                local_y = glob_y - start_y
                local_x = glob_x - start_x
                if worker == rank:
                    return worker_grid[local_y][local_x]
                else:
                    return neighbor_grid[worker][local_y][local_x]

        return None


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
        self.damaged = 0

    def applyDamage(self, damage):
        self.health -= int(damage * self.damageReduction)
        damaged = 1


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

    def flood(self, worker_grid, neighbor_grids):
        glob_y = self.y + glob_index_y
        glob_x = self.x + glob_index_x

        for direction in self.adjacentCells:
            target_y = glob_y + direction[0]
            target_x = glob_x + direction[1]
            cell = self.get_cell(target_y, target_x, worker_partitions, worker_grid, neighbor_grids)
            if cell is None:
                continue
            elif cell == ".":
                return (target_y, target_x)
        return None

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
    def attack(self, worker_grid, neighbor_grids):
        target_positions = []
        glob_y = self.y + glob_index_y
        glob_x = self.x + glob_index_x

        for direction in self.attackAndMovePattern:
            target_y = glob_y + direction[0]
            target_x = glob_x + direction[1]

            skipped = 0
            max_skip = 1
            for _ in range(2):
                cell = self.get_cell(target_y, target_x, worker_partitions, worker_grid, neighbor_grids)
                if cell is None:
                    break

                if cell == ".":
                    if skipped < max_skip:
                        skipped += 1
                        target_y += direction[0]
                        target_x += direction[1]
                    else:
                        break
                else:
                    if not isinstance(cell, Air):
                        target_positions.append((glob_y, glob_x, target_y, target_x, self.attackPower, "Air"))
                    break
        return target_positions

    def move(self, worker_grid, neighbor_grids):
        current_glob_y = self.y + glob_index_y
        current_glob_x = self.x + glob_index_x
        current_nearby_units = self.count_attackable_units(worker_grid, neighbor_grids, self.y, self.x)
        new_positions = [(current_nearby_units, self.y, self.x)]

        for direction in self.attackAndMovePattern:
            test_glob_y = current_glob_y + direction[0]
            test_glob_x = current_glob_x + direction[1]

            cell = self.get_cell(test_glob_y, test_glob_x, worker_partitions, worker_grid, neighbor_grids)

            if cell == ".":
                test_y = test_glob_y - glob_index_y
                test_x = test_glob_x - glob_index_x
                new_nearby_units = self.count_attackable_units(worker_grid, neighbor_grids, test_y, test_x)
                if new_nearby_units > current_nearby_units:
                    new_positions.append((new_nearby_units, test_y, test_x))

        sorted_new_positions = sorted(new_positions, key=lambda pos: (-pos[0], pos[1], pos[2]))
        next_y = sorted_new_positions[0][1]
        next_x = sorted_new_positions[0][2]
        return next_y, next_x

    def count_attackable_units(self, worker_grid, neighbor_grids, y, x):
        glob_y = y + glob_index_y
        glob_x = x + glob_index_x

        num_units = 0
        for direction in self.attackAndMovePattern:
            new_y = glob_y + direction[0]
            new_x = glob_x + direction[1]

            skipped = 0
            max_skip = 1
            for _ in range(2):
                cell = self.get_cell(new_y, new_x, worker_partitions, worker_grid, neighbor_grids)
                if cell is None:
                    break

                if cell == ".":
                    if skipped < max_skip:
                        skipped += 1
                        new_y += direction[0]
                        new_x += direction[1]
                    else:
                        break
                else:
                    if not isinstance(cell, Air):
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


def send_sub_grid(worker_grid):
    sub_grid = []
    for y in range(offset):
        sub_grid.append(worker_grid[y])
    comm.send(sub_grid, dest=0)


def recv_sub_grids(grid):
    for worker_rank in range(1, num_workers + 1):
        sub_grid = comm.recv(source=worker_rank)
        start_index_y, start_index_x, offset = worker_partitions[worker_rank]
        for y in range(start_index_y, start_index_y + offset):
            for x in range(start_index_x, start_index_x + offset):
                grid[y][x] = sub_grid[y - start_index_y][x - start_index_x]

def find_neighbors(worker_grid):
    neighbors = []
    current_worker = rank
    for neighbor_worker, neighbor_partition in worker_partitions.items():
        current_worker_y, current_worker_x, offset = worker_partitions[current_worker]
        neighbor_y, neighbor_x, neighbor_offset = neighbor_partition
        if abs(neighbor_y - current_worker_y) == offset or abs(neighbor_x - current_worker_x) == offset:
            neighbors.append(neighbor_worker)
    return neighbors

def convert_local_to_global(worker, y, x):
    start_y, start_x, offset = worker_partitions[worker]
    return start_y + y, start_x + x

def convert_global_to_local(worker, y, x):
    start_y, start_x, offset = worker_partitions[worker]
    return y - start_y, x - start_x

def get_neigh_worker_pos(worker, worker_partitions, glob_y, glob_x):
    for neighbor, partition in worker_partitions.items():
        start_y, start_x, offset = partition
        if glob_y >= start_y and glob_y < start_y + offset and glob_x >= start_x and glob_x < start_x + offset:
            local_y = glob_y - start_y
            local_x = glob_x - start_x
            return neighbor, local_y, local_x

def compute_movements(worker_grid, neighbor_grids):
    movements = []
    for y in range(offset):
        for x in range(offset):
            if isinstance(worker_grid[y][x], Air):
                air_unit = worker_grid[y][x]
                new_y, new_x = air_unit.move(worker_grid, neighbor_grids)
                movements.append((y, x, new_y, new_x))
    return movements

def fill_waiting_data(movements):
    waiting_data = []
    for movement in movements:
        y, x, new_y, new_x = movement
        if new_y < 0 or new_y >= offset or new_x < 0 or new_x >= offset:
            glob_y, glob_x = convert_local_to_global(rank, new_y, new_x)
            neighbor, neigh_y, neigh_x = get_neigh_worker_pos(rank, worker_partitions, glob_y, glob_x)
            waiting_data.append(neighbor)
    return waiting_data

def get_cell2(glob_y, glob_x, worker_partitions, worker_grid, neighbor_grid):
    if glob_y < 0 or glob_y >= N or glob_x < 0 or glob_x >= N:
        return None

    for worker, (start_y, start_x, offset) in worker_partitions.items():
        if glob_y >= start_y and glob_y < start_y + offset and glob_x >= start_x and glob_x < start_x + offset:
            local_y = glob_y - start_y
            local_x = glob_x - start_x
            if worker == rank:
                return worker_grid[local_y][local_x]
            else:
                return neighbor_grid[worker][local_y][local_x]

    return None

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

for _ in range(2):
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

    for i in range(4):
        # Movement phase
        waiting_data = []
        if rank != 0:
            # send current grid to neighbors
            current_worker_neighbor = find_neighbors(worker_grid)
            neighbor_grids = {}

            for neighbor in current_worker_neighbor:
                comm.send(worker_grid, dest=neighbor)
                neighbor_grids[neighbor] = (comm.recv(source=neighbor))

            movements = compute_movements(worker_grid, neighbor_grids)
            waiting_data = fill_waiting_data(movements)

            for neighbor_2 in neighbor_grids:
                comm.send(waiting_data, dest=neighbor_2)

            for neighbor_2 in neighbor_grids:
                waiting_data += comm.recv(source=neighbor_2)
        else:
            current_worker_neighbor = {}
        comm.Barrier()

        if rank != 0:
            for movement in movements:
                y, x, new_y, new_x = movement
                print("Rank", rank, "moving", y, x, "to", new_y, new_x)
                air_unit = worker_grid[y][x]
                next_pos = worker_grid[new_y][new_x]
                if new_y >= 0 and new_y < offset and new_x >= 0 and new_x < offset:
                    if y == new_y and x == new_x:
                        continue
                    elif next_pos == ".":
                        air_unit.y = new_y
                        air_unit.x = new_x
                        worker_grid[new_y][new_x] = air_unit
                        worker_grid[y][x] = "."
                    elif isinstance(next_pos, Air):
                        next_pos.health = min(next_pos.health + air_unit.health, 10)
                        next_pos.attackPower += air_unit.attackPower
                        worker_grid[y][x] = "."
                else:
                    glob_new_y, glob_new_x = convert_local_to_global(rank, new_y, new_x)
                    neighbor, neigh_y, neigh_x = get_neigh_worker_pos(rank, worker_partitions, glob_new_y, glob_new_x)
                    if neighbor != rank:
                        comm.send((air_unit, glob_new_y, glob_new_x), dest=neighbor)
                    worker_grid[y][x] = "."

            for waiting_rank in waiting_data:
                if waiting_rank == rank:
                    air_unit, global_y, global_x = comm.recv(source=MPI.ANY_SOURCE)
                    local_y, local_x = convert_global_to_local(rank, global_y, global_x)
                    next_pos = worker_grid[local_y][local_x]

                    if next_pos == ".":
                        air_unit.y = local_y
                        air_unit.x = local_x
                        worker_grid[local_y][local_x] = air_unit

                    elif isinstance(next_pos, Air):
                        next_pos.health = min(next_pos.health + air_unit.health, 10)
                        next_pos.attackPower += air_unit.attackPower
        comm.Barrier()
        if rank != 0:
            for neighbor in neighbor_grids:
                comm.send(worker_grid, dest=neighbor)
                neighbor_grids[neighbor] = comm.recv(source=neighbor)
            
        comm.Barrier()
        
        # Attack phase
        if rank != 0:
            unitAttackQueue = []
            for y in range(offset):
                for x in range(offset):
                    if worker_grid[y][x] != ".":
                        unit = worker_grid[y][x]
                        temp = unit.attack(worker_grid, neighbor_grids)

                        if unit.health < unit.maxHealth / 2:
                            unit.healing = 1
                        elif len(temp) == 0:
                            unit.healing = 1
                        else:
                            unitAttackQueue += temp

            waiting_attack_data = []
            for attack_instance in unitAttackQueue:
                source_y, source_x, dest_y, dest_x, damage, attacker = attack_instance
                if dest_y >= glob_index_y and dest_y < glob_index_y + offset and dest_x >= glob_index_x and dest_x < glob_index_x + offset:
                    pass
                else:
                    neighbor, neigh_y, neigh_x = get_neigh_worker_pos(rank, worker_partitions, dest_y, dest_x)
                    waiting_attack_data.append(neighbor)

            for neighbor_2 in neighbor_grids:
                comm.send(waiting_attack_data, dest=neighbor_2)

            for neighbor_2 in neighbor_grids:
                waiting_attack_data += comm.recv(source=neighbor_2)
            # print("Rank", rank, "attack queue")
            # print(unitAttackQueue)
            
        comm.Barrier()

        # if rank != 0:
        #     for neighbor in neighbor_grids:
        #         comm.send(worker_grid, dest=neighbor)
        #         neighbor_grids[neighbor] = comm.recv(source=neighbor)
                
        # comm.Barrier()

        # Resolution phase
        if rank != 0:
            earth_damage_list = []
            j = 0
            while j < len(unitAttackQueue):
                k = j + 1
                source_y, source_x, dest_y, dest_x, damage, attacker = unitAttackQueue[j]
                while k < len(unitAttackQueue):
                    source2_y, source2_x, dest2_y, dest2_x, damage2, attacker2 = unitAttackQueue[k]
                    if dest_y == dest2_y and dest_x == dest2_x:
                        damage += damage2
                    k += 1
                j += 1
                earth_damage_list.append((dest_y, dest_x, damage))

            for attack_instance in unitAttackQueue:
                source_y, source_x, dest_y, dest_x, damage, attacker = attack_instance

                if dest_y >= glob_index_y and dest_y < glob_index_y + offset and dest_x >= glob_index_x and dest_x < glob_index_x + offset:
                    local_y, local_x = convert_global_to_local(rank, dest_y, dest_x)
                    attacked_unit = worker_grid[local_y][local_x]
                    if isinstance(attacked_unit, Earth) and not attacked_unit.damaged:
                        attacked_unit.applyDamage(earth_damage_list[0][2])
                    else:
                        attacked_unit.applyDamage(damage)
                else:
                    neighbor, neigh_y, neigh_x = get_neigh_worker_pos(rank, worker_partitions, dest_y, dest_x)
                    comm.send(attack_instance, dest=neighbor)

            for waiting_rank in waiting_attack_data:
                if waiting_rank == rank:
                    attack_instance = comm.recv(source=MPI.ANY_SOURCE)
                    source_y, source_x, dest_y, dest_x, damage, attacker = attack_instance
                    local_y, local_x = convert_global_to_local(rank, dest_y, dest_x)
                    attacked_unit = worker_grid[local_y][local_x]
                    attacked_unit.applyDamage(damage)

        comm.Barrier()

        # fire damage increase
        if rank != 0:
            fire_increase_list = []
            for attack_instance in unitAttackQueue:
                source_y, source_x, dest_y, dest_x, damage, attacker = attack_instance
                
                if dest_y >= glob_index_y and dest_y < glob_index_y + offset and dest_x >= glob_index_x and dest_x < glob_index_x + offset:
                    local_y, local_x = convert_global_to_local(rank, dest_y, dest_x)
                    attacked_unit = worker_grid[local_y][local_x]
                    local_source_y, local_source_x = convert_global_to_local(rank, source_y, source_x)
                    attacker_unit = worker_grid[local_source_y][local_source_x]
                    if attacked_unit != "." and attacked_unit.health <= 0:
                        worker_grid[local_y][local_x] = "."
                        if isinstance(attacker_unit, Fire):
                            attacker_unit.increaseAttack()
                else:
                    neighbor, neigh_y, neigh_x = get_neigh_worker_pos(rank, worker_partitions, dest_y, dest_x)
                    comm.send(attack_instance, dest=neighbor)

            for waiting_rank in waiting_attack_data:
                if waiting_rank == rank:
                    attack_instance = comm.recv(source=MPI.ANY_SOURCE)
                    source_y, source_x, dest_y, dest_x, damage, attacker = attack_instance
                    local_y, local_x = convert_global_to_local(rank, dest_y, dest_x)

                    attacked_unit = worker_grid[local_y][local_x]
                    
                    if attacked_unit != "." and attacked_unit.health <= 0:
                        worker_grid[local_y][local_x] = "."
                        if attacker == "Fire":
                            neighbor, neigh_y, neigh_x = get_neigh_worker_pos(rank, worker_partitions, source_y, source_x)
                            attacker_unit = get_cell2(source_y, source_x, worker_partitions, worker_grid, neighbor_grids)
                            fire_increase_list.append((neighbor, neigh_y, neigh_x))
        comm.Barrier()
        if rank != 0:
            for neighbor in neighbor_grids:
                comm.send(fire_increase_list, dest=neighbor)
            for neighbor in neighbor_grids:
                fire_increase_list += comm.recv(source=neighbor)
            
        comm.Barrier()

        if rank != 0:
            for increase_instance in fire_increase_list:
                worker_num, loc_y, loc_x = increase_instance
                if worker_num == rank:
                    worker_grid[loc_y][loc_x].increaseAttack()

        comm.Barrier()
        
        # if rank != 0:
        #     for neighbor in neighbor_grids:
        #         comm.send(worker_grid, dest=neighbor)
        #         neighbor_grids[neighbor] = comm.recv(source=neighbor)
        # comm.Barrier()
        
        # healing phase
        if rank != 0:
            for y in range(offset):
                for x in range(offset):
                    if worker_grid[y][x] != ".":
                        unit = worker_grid[y][x]
                        if unit.healing == 1:
                            unit.heal()

        comm.Barrier()
        
        if rank == 0:
            pass
            recv_sub_grids(grid)
            print("Round", i + 1, "ends")
            print_grid(grid)
        else:
            send_sub_grid(worker_grid)
        
    # Wave ending
    if rank != 0:
        for y in range(offset):
            for x in range(offset):
                if isinstance(worker_grid[y][x], Fire):
                    worker_grid[y][x].resetAttack()
                if isinstance(worker_grid[y][x], Earth):
                    worker_grid[y][x].damaged = 0
        flood_queue = []
        waiting_flood_data = []
        for y in range(offset):
            for x in range(offset):
                if isinstance(worker_grid[y][x], Water):
                    flood_y, flood_x = worker_grid[y][x].flood(worker_grid, neighbor_grids)
                    neighbor, neigh_y, neigh_x = get_neigh_worker_pos(rank, worker_partitions, flood_y, flood_x)
                    waiting_flood_data.append(neighbor)
                    flood_queue.append((flood_y, flood_x))

        for neighbor in neighbor_grids:
            comm.send(waiting_flood_data, dest=neighbor)

        for neighbor in neighbor_grids:
            waiting_flood_data += comm.recv(source=neighbor)

    comm.Barrier()
    if rank != 0:
        for flood in flood_queue:
            if flood is not None:
                y, x = flood

                if y >= glob_index_y and y < glob_index_y + offset and x >= glob_index_x and x < glob_index_x + offset:
                    local_y, local_x = convert_global_to_local(rank, y, x)
                    worker_grid[local_y][local_x] = Water(local_x, local_y, "Water")
                else:
                    neighbor, neigh_y, neigh_x = get_neigh_worker_pos(rank, worker_partitions, y, x)
                    comm.send((neigh_y, neigh_x), dest=neighbor)

        for worker in waiting_flood_data:
            if worker == rank:
                neigh_y, neigh_x = comm.recv(source=MPI.ANY_SOURCE)
                worker_grid[neigh_y][neigh_x] = Water(neigh_x, neigh_y, "Water")

    comm.Barrier()
    if rank == 0:
        print("Wave", _ + 1, "ends", flush=True)

file.close()