.origin 0
.entrypoint START

#define INS_PER_US   200
#define INS_PER_DELAY_LOOP 2
#define FREQUENCY 450; 350 herts is 21000 rpm, dont use more than 12 for new polygons (different for other prism!)
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
    ; PANASONIC AN44000A, flip enable pin, has the end connector point vertically
    ; NBC3111, end connector horizonal
    ; to mitage the enable and pulse pin are flipped (PANASONIC uses enable, NBC pwm pin)
    SET r30.t2  
    MOV r0, DELAY

DELAYON:
    SUB r0, r0, 1
    QBNE DELAYON, r0, 0

    ; Polygon output pin low
    CLR r30.t2        
    MOV r0, DELAY

DELAYOFF:
    SUB r0, r0, 1
    QBNE DELAYOFF, r0, 0

    SUB r1, r1, 1
    QBNE POLYLOOP, r1, 0
HALT
