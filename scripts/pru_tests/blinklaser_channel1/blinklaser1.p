.origin 0
.entrypoint START

#define INS_PER_US   200
#define INS_PER_DELAY_LOOP 2
; set up 3 second delay
; 10 ms ==> 100e3 Hertz
#define DELAY  100 
#define TIMES 3000000000 

START:
    LBCO r0, C4, 4, 4				
    CLR  r0, r0, 4			
    SBCO r0, C4, 4, 4	


    MOV r1, TIMES ; pulse 3 times
BLINK:
    SET r30.t7   ; LASER ON
    MOV r0, DELAY
DELAYON:
    SUB r0, r0, 1
    QBNE DELAYON, r0, 0
LASEROFF:
    CLR r30.t7   ; LASER OFF
    MOV r0, DELAY
DELAYOFF:
    SUB r0, r0, 1
    QBNE DELAYOFF, r0, 0
    SUB r1, r1, 1
    QBNE BLINK, r1, 0
HALT
