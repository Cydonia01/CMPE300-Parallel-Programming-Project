# CMPE300 Parallel Programming Project

## Elemental Battle Simulation with MPI

### Project Overview

This project implements a parallel simulation of elemental battles using MPI (Message Passing Interface) in Python. The simulation involves four elemental unit types (Earth, Fire, Water, Air) that interact on a grid-based battlefield through multiple waves and rounds of combat.

### Table of Contents

- [Project Overview](#project-overview)
- [System Architecture](#system-architecture)
- [Unit Types and Characteristics](#unit-types-and-characteristics)
- [Game Mechanics](#game-mechanics)
- [Parallel Implementation](#parallel-implementation)
- [Installation & Requirements](#installation--requirements)
- [Usage](#usage)
- [Input Format](#input-format)
- [Output Format](#output-format)
- [Example Execution](#example-execution)
- [Implementation Details](#implementation-details)
- [Known Issues](#known-issues)
- [Additional Resources](#additional-resources)

### System Architecture

The simulation employs a **master-worker** parallel architecture:

- **Master Process (Rank 0)**: Coordinates the simulation, reads input, manages grid partitioning, and writes final output
- **Worker Processes (Rank 1-N)**: Handle local grid computations, unit interactions, and inter-process communication

### Unit Types and Characteristics

#### Earth Units (E)

- **Health**: 18 HP (max)
- **Attack Power**: 2
- **Healing Rate**: 3 HP per healing phase
- **Attack Pattern**: Orthogonal directions (up, down, left, right)
- **Special Ability**: Takes half damage (damage is integer-divided by 2)

#### Fire Units (F)

- **Health**: 12 HP (max)
- **Attack Power**: 4 (can increase up to 6)
- **Healing Rate**: 1 HP per healing phase
- **Attack Pattern**: All 8 adjacent cells (orthogonal + diagonal)
- **Special Ability**: Attack power increases by 1 when killing an enemy unit

#### Water Units (W)

- **Health**: 14 HP (max)
- **Attack Power**: 3
- **Healing Rate**: 2 HP per healing phase
- **Attack Pattern**: Diagonal directions only
- **Special Ability**: Can flood empty adjacent cells, creating new Water units

#### Air Units (A)

- **Health**: 10 HP (max)
- **Attack Power**: 2
- **Healing Rate**: 2 HP per healing phase
- **Attack Pattern**: All 8 directions, can skip over one empty cell
- **Special Ability**: Can move to optimize attack opportunities; merges when occupying same cell

### Game Mechanics

#### Round Structure

Each round consists of four phases executed in order:

1. **Movement Phase**: Only Air units can move
2. **Attack Phase**: All units determine their targets
3. **Resolution Phase**: Damage is applied to targeted units
4. **Healing Phase**: Units with low health or no targets heal

#### Combat Rules

- Units attack enemies of different types within their attack pattern
- Healing occurs when health < 50% of max health OR no valid targets exist
- Dead units (health ≤ 0) are removed from the grid
- Air units merge when moving to the same cell (combined health up to max, combined attack power)

#### Wave System

- Multiple waves of units are spawned throughout the simulation
- Each wave places new units on the grid
- Between waves: Fire units reset attack power, Water units attempt flooding

### Parallel Implementation

#### Grid Partitioning

- Grid is divided into square sub-grids using **checkered partitioning**
- Each worker manages a local sub-grid
- Number of workers must be a perfect square (4, 9, 16, etc.)
- Sub-grid size = N / √(number_of_workers)

#### Communication Strategy

- **Synchronization**: Workers exchange full sub-grids with neighbors
- **Boundary Management**: Cross-boundary attacks and movements handled via MPI messaging
- **Coordination**: Barrier synchronization ensures phase completion across all workers

#### Data Distribution

- Master distributes unit spawning data to appropriate workers
- Workers handle local computations and communicate boundary interactions
- Final grid reconstruction at master for output generation

### Installation & Requirements

#### Prerequisites

```bash
# Python 3.x
# MPI implementation (e.g., OpenMPI, MPICH)
# mpi4py library
```

#### Installation

```bash
# Install MPI (example for Ubuntu/Debian)
sudo apt-get install openmpi-bin openmpi-dev

# Install Python MPI bindings
pip install mpi4py

# Clone or download project files
# Ensure main.py and input files are in the same directory
```

### Usage

#### Basic Execution

```bash
mpiexec -n <num_processes> python main.py <input_file> <output_file>
```

#### Parameters

- `<num_processes>`: Total number of MPI processes (1 master + N workers, where N is a perfect square)
- `<input_file>`: Path to input file containing simulation parameters
- `<output_file>`: Path where final grid state will be written

### Input Format

```
N W T R
Wave 1:
E: y1 x1, y2 x2, ...
F: y1 x1, y2 x2, ...
W: y1 x1, y2 x2, ...
A: y1 x1, y2 x2, ...
Wave 2:
...
```

#### Parameters

- **N**: Grid size (N×N)
- **W**: Number of waves
- **T**: Number of units per faction per wave
- **R**: Number of rounds per wave

### Output Format

The output file contains the final grid state with:

- `E`: Earth units
- `F`: Fire units
- `W`: Water units
- `A`: Air units
- `.`: Empty cells

### Example Execution

#### Input File (input1.txt)

```
8 2 2 4
Wave 1:
E: 0 0, 1 1
F: 2 2, 3 3
W: 4 4, 4 5
A: 6 6, 7 7
Wave 2:
E: 1 0, 2 1
F: 3 2, 4 3
W: 5 4, 6 5
A: 7 6, 0 7
```

#### Execution Commands

```bash
# For input1.txt (8x8 grid, requires 4 workers + 1 master = 5 processes)
mpiexec -n 5 python main.py input1.txt output1.txt

# For larger inputs (may require more workers)
mpiexec -n 10 python main.py my_input2.txt my_output2.txt
```

#### Expected Output (output1.txt)

```
E . . . . . . .
E E . . . . . .
. E F A W . . .
. . F . W . . .
. . . F A W . .
. . . . W W A .
. . . . . W . .
. . . . . . A .
```

### Implementation Details

#### Key Classes

- **Unit**: Base class for all unit types
- **Earth, Fire, Water, Air**: Specific unit implementations with unique behaviors
- **MPI Communication**: Handles grid partitioning and inter-process messaging

#### Critical Functions

- `read_wave()`: Parses input file for unit placement
- `synchronize()`: Exchanges grid data between neighboring workers
- `compute_movements()`: Calculates Air unit movements
- `get_cell()`: Retrieves cell data across grid boundaries
- `convert_local_to_global()`: Coordinate system conversion

#### Synchronization Points

- After unit placement
- After movement computation
- After attack resolution
- After healing phase
- Between waves

### Known Issues

#### Implementation Notes

- **Grid Exchange**: Currently sends entire sub-grids to neighbors instead of only boundary data
  - This increases communication overhead but simplifies implementation
  - Future optimization could implement boundary-only communication
- **Perfect Square Requirement**: Number of workers must be a perfect square for grid partitioning
- **Memory Usage**: Full grid synchronization increases memory requirements

#### Assumptions

- Input coordinates are valid and within grid boundaries
- Number of MPI processes matches required worker count
- Grid size is evenly divisible by square root of worker count

### Additional Resources

#### Project Files

- `main.py`: Complete simulation implementation
- `input1.txt`: Sample input file
- `output1.txt`: Expected output for input1.txt
- `report.pdf`: Project report detailing design and implementation

#### External Links

- MPI4Py Documentation: https://mpi4py.readthedocs.io/
- OpenMPI Installation Guide: https://www.open-mpi.org/

#### Performance Considerations

- **Scalability**: Performance scales with grid size and worker count
- **Communication Overhead**: Synchronization frequency affects overall performance
- **Load Balancing**: Uniform grid partitioning ensures balanced workload distribution

#### Testing

```bash
# Test with provided examples
mpiexec -n 5 python main.py input1.txt test_output1.txt
diff test_output1.txt output1.txt  # Should show no differences

# Performance testing with larger grids
mpiexec -n 10 python main.py my_input2.txt my_output2.txt
```

---

**Course**: CMPE300 - Parallel Programming  
**Implementation**: Python with MPI4Py  
**Architecture**: Master-Worker with Grid Partitioning
