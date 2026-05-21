import sys

# ==========================================
# MIPS Processor Simulation (Fixed for J)
# ==========================================

# --- Hardware Components ---
registers = [0] * 32        # 32 general-purpose registers ($0 to $31)
data_memory = [0] * 1024    # 1KB Data Memory (Word-indexed internally)
instruction_memory = []     # Instruction Memory
pc = 0                      # Program Counter

# --- Configuration ---
DATA_START_ADDR = 0x10010000
TEXT_BASE = 0x00400000      # <-- typical assembler text base (we map J targets against this)
max_data_index = 0          # Tracks how many lines to write back to data.txt

# --- Helper: Sign Extension ---
def sign_extend(value, bits):
    sign_bit = 1 << (bits - 1)
    return (value & (sign_bit - 1)) - (value & sign_bit)

# --- File Loaders & Writers ---
def load_instructions(filename):
    print(f"--- Loading Instructions from {filename} ---")
    try:
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    # expect each line a 32-bit binary string
                    instruction_memory.append(line)
        print(f"Loaded {len(instruction_memory)} instructions.\n")
    except FileNotFoundError:
        print(f"Error: '{filename}' not found. Please verify the file exists.")
        sys.exit()

def load_data(filename):
    global max_data_index
    print(f"--- Loading Data Segment from {filename} ---")
    try:
        with open(filename, 'r') as f:
            index = 0
            for line in f:
                line = line.strip()
                if line:
                    data_memory[index] = sign_extend(int(line, 2), 32)
                    index += 1
            max_data_index = max(index - 1, 0)
        print(f"Loaded {index} data words.\n")
    except FileNotFoundError:
        print(f"Warning: '{filename}' not found. Data memory initialized to 0.\n")

def sync_data_to_file(filename):
    """ Writes the current state of Data Memory back to the text file in 32-bit binary """
    try:
        with open(filename, 'w') as f:
            for i in range(max_data_index + 1):
                # Convert the integer back to a 32-bit binary string (handling negatives)
                bin_str = format(data_memory[i] & 0xFFFFFFFF, '032b')
                f.write(bin_str + '\n')
    except Exception as e:
        print(f"Failed to write to {filename}: {e}")

# --- Stage 1: FETCH ---
def fetch():
    global pc
    if pc // 4 >= len(instruction_memory):
        return None, pc

    instruction = instruction_memory[pc // 4]
    next_pc = pc + 4
    return instruction, next_pc

# --- Stage 2: DECODE ---
def decode(instr):
    opcode_bin = instr[0:6]    # Bits 31-26
    rs_bin     = instr[6:11]   # Bits 25-21
    rt_bin     = instr[11:16]  # Bits 20-16
    rd_bin     = instr[16:21]  # Bits 15-11
    funct_bin  = instr[26:32]  # Bits 5-0
    imm_bin    = instr[16:32]  # Bits 15-0

    return {
        "opcode": opcode_bin,
        "funct":  funct_bin,
        "rs":     int(rs_bin, 2),
        "rt":     int(rt_bin, 2),
        "rd":     int(rd_bin, 2),
        "imm":    int(imm_bin, 2),
        "target": int(instr[6:32], 2),  # 26-bit field for J
        "rs_val": registers[int(rs_bin, 2)],
        "rt_val": registers[int(rt_bin, 2)]
    }

# --- Stage 3: EXECUTE ---
def execute(decoded, next_pc):
    op = decoded["opcode"]
    funct = decoded["funct"]
    rs_val = decoded["rs_val"]
    rt_val = decoded["rt_val"]
    imm = decoded["imm"]

    alu_result = 0
    branch_taken = False
    branch_target = 0

    # R-Type
    if op == "000000":
        if funct == "100000":   # ADD
            alu_result = rs_val + rt_val
        elif funct == "100010": # SUB
            alu_result = rs_val - rt_val
        elif funct == "001100": # SYSCALL
            if registers[2] == 10:
                print("\n[System] Program Exited via Syscall 10.")
                return None, False, 0

    # MUL (Special)
    elif op == "011100" and funct == "000010":
        alu_result = rs_val * rt_val

    # I-Type
    elif op == "001000": # ADDI
        alu_result = rs_val + sign_extend(imm, 16)
    elif op == "001101": # ORI
        alu_result = rs_val | imm
    elif op == "001111": # LUI
        alu_result = imm << 16
    elif op == "100011": # LW
        alu_result = rs_val + sign_extend(imm, 16)
    elif op == "101011": # SW
        alu_result = rs_val + sign_extend(imm, 16)
    elif op == "000100": # BEQ
        if rs_val == rt_val:
            branch_taken = True
            branch_target = next_pc + (sign_extend(imm, 16) << 2)

    # J-Type
    elif op == "000010": # J
        branch_taken = True
        upper_bits = next_pc & 0b11110000000000000000000000000000
        branch_target = upper_bits | (decoded["target"] << 2)

        # --- FIX: map assembler's typical text base to our instruction memory space ---
        # Some assemblers encode jump targets relative to 0x00400000 (MIPS text segment).
        # If the computed branch_target lands in that region, map it down to our PC=0-based text.
        if branch_target >= TEXT_BASE:
            branch_target = branch_target - TEXT_BASE

    return alu_result, branch_taken, branch_target

# --- Stage 4: MEMORY ACCESS ---
def memory_access(decoded, alu_result):
    global max_data_index
    op = decoded["opcode"]
    rt_val = decoded["rt_val"]
    mem_read_data = 0

    if alu_result is not None:
        mem_index = (alu_result - DATA_START_ADDR) // 4

    if op == "100011": # LW
        if 0 <= mem_index < len(data_memory):
            mem_read_data = data_memory[mem_index]

    elif op == "101011": # SW
        if 0 <= mem_index < len(data_memory):
            data_memory[mem_index] = rt_val

            # Update max index if we write past the original file length
            if mem_index > max_data_index:
                max_data_index = mem_index

            # WRITING BACK TO THE PHYSICAL FILE
            sync_data_to_file("data.txt")
            print(f"   -> [MEMORY WRITE] Stored {rt_val} into address {hex(alu_result)}. Synced to 'data.txt'.")

    return mem_read_data

# --- Stage 5: WRITE BACK ---
def write_back(decoded, alu_result, mem_read_data):
    op = decoded["opcode"]
    rd = decoded["rd"]
    rt = decoded["rt"]

    reg_dest = 0
    write_data = 0
    write_enable = False

    if op == "000000" or op == "011100":
        reg_dest = rd
        write_data = alu_result
        write_enable = True
    elif op in ["001000", "001101", "001111"]:
        reg_dest = rt
        write_data = alu_result
        write_enable = True
    elif op == "100011":
        reg_dest = rt
        write_data = mem_read_data
        write_enable = True

    if write_enable and reg_dest != 0:
        registers[reg_dest] = write_data

    # enforce $0 == 0
    registers[0] = 0

# ==========================================
# Main Execution Block
# ==========================================
if __name__ == "__main__":

    load_instructions("machine_code.txt")
    load_data("data.txt")

    print("--- Starting Execution ---")
    while True:
        curr_inst, temp_pc = fetch()
        if curr_inst is None:
            break

        decoded = decode(curr_inst)
        alu_res, branch, branch_tgt = execute(decoded, temp_pc)

        if alu_res is None:
            break

        mem_data = memory_access(decoded, alu_res)
        write_back(decoded, alu_res, mem_data)

        if branch:
            pc = branch_tgt
        else:
            pc = temp_pc

    print("--- Simulation Finished ---\n")

    # --- FINAL ANSWER LOCATION ---
    print("=====================================================")
    print("              WHERE TO CHECK THE ANSWER              ")
    print("=====================================================")
    print("The processor has updated the physical 'data.txt' file.")
    print("Open 'data.txt' in your text editor. The lines correspond")
    print("to the memory addresses:")
    print("  Line 1: 0x10010000 (Your Input Number)")
    print("  Line 2: 0x10010004 (Your Final Result in 32-bit Binary)")
    print("=====================================================")