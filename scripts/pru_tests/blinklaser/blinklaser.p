.origin 0
.entrypoint START

#define PRU0_ARM_INTERRUPT 19
#define INS_PER_US   200
#define INS_PER_DELAY_LOOP 2
// set up 3 second delay
#define DELAY   3000 * 1000 * (INS_PER_US / INS_PER_DELAY_LOOP)


START:
    LBCO r0, C4, 4, 4					// Load Bytes Constant Offset (?)
    CLR  r0, r0, 4						// Clear bit 4 in reg 0
    SBCO r0, C4, 4, 4					// Store Bytes Constant Offset


// TODO replace constant
    MOV r1, 3 // pulse 3 times
BLINK:
    SET r30.t1   // LASER ON
    MOV r0, DELAY
DELAYON:
    SUB r0, r0, 1
    QBNE DELAYON, r0, 0
LASEROFF:
    CLR r30.t1  // LASER OFF
    MOV r0, DELAY
DELAYOFF:
    SUB r0, r0, 1
    QBNE DELAYOFF, r0, 0
    SUB r1, r1, 1
    QBNE BLINK, r1, 0

    MOV R31.b0, PRU0_ARM_INTERRUPT+16   // Send notification to Host for program completion
HALT
