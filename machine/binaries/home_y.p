.origin 0
.entrypoint START

#define GPIO_1_BASE       0x4804c000
#define CONST_PRUDRAM     C24
#define GPIO_DATAIN       0x138
#define YPO               18

.struct Params
	.u32	steps
	.u32	halfperiodstep
.ends


.assign Params, r5, *, params


START:
    LBCO r0, C4, 4, 4				
    CLR  r0, r0, 4			
    SBCO r0, C4, 4, 4	

; load parameters
    LBCO  &params, c24, 0, SIZE(params)
    ; r0 reserved for halfperiod
    MOV r1, params.steps
    MOV r2, 1  ; no success
    MOV r3, GPIO_1_BASE | GPIO_DATAIN
STEPLOOP:
    LBBO r4, r3, 0, 4
    QBBC bit_is_clear, r4, YPO
    MOV r2, 0 ; success
    JMP FINISH
bit_is_clear:
    SET r30.t14 ; Y-STEP pulse
    MOV r0, params.halfperiodstep
DELAYON:
    SUB r0, r0, 1
    QBNE DELAYON, r0, 0

    CLR r30.t14   ; Y-STEP pulse
    MOV r0, params.halfperiodstep
DELAYOFF:
    SUB r0, r0, 1
    QBNE DELAYOFF, r0, 0
    SUB r1, r1, 1
    QBNE STEPLOOP, r1, 0
FINISH:
HALT
