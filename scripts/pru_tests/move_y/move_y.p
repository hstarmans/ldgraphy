.origin 0
.entrypoint START

#define CONST_PRUDRAM C24


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
    LBCO  &params, c24, 0, SIZE(params)
    MOV r1, params.steps
STEPLOOP:
    SET r30.t3 ; Y-STEP pulse
    MOV r0, params.halfperiodstep
DELAYON:
    SUB r0, r0, 1
    QBNE DELAYON, r0, 0

    CLR r30.t3   ; Y-STEP pulse
    MOV r0, params.halfperiodstep
DELAYOFF:
    SUB r0, r0, 1
    QBNE DELAYOFF, r0, 0
    SUB r1, r1, 1
    QBNE STEPLOOP, r1, 0
HALT
