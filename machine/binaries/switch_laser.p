.origin 0
.entrypoint START

.struct Params
        .u32  power 
.ends

.assign Params, r5, *, params

START:
    LBCO r0, C4, 4, 4
    CLR  r0, r0, 4
    SBCO r0, C4, 4, 4

; load parameters
    LBCO &params, C24, 0, SIZE(params)
    MOV r0, params.power
    QBEQ LASEROFF, r0, 0 
CHANNEL1ON:
    SET r30.t1
    QBEQ FINISH, r0, 1
CHANNEL2ON:
    SET r30.t0
    QBEQ FINISH, r0, 2
LASEROFF:
    CLR r30.t1  
    CLR r30.t0
FINISH:
HALT

    



