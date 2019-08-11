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
     
    SET r30.t7   ; LASER ON
HALT
