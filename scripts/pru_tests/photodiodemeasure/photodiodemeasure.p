.origin 0
.entrypoint START

#define PRU0_ARM_INTERRUPT 19
#define INS_PER_US   200
#define INS_PER_DELAY_LOOP 2
#define FREQUENCY 1000 ; Hertz maximum is 2.1 kHz
#define DELAY  (1000 * 1000) / (FREQUENCY * 2) * (INS_PER_US / INS_PER_DELAY_LOOP)
#define DURATION 60 ; seconds
#define TICKS DURATION * FREQUENCY

START:
    LBCO r0, C4, 4, 4		
    CLR  r0, r0, 4	
    SBCO r0, C4, 4, 4	
    
    MOV r1, TICKS
    SET r30.t1         ; LASER ON

POLYLOOP:
    SET r30.t7  ; polygon output pin high
    MOV r0, DELAY       

DELAYON:
    SUB r0, r0, 1
    QBNE DELAYON, r0, 0

    CLR r30.t7  ; polygon output pin low
    MOV r0, DELAY

DELAYOFF:
    SUB r0, r0, 1
    QBNE DELAYOFF, r0, 0

    SUB r1, r1, 1
    QBNE POLYLOOP, r1, 0


FINISH:
    CLR r30.t1          ;  LASER OFF
HALT
