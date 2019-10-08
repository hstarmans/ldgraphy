.origin 0
.entrypoint START

#define CONST_PRUDRAM C24
#define GPIO_3_ADDR 0x481AE000
#define XSTEP 20
#define GPIO_DATAOUT 0x13c
#define GPIO_SETDATAOUT 0x194
#define GPIO_CLEARDATAOUT 0x190
#define GPIO_OE 0x134
#define DURATION 20000


START:
    LBCO r0, C4, 4, 4				
    CLR  r0, r0, 4			
    SBCO r0, C4, 4, 4	

    MOV r3, GPIO_3_ADDR | GPIO_OE
    // set direction to otput
    LBBO r2, r3, 0, 4
    CLR r2, r2, XSTEP
    SBBO r2, r3, 0, 4

    MOV r2,1 << XSTEP
    MOV r3, GPIO_3_ADDR | GPIO_SETDATAOUT
    MOV r4, GPIO_3_ADDR | GPIO_CLEARDATAOUT

    MOV r1, 10000
STEPLOOP:
    SBBO r2, r3, 0, 4
    MOV r0, DURATION
DELAYON:
    SUB r0, r0, 1
    QBNE DELAYON, r0, 0
    
    SBBO r2, r4, 0, 4
    MOV r0, DURATION
DELAYOFF:
    SUB r0, r0, 1
    QBNE DELAYOFF, r0, 0
    SUB r1, r1, 1
    QBNE STEPLOOP, r1, 0
HALT
