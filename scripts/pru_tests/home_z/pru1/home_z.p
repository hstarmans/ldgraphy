.origin 0
.entrypoint START

#define GPIO_1_ADDR       0x4804c000
#define GPIO_DATAOUT      0x13c
#define GPIO_DATAIN       0x138
#define GPIO_SETDATAOUT   0x194
#define GPIO_CLEARDATAOUT 0x190
#define GPIO_OE           0x134
#define ZPO               19
#define ZSTEP             14

.struct Params
	.u32	steps
	.u32	halfperiodstep
.ends


.assign Params, r12, r13, params


START:
    LBCO r0, C4, 4, 4				
    CLR  r0, r0, 4			
    SBCO r0, C4, 4, 4	

; this can also be done via config-pin
    MOV r3, GPIO_3_ADDR | GPIO_OE
    ; set direction to output
    LBBO r2, r3, 0, 4
    CLR r2, r2, ZSTEP
    SBBO r2, r3, 0, 4

    ; load parameters
    LBCO  &params, c24, 0, SIZE(params)
    ; r0 reserved for halfperiod
    MOV r1, params.stepsr
    MOV r2, 1 << XSTEP
    MOV r3, GPIO_3_ADDR | GPIO_SETDATAOUT
    MOV r4, GPIO_3_ADDR | GPIO_CLEARDATAOUT
    MOV r5, GPIO_1_ADDR | GPIO_DATAIN
    MOV r10, 1 ; no success

STEPLOOP:
    LBBO r6, r5, 0, 4
    QBBC bit_is_clear, r6, XPO
    MOV r10, 0 ; success
    JMP FINISH
bit_is_clear:
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
FINISH:
HALT