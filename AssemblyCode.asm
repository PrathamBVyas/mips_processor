.data
    input_num:  .word 5      # The value 5 is stored at 0x10010000
    result:     .word 0      # Space for result at 0x10010004

.text
.globl main

main:
    # 1. LOAD ADDRESS MANUALLY
    # Instead of 'la', we use 'lui' and 'ori' to form 0x10010000
    # This aligns with MIPS encoding formats [cite: 1926]
    lui     $t1, 0x1001      # Load upper 16 bits: $t1 becomes 0x10010000
    ori     $t1, $t1, 0      # Lower 16 bits are 0. $t1 remains 0x10010000 [cite: 1754]

    # 2. LOAD VALUE
    # Load word from the address stored in $t1
    lw      $t0, 0($t1)      # $t0 = 5 [cite: 1736]

    # 3. INITIALIZE RESULT
    # Use ADDI to set $t2 to 1 (0 + 1)
    addi    $t2, $zero, 1    # $t2 = 1 [cite: 1914]

loop:
    # 4. BRANCH CONDITION   
    # If $t0 is 0, we are finished
    beq     $t0, $zero, end_loop  # [cite: 1767]

    # 5. MULTIPLY
    # Multiply result by current number
    mul     $t2, $t2, $t0    

    # 6. DECREMENT
    # Use ADDI with a negative immediate to subtract
    addi    $t0, $t0, -1     # $t0 = $t0 - 1 [cite: 1917]

    # 7. JUMP
    # Jump back to the start of the loop
    j       loop             # [cite: 1964]

end_loop:
    # 8. STORE RESULT
    # Store the value in $t2 to the address in $t1 with offset 4
    # Address = 0x10010000 + 4 = 0x10010004
    sw      $t2, 4($t1)      # [cite: 1736]

    # 9. EXIT
    # Basic syscall to stop the program
    addi    $v0, $zero, 10
    syscall