.origin 0
.entrypoint START

#define PRU0_ARM_INTERRUPT 19
#define INS_PER_US   200
#define INS_PER_DELAY_LOOP 2
#define FREQUENCY 1000 // hertz maximum is 2.1 kHz
// can you do 1/1000 here or will it result in zero?
// do you need to account for the fact that a delay cycle is 2 instructions?
#define DELAY  (1000 * 1000) / (FREQUENCY * 2) * (INS_PER_US / INS_PER_DELAY_LOOP)
#define DURATION 5 // seconds
#define TICKS DURATION * FREQUENCY
#define PHOTODIODETIME 3000 * 1000 * (INS_PER_US / INS_PER_DELAY_LOOP)

START:
    LBCO r0, C4, 4, 4					// Load Bytes Constant Offset (?)
    CLR  r0, r0, 4						// Clear bit 4 in reg 0
    SBCO r0, C4, 4, 4					// Store Bytes Constant Offset
// r0 = DELAY
// r1 = TICKS
// r2 = PHOTODIODETIME 
// r3 = TEST   
    MOV r1, TICKS
    MOV r2, PHOTODIODETIME
    MOV r3, 0xbabe0000 // photodiode test succesfull
    SET r30.t1         // LASER ON

LOOP:
    SET r30.t5 // polygon output pin high
    MOV r0, DELAY       

DELAYON:
    SUB r0, r0, 1
    QBNE DELAYON, r0, 0

    CLR r30.t5  // polygon output pin low
    MOV r0, DELAY

DELAYOFF:
    SUB r0, r0, 1
    QBNE DELAYOFF, r0, 0

    SUB r1, r1, 1
    QBNE LOOP, r1, 0

MEASURE:
    SUB r2, r2, 1
    QBBS FINISH, r31.t6
    QBNE MEASURE, r2, 0

    MOV r3, 0xbabe0001 // photodiode test unsuccesfull, i.e timeout

FINISH:
    SBCO r3, c24, 0, 4                  // place result in PRU0 ram
    CLR r30.t1                          // LASER OFF
    MOV R31.b0, PRU0_ARM_INTERRUPT+16   // Send notification to Host for program completion
HALT
