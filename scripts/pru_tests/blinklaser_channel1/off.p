.origin 0
.entrypoint START


START:
    LBCO r0, C4, 4, 4				
    CLR  r0, r0, 4			
    SBCO r0, C4, 4, 4	


    CLR r30.t7   ; LASER channel1 OFF
HALT
