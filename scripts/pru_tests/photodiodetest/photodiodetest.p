.origin 0
.entrypoint START

#define INS_PER_US   200
#define INS_PER_DELAY_LOOP 2
#define FREQUENCY 100 ; Hertz maximum is 2.1 kHz
#define DELAY  (1000 * 1000) / (FREQUENCY * 2) * (INS_PER_US / INS_PER_DELAY_LOOP)
#define DURATION 5 ; seconds
#define TICKS DURATION * FREQUENCY
#define PHOTODIODETIME 3000 * 1000 * (INS_PER_US / 3)

START:
    LBCO r0, C4, 4, 4	
    CLR  r0, r0, 4 
    SBCO r0, C4, 4, 4 
    
    MOV r1, TICKS
    MOV r2, PHOTODIODETIME
    
    
    MOV r3, 0x2 ; photodiode test unsuccesfull, sensor fail

    ; pin is high without light and low with light
    ; so if pin is low without light, sensor does not work
    CLR r30.t7
    QBBC FINISH, r31.t16;
    
    MOV r3, 0x0 ; photodiode successfull, 

    SET r30.t7         ; LASER channel 1 ON

POLYLOOP:
    SET r30.t2 ; polygon output pin high, NBC3111
    MOV r0, DELAY       

DELAYON:
    SUB r0, r0, 1
    QBNE DELAYON, r0, 0

    CLR r30.t2  ; polygon output pin low, NBC3111
    MOV r0, DELAY

DELAYOFF:
    SUB r0, r0, 1
    QBNE DELAYOFF, r0, 0

    SUB r1, r1, 1
    QBNE POLYLOOP, r1, 0

    SET r4.t6
MEASURE:
    SUB r2, r2, 1
    QBBC FINISH, r31.t16
    QBNE MEASURE, r2, 0

    MOV r3, 0x1 ; photodiode test unsuccesfull, no signal in time window (i.e. timeout)

FINISH:
    SBCO r3, c24, 0, 4                  ; place result in PRU0 ram
    CLR r30.t7                          ; LASER channel1 OFF
HALT
