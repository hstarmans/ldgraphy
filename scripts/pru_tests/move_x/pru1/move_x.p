.origin 0
.entrypoint START

#define CONST_PRUDRAM C24
#define GPIO_3_ADDR 0x481ae000
#define XSTEP 20
#define GPIO_DATAOUT 0x13c
#define GPIO_SETDATAOUT 0x194
#define GPIO_CLEARDATAOUT 0x190
#define GPIO_OE 0x134

.struct Params
	.u32	steps
	.u32	halfperiodstep
.ends


.assign Params, r4, *, params


START:
    LBCO r0, C4, 4, 4				
    CLR  r0, r0, 4			
    SBCO r0, C4, 4, 4	

; load parameters
    LBCO  &params, c24, 0, SIZE(params)  // can give conflict with gpio
    MOV r10, params.halfperiodstep
    MOV r1, params.steps
    MOV r2, GPIO_3_ADDR | GPIO_DATAOUT
    MOV r3, 0
; set GPIO bits to writable
;    MOV r4, GPIO_3_ADDR | GPIO_OE
;    // set direction to otput
;    LBBO r5, r4, 0, 4
;    CLR r5, r5, XSTEP
;    SBBO r2, r4, 0, 4

    MOV r2, XSTEP
    MOV r6, GPIO_3_ADDR | GPIO_SETDATAOUT
    MOV r7, GPIO_3_ADDR | GPIO_CLEARDATAOUT
STEPLOOP:
    SBBO r2, r6, 0, 4
    MOV r0, r10
DELAYON:
    SUB r0, r0, 1
    QBNE DELAYON, r0, 0
    
    SBBO r2, r7, 0, 4
    MOV r0, r10
DELAYOFF:
    SUB r0, r0, 1
    QBNE DELAYOFF, r0, 0
    SUB r1, r1, 1
    QBNE STEPLOOP, r1, 0
HALT
