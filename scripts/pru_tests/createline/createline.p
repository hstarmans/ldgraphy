.origin 0
.entrypoint START

#define INS_PER_US   200
#define INS_PER_DELAY_LOOP 2
#define FREQUENCY 450 ; Hertz maximum is 2.1 kHz
#define DELAY  1000 / (FREQUENCY * 2) * 1000 * (INS_PER_US / INS_PER_DELAY_LOOP)
#define DURATION 1500 ; seconds
#define TICKS DURATION * FREQUENCY

START:
    LBCO r0, C4, 4, 4			
    CLR  r0, r0, 4		
    SBCO r0, C4, 4, 4	
    SET r30.t1
    MOV r1, TICKS

LASERON:
    SET r30.t7  ; laser channel 1
    
POLYLOOP:
    ; Polygon output pin high
    ; PANASONIC AN44000A, flip enable pin
    SET r30.t2  ; NBC3111
    MOV r0, DELAY
       
DELAYON:
    SUB r0, r0, 1
    QBNE DELAYON, r0, 0

    ; Polygon output pin low
    ; PANASONIC AN44000A, flip enable pin
    CLR r30.t2        ; NBC3111
    MOV r0, DELAY

DELAYOFF:
    SUB r0, r0, 1
    QBNE DELAYOFF, r0, 0

    SUB r1, r1, 1
    QBNE POLYLOOP, r1, 0

LASEROFF:
    CLR r30.t7  ; laser channel 1
HALT
