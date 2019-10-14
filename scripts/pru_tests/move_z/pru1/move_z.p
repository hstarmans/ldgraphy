.origin 0
.entrypoint START

#define GPIO_1_ADDR       0x4804c000
#define ZSTEP 14
#define GPIO_DATAOUT 0x13c
#define GPIO_SETDATAOUT 0x194
#define GPIO_CLEARDATAOUT 0x190
#define GPIO_OE 0x134

.struct Params
        .u32 steps
        .u32 halfperiodstep
.ends

.assign Params, r6, r7, params

START:
    LBCO r0, C4, 4, 4				
    CLR  r0, r0, 4			
    SBCO r0, C4, 4, 4	

    MOV r3, GPIO_1_ADDR | GPIO_OE
    ; set direction to output
    LBBO r2, r3, 0, 4
    CLR r2, r2, ZSTEP
    SBBO r2, r3, 0, 4

    MOV r2,1 << ZSTEP
    MOV r3, GPIO_1_ADDR | GPIO_SETDATAOUT
    MOV r4, GPIO_1_ADDR | GPIO_CLEARDATAOUT

    ; load parameters
    LBCO &params, c24, 0, SIZE(params)
    MOV r1, params.steps

STEPLOOP:
    SBBO r2, r3, 0, 4
    MOV r0, params.halfperiodstep
DELAYON:
    SUB r0, r0, 1
    QBNE DELAYON, r0, 0
    
    SBBO r2, r4, 0, 4
    MOV r0, params.halfperiodstep
DELAYOFF:
    SUB r0, r0, 1
    QBNE DELAYOFF, r0, 0
    SUB r1, r1, 1
    QBNE STEPLOOP, r1, 0
HALT
