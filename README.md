# MIPS Processor Simulation

**Course Project** | Students: BC2025094, BC2025078, BC2025119

A software simulation of a MIPS processor pipeline implemented in Python, along with a sample MIPS assembly program that computes the factorial of a number.

---

## Project Overview

This project simulates the five classic stages of the MIPS processor pipeline:

1. **Fetch** – Retrieves the next instruction from instruction memory using the Program Counter (PC)
2. **Decode** – Parses the 32-bit binary instruction into opcode, register fields, immediate values, and jump targets
3. **Execute** – Performs ALU operations, evaluates branch conditions, and computes memory addresses
4. **Memory Access** – Reads from or writes to data memory; syncs write results back to `data.txt`
5. **Write Back** – Writes ALU or memory results back into the register file

The sample program computes the **factorial of 5** (5! = 120) using a MIPS assembly loop and stores the result in data memory.

---

## Repository Structure

```
MIPS Project/
├── AssemblyCode.asm.asm              # MIPS assembly source (factorial of 5)
├── BC2025094_BC2025078_BC2025119_processor.py.py  # Python MIPS processor simulator
├── machine_code.txt                  # Pre-assembled 32-bit binary instructions
├── data.txt                          # Data memory (input value + result)
└── Project_Report.pdf                # Full project report
```

---

## Files Description

### `AssemblyCode.asm.asm`
The MIPS assembly source code. It computes `n!` for the value stored in data memory at address `0x10010000` (default: 5). The algorithm:
- Loads the input number from memory
- Multiplies iteratively in a loop, decrementing the counter each iteration
- Branches out of the loop when the counter reaches zero
- Stores the final result at `0x10010004`

**Instructions used:** `lui`, `ori`, `lw`, `addi`, `beq`, `mul`, `j`, `sw`, `syscall`

### `BC2025094_BC2025078_BC2025119_processor.py.py`
The main Python simulator. It reads binary instructions from `machine_code.txt` and data from `data.txt`, then executes them through the five-stage pipeline. Key behaviors:
- Supports R-type, I-type, and J-type MIPS instructions
- Handles sign extension for immediate values
- Maps jump targets from the standard MIPS text base (`0x00400000`) to the simulator's PC-zero-based instruction memory
- Writes memory results back to `data.txt` after every store instruction

### `machine_code.txt`
Contains the 11 pre-assembled 32-bit binary instructions corresponding to the assembly source, one per line. Loaded directly into instruction memory at runtime.

### `data.txt`
Represents data memory starting at address `0x10010000`. Each line is a 32-bit binary value representing one word:
- **Line 1** (`0x10010000`): Input number (e.g., `5`)
- **Line 2** (`0x10010004`): Result written here after execution

---

## Supported Instructions

| Type   | Instructions                        |
|--------|-------------------------------------|
| R-Type | `add`, `sub`, `mul`, `syscall`      |
| I-Type | `addi`, `ori`, `lui`, `lw`, `sw`, `beq` |
| J-Type | `j`                                 |

---

## How to Run

### Prerequisites
- Python 3.x (no additional libraries required)

### Steps

1. First write the required assembly code and compile it in the MIPS assembler.

2. Then add dump the text and data segments from the MIPS compiler and paste them in the machine_code.txt and data.txt files respectively.

3. Make sure all four files are in the **same directory**:
   - `BC2025094_BC2025078_BC2025119_processor.py`
   - `machine_code.txt`
   - `data.txt`

4. Run the simulator:
   ```bash
   python BC2025094_BC2025078_BC2025119_processor.py
   ```

5. The simulator will print a step-by-step execution log and terminate with `syscall 10`.

6. Open `data.txt` after execution to read the result:
   - **Line 1**: Original input (e.g., `00000000000000000000000000000101` = 5)
   - **Line 2**: Computed result in 32-bit binary (e.g., `00000000000000000000000001111000` = 120)

### Changing the Input

To compute the factorial of a different number, edit the first line of `data.txt` with its 32-bit binary representation. For example, to compute `6!`, replace line 1 with:
```
00000000000000000000000000000110
```

---

## Example Output

```
--- Loading Instructions from machine_code.txt ---
Loaded 11 instructions.

--- Loading Data Segment from data.txt ---
Loaded 1 data words.

--- Starting Execution ---
   -> [MEMORY WRITE] Stored 120 into address 0x10010004. Synced to 'data.txt'.

[System] Program Exited via Syscall 10.
--- Simulation Finished ---

=====================================================
              WHERE TO CHECK THE ANSWER              
=====================================================
The processor has updated the physical 'data.txt' file.
  Line 1: 0x10010000 (Your Input Number)
  Line 2: 0x10010004 (Your Final Result in 32-bit Binary)
=====================================================
```

---

## Design Notes

- The register file contains 32 registers (`$0`–`$31`); `$zero` (`$0`) is hardwired to 0 and enforced after every write-back.
- Data memory is 1 KB (1024 words), addressed from `0x10010000`.
- The simulator adjusts J-type jump targets encoded relative to the standard MIPS text base (`0x00400000`) to work correctly with the internal zero-based PC.
- `data.txt` is synced to disk on every `sw` instruction, so results persist after execution.
