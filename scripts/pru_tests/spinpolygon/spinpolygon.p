.origin 0
.entrypoint START

#define INS_PER_US   200
#define INS_PER_DELAY_LOOP 2
#define FREQUENCY 450 ; Hertz maximum is 2.1 kHz
#define DELAY  1000 / (FREQUENCY * 2) * 1000 * (INS_PER_US / INS_PER_DELAY_LOOP)
#define DURATION 15 ; seconds
#define TICKS DURATION * FREQUENCY

START:
    LBCO r0, C4, 4, 4			
    CLR  r0, r0, 4		
    SBCO r0, C4, 4, 4	
    
    MOV r1, TICKS
    
POLYLOOP:
    ; Polygon output pin high
    ; SET r30.t7     // PANASONIC AN44000A
    SET r30.t5  ; NBC3111
    MOV r0, DELAY
       
DELAYON:
    SUB r0, r0, 1
    QBNE DELAYON, r0, 0

    ; Polygon output pin low
    ; CLR r30.t7     // PANASONIC AN44000A
    CLR r30.t5        // NBC3111
    MOV r0, DELAY

DELAYOFF:
    SUB r0, r0, 1
    QBNE DELAYOFF, r0, 0

    SUB r1, r1, 1
    QBNE POLYLOOP, r1, 0
HALT
