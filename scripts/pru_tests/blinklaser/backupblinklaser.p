.origin 0
.entrypoint START

#define PRU0_ARM_INTERRUPT 19
#define GPIO_LASER_DATA    15    // GPIO_3, PIN_P9_29
#define GPIO_0_BASE   0x44e07000
#define GPIO_3_BASE   0x481AF000
#define GPIO_OE                 0x134
#define GPIO_DATAIN             0x138
#define GPIO_DATAOUT            0x13c
#define GPIO_CLEARDATAOUT 	0x190
#define GPIO_SETDATAOUT 	0x194
#define INS_PER_US   200
#define INS_PER_DELAY_LOOP 2
// set up 3 second delay
#define DELAY  3000 * 1000 * (INS_PER_US / INS_PER_DELAY_LOOP)

// mapping some fixed registers to named variables
// this enables readibility
.struct Variables
	;; Some convenient constants. 32 bit values cannot be given as
	;; immediate, so we have to store them in registers.
	.u32 gpio_3_read
	.u32 gpio_1_read
	.u32 gpio_3_write
	.u32 gpio_1_write

	.u32 ringbuffer_size
	.u32 item_size

	.u32 start_sync_after	; time after which we should start sync.

	;; Variables used.
	.u32 gpio_out3	   ; Stuff we write out GPIO. Bits for polygon + laser
	.u32 gpio_out1	   ; Stuff we write out to GPIO. Bits step/dir/enable

	.u32 global_time	; our cycle time.

	.u32 polygon_time
	.u32 wait_countdown	; countdown used in states  for certain states to finish
	.u32 hsync_time		; time when we have seen the hsync
	.u32 last_hsync_time
	.u32 sync_laser_on_time


	.u32 item_start	   ; Start position of current item in ringbuffer
	.u32 item_pos		; position within item.

	.u16 state		; Current state machine state.
	.u8  bit_loop		; bit loop
	.u8  last_hsync_bit	; so that we can trigger on an edge
.ends
.assign Variables, r10, r27, v
// registers
// r1 .. r9 : common use
// r10 ... named variables



START:
    LBCO r0, C4, 4, 4					// Load Bytes Constant Offset (?)
    CLR  r0, r0, 4						// Clear bit 4 in reg 0
    SBCO r0, C4, 4, 4					// Store Bytes Constant Offset

// Populate some constants
    MOV v.gpio_3_read, GPIO_3_BASE | GPIO_DATAIN
    MOV v.gpio_3_write, GPIO_3_BASE | GPIO_DATAOUT

// TODO replace constant
    MOV r1, 3 // pulse 3 times
BLINK:
// enable output
    MOV r2, (0xffffffff ^ (1<<GPIO_LASER_DATA))
    MOV r3, GPIO_3_BASE | GPIO_OE ; output enable
    SBBO r2, r3, 0, 4
//  set output to zero
    MOV v.gpio_out3, 0
// enable laser
    SET v.gpio_out3, GPIO_LASER_DATA  // laser on 
// GPIO out
    SBBO v.gpio_out3, v.gpio_3_write, 0, 4

    MOV r0, DELAY
DELAYON:
    SUB r0, r0, 1
    QBNE DELAYON, r0, 0

// enable laser
    CLR v.gpio_out3, GPIO_LASER_DATA  // laser off 
// GPIO out
    SBBO v.gpio_out3, v.gpio_3_write, 0, 4

    MOV r0, DELAY
DELAYOFF:
    SUB r0, r0, 1
    QBNE DELAYOFF, r0, 0
    SUB r1, r1, 1
    QBNE BLINK, r1, 0

    MOV R31.b0, PRU0_ARM_INTERRUPT+16   // Send notification to Host for program completion
HALT
