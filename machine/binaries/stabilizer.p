;; -*- asm -*-
;;
;; (c) 2017 Henner Zeller <h.zeller@acm.org>
;;
;; This file is part of LDGraphy. http://github.com/hzeller/ldgraphy
;;
;; LDGraphy is free software: you can redistribute it and/or modify
;; it under the terms of the GNU General Public License as published by
;; the Free Software Foundation, either version 3 of the License, or
;; (at your option) any later version.
;;
;; LDGraphy is distributed in the hope that it will be useful,
;; but WITHOUT ANY WARRANTY; without even the implied warranty of
;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
;; GNU General Public License for more details.
;;
;; You should have received a copy of the GNU General Public License
;; along with LDGraphy.  If not, see <http://www.gnu.org/licenses/>.


#include "laser-scribe-constants.h"

.origin 0
.entrypoint INIT

#define PRU0_ARM_INTERRUPT 19
#define CONST_PRUDRAM	   C24


#define PRUSS_PRU_CTL      0x22000
#define CYCLE_COUNTER_OFFSET  0x0C


// Mapping some fixed registers to named variables.
// We have enough registers to keep things readable.
.struct Variables
	;; Some convenient constants. 32 bit values cannot be given as
	;; immediate, so we have to store them in registers.
	.u32 ringbuffer_size
	.u32 item_size

	.u32 start_sync_after	; time after which we should start sync.

	;; Variables used.
	.u32 global_time	; our cycle time.

	.u32 polygon_time
	.u32 wait_countdown	; countdown used in states  for certain states to finish
	.u32 hsync_time		; time when we have seen the hsync
	.u32 last_hsync_time
	.u32 sync_laser_on_time


	.u32 item_start	        ; Start position of current item in ringbuffer
	.u32 item_pos		; position within item.
	.u32 sync_fails         ; number of lines failed to sync

	.u16 state		; Current state machine state.
	.u8  bit_loop		; bit loop
	.u8  last_hsync_bit	; so that we can trigger on an edge
.ends
.assign Variables, r10, r22, v

;; Registers
;; r1 ... r9 : common use
;; r10 ... named variables

.macro branch_if_not_between
.mparam to_label, value, min_cmp, max_cmp
	MOV r5, min_cmp
	MOV r6, max_cmp
	QBLT to_label, r5, value
	QBGT to_label, r6, value
.endm


// the laser just finishing the fluorescencing hsync block. Electrically
// the rising edge after we have been low for a bit (while laser is over block).
// Reading from r31
.macro branch_if_hsync
.mparam to_label
	QBBS bit_is_set, r31, 16 	       ; direct PRU input
	QBEQ no_hsync, v.last_hsync_bit, 1 ; we are only interested in 0->1 edge
	MOV v.last_hsync_bit, 1
	MOV v.hsync_time, v.global_time 
	JMP to_label
bit_is_set:
	MOV v.last_hsync_bit, 0
no_hsync:
.endm

// Using cpu cycle counter instead of IEP, so that we have
// an easier time to transfer that to a simpler processor later.
.macro start_cpu_cycle_counter
	MOV r5, PRUSS_PRU_CTL

	LBBO r6, r5, 0, 4
	CLR r6, 3		; bit 3: disable
	SBBO r6, r5, 0, 4

	MOV r7, 0
	SBBO r7, r5, CYCLE_COUNTER_OFFSET, 4 ; reset

	SET r6, 3		; bit 3: enable
	SBBO r6, r5, 0, 4
.endm

.macro wait_to_next_tick_and_reset
.mparam value
	MOV r7, PRUSS_PRU_CTL
	; Reading this register takes 4 cpu cycles. So we read it and
	; then do the remaining time with a busy loop.
	LBBO r9, r7, CYCLE_COUNTER_OFFSET, 4 ; get current counter
	MOV r8, (value - 10)		     ; account for some overhead
	QBGT REPORT_ERROR_TIME_OVERRUN, r8, r9 ; Error. Optimize state machine!
	SUB r9, r8, r9			     ; remaining CPU cycles
	QBGE end_loop, r9, 1		     ; if (i <= 1) goto end_loop
wait_loop:                                   ; do {
	SUB r9, r9, 2                        ;   i-=2;  // loop takes two cycles
	QBLT wait_loop, r9, 1		     ; } while (i > 1)

end_loop:
	QBEQ reset_cycle, r9, 0	       ; already at zero ?
	MOV r9, 0		       ; othewise we have to waste another cycle
reset_cycle:
	;; in any case, r9 is zero now.
	SBBO r9, r7, CYCLE_COUNTER_OFFSET, 4 ; reset
.endm

INIT:
	;; Clear STANDBY_INIT in SYSCFG register.
	LBCO r0, C4, 4, 4
	CLR r0, r0, 4
	SBCO r0, C4, 4, 4

	;; Populate some constants
	MOV v.item_size, SCANLINE_ITEM_SIZE
	MOV v.ringbuffer_size, SCANLINE_ITEM_SIZE * QUEUE_LEN

	;; switch the laser full on at this period so that we reliably hit the
	;; hsync sensor.
	MOV v.start_sync_after, TICKS_PER_MIRROR_SEGMENT - JITTER_ALLOW - 1

	;; Set GPIO bits to writable. Output bits need to be set to 0.

	MOV v.item_start, START_RINGBUFFER         ; command byte position in DRAM
	MOV v.state, STATE_IDLE
	MOV v.sync_fails, 0

	start_cpu_cycle_counter

MAIN_LOOP:
	LBCO r1.b0, CONST_PRUDRAM, v.item_start, 1 ; read header
	QBEQ FINISH, r1.b0, CMD_EXIT		       ; react to exit immediately
	JMP v.state								   ; switch/case with direct jump :)


	;; Each of these states must not use more than TICK_DELAY steps

	;; Waiting for Data to arrive
STATE_IDLE:
	QBEQ FINISH, r1.b0, CMD_EXIT
	QBEQ MAIN_LOOP_NEXT, r1.b0, CMD_EMPTY
	MOV v.global_time, 0	                    ; have monotone increasing time for 1h or so
	MOV v.wait_countdown, SPINUP_TICKS
	MOV v.last_hsync_time, 0
	MOV v.polygon_time, 0
	MOV v.state, STATE_SPINUP
	MOV v.sync_laser_on_time, 0

	;; prepare data
	MOV v.item_pos, SCANLINE_HEADER_SIZE 		; Start after header
	MOV v.bit_loop, 7  

	JMP MAIN_LOOP_NEXT

	;; Spinup. The mirror takes a second or so until it is ready,
	;; dont switch on the laser quite yet.
STATE_SPINUP:
	SUB v.wait_countdown, v.wait_countdown, 1
	QBEQ spinup_done, v.wait_countdown, 0
	JMP MAIN_LOOP_NEXT
spinup_done:
	SET r30.t7	                                ; laser pwm1 on
	SET r30.t5                                  ; laser pwm2 on 
	MOV v.wait_countdown, MAX_WAIT_STABLE_TICKS
	MOV v.state, STATE_WAIT_STABLE
	JMP MAIN_LOOP_NEXT

	;; Switch on the laser the full time and wait until we get it within
	;; some acceptable margin. Sometimes, mirrors have a harder time
	;; synchronizing in the beginning. We wait until we are stable.
STATE_WAIT_STABLE:
	;; If we are too long waiting for a sync, assume there is an issue
	;; with the laser not properly rotating or no feedback.
	SUB v.wait_countdown, v.wait_countdown, 1
	QBEQ REPORT_ERROR_MIRROR, v.wait_countdown, 0
	QBLT MAIN_LOOP_NEXT, v.sync_laser_on_time, v.global_time
	SET r30.t6     ; laser pwm1 on
	SET r30.t5     ; laser pwm2 on
	branch_if_hsync wait_stable_hsync_seen
	JMP MAIN_LOOP_NEXT	; todo: account for cpu-cycles
wait_stable_hsync_seen:
	SUB r1, v.hsync_time, v.last_hsync_time
	MOV v.last_hsync_time, v.hsync_time 
	CLR r30.t7     ; laser pwm1 off
	CLR r30.t5     ; laser pwm2 off
	/* zeller used something different but this didn't work with all motors */
	ADD v.sync_laser_on_time, v.hsync_time, v.start_sync_after ; laser on then
	branch_if_not_between wait_stable_not_synced_yet, r1, TICKS_PER_MIRROR_SEGMENT-JITTER_THRESH, TICKS_PER_MIRROR_SEGMENT+JITTER_THRESH
	MOV v.state, STATE_CONFIRM_STABLE
	JMP MAIN_LOOP_NEXT

wait_stable_not_synced_yet:
	JMP MAIN_LOOP_NEXT

	;; We got synchronization and know when it is time to switch on
	;; the laser to get the next synchronization. Lets see if we can repeat
	;; this.
STATE_CONFIRM_STABLE:
	QBLT MAIN_LOOP_NEXT, v.sync_laser_on_time, v.global_time
	SET r30.t7    ; laser pwm1 on
	SET r30.t5    ; laser pwm2 on
confirm_stable_test_for_hsync:
	branch_if_hsync confirm_stable_hsync_seen
	JMP MAIN_LOOP_NEXT
confirm_stable_hsync_seen:
	CLR r30.t7 ; hsync finished, laser pwm1 off
	CLR r30.t5 ; laser pwm2 off
	ADD v.sync_laser_on_time, v.hsync_time, v.start_sync_after
	/* todo: test if in between expected range, otherwise state wait stable 
	         zeller went straight to data run but I want it to pass the facet filter */
	JMP active_data_wait

	;; Sync step between data lines.
STATE_DATA_WAIT_FOR_SYNC:
	QBLT MAIN_LOOP_NEXT, v.sync_laser_on_time, v.global_time ; not yet
	;; Now we are close enough to the hsync-block, switch on the laser.
	SET r30.t7     ; laser pwm1 on
	SET r30.t5     ; laser pwm2 on
wait_for_sync:
	branch_if_hsync wait_for_sync_hsync_seen
	JMP MAIN_LOOP_NEXT
wait_for_sync_hsync_seen:
	CLR r30.t7 ; hsync finished, laser pwm1 off
	CLR r30.t5 ; laser pwm2 off
	/* calculate hsync_time to enable binning TODO: code clone! */
	SUB r4, v.hsync_time, v.last_hsync_time  
	MOV v.last_hsync_time, v.hsync_time
	ADD v.sync_laser_on_time, v.hsync_time, v.start_sync_after
	/* TODO: this only works for MVP demonstrator model 1
	         if it is the the outlier continue else go back to STATE_DATA_WAIT_FOR_SYNC */
	; for testing
	;JMP active_data_wait
	;MOV r5, 25015
	;QBLT active_data_wait, r5, r4

	;; we step at the end of a data line, so here we should reset.
	CLR r30.t14  ; y-step

	MOV v.state, STATE_WAIT_FOR_DATA_RUN
	MOV v.wait_countdown, 0
	JMP MAIN_LOOP_NEXT

STATE_WAIT_FOR_DATA_RUN:
	ADD v.wait_countdown, v.wait_countdown, 1
	MOV r1, TICKS_START
	QBLT MAIN_LOOP_NEXT, r1, v.wait_countdown
	MOV v.state, STATE_DATA_RUN
	JMP MAIN_LOOP_NEXT

	;; Loop to send all the data. We go through each byte, and within that
	;; through each bit, once per state.
STATE_DATA_RUN:
	MOV r1, v.item_size
	QBLT data_run_data_output, r1, v.item_pos
	MOV v.state, STATE_ADVANCE_RINGBUFFER
	JMP MAIN_LOOP_NEXT
data_run_data_output:
	;; super lazy, we read the full byte every time, this needs
	;; to be optimized.
	MOV r2, v.item_start
	ADD r2, r2, v.item_pos
	LBCO r1.b0, CONST_PRUDRAM, r2, 1

	QBBS data_laser_set_on, r1.b0, v.bit_loop
	CLR r30.t7 ; laser pwm1 off
	CLR r30.t5 ; laser pwm2 off
	JMP data_laser_set_done
data_laser_set_on:
	SET r30.t7 ; laser pwm1 on
	SET r30.t5 ; laser pwm2 on
data_laser_set_done:

	QBEQ data_run_next_byte, v.bit_loop, 0
	SUB v.bit_loop, v.bit_loop, 1
	JMP MAIN_LOOP_NEXT
data_run_next_byte:
	ADD v.item_pos, v.item_pos, 1
	MOV v.bit_loop, 7 
	JMP MAIN_LOOP_NEXT

	;;  not really necessary to be its own state.
STATE_ADVANCE_RINGBUFFER:
	CLR r30.t7 ; laser pwm1 off
	CLR r30.t5 ; laser pwm2 off

	;; check if we need to advance stepper
	LBCO r1.b0, CONST_PRUDRAM, v.item_start, 1
	QBEQ advance_sled_done, r1.b0, CMD_SCAN_DATA_NO_SLED
	SET r30.t14  ; y-step
advance_sled_done:
	;; signal host that we are done with this item.
	MOV r1.b0, CMD_EMPTY
	SBCO r1.b0, CONST_PRUDRAM, v.item_start, 1
	MOV R31.b0, PRU0_ARM_INTERRUPT+16 ; tell that status changed.

	ADD v.item_start, v.item_start, v.item_size ; advance in ringbuffer
	QBLT rb_advanced, v.ringbuffer_size, v.item_start ; item_start < rb_sizes
	MOV v.item_start, START_RINGBUFFER	; Wrap around
rb_advanced:
	MOV v.wait_countdown, END_OF_DATA_WAIT_TICKS
	MOV v.state, STATE_AWAIT_MORE_DATA
	JMP MAIN_LOOP_NEXT

STATE_AWAIT_MORE_DATA:
	SUB v.wait_countdown, v.wait_countdown, 1
	QBNE active_data_wait, v.wait_countdown, 0
	;; ok, we waited too long, let us switch off motors and go back
	;; to idle.
	MOV r1, 1000000 ; random just some upper limit to prevent overflow
	QBLT ringbufferreset, r1, v.sync_fails 
	ADD v.sync_fails, v.sync_fails, 1
ringbufferreset:
	MOV v.state, STATE_IDLE
	JMP MAIN_LOOP_NEXT

active_data_wait:
	LBCO r1.b0, CONST_PRUDRAM, v.item_start, 1 ; read header
	QBEQ FINISH, r1.b0, CMD_EXIT
	QBEQ MAIN_LOOP_NEXT, r1.b0, CMD_EMPTY

	MOV v.item_pos, SCANLINE_HEADER_SIZE 		; Start after header
	MOV v.bit_loop, 7

	MOV v.state, STATE_DATA_WAIT_FOR_SYNC
	JMP MAIN_LOOP_NEXT

MAIN_LOOP_NEXT:
	;; The current state set whatever state it needed, now wait for the
	;; end of our period to execute the actions: set GPIO bits.
	wait_to_next_tick_and_reset TICK_DELAY
	;; XOR r30, r30, (1<<5)	; debug output

	;; Global time update. The global time wraps around after 1h or so
	;; but it is sufficient for the typical exposure times of a few minutes.
	ADD v.global_time, v.global_time, 1

	;; time for mirror toggle ?
	ADD v.polygon_time, v.polygon_time, 1
	MOV r1, (TICKS_PER_MIRROR_SEGMENT*FACETS/6)/2
	QBLT mirror_toggle_done, r1, v.polygon_time
	XOR r30, r30, (1<<2)
	MOV v.polygon_time, 0
mirror_toggle_done:

	;; GPIO out, once per loop.
	JMP MAIN_LOOP

FINISH:
	CLR r30.t7 ; laser pwm1 off
	CLR r30.t5 ; laser pwm0 off
	MOV r1, 0		; Switch off all GPIO bits.
	;; Tell host that we have seen the CMD_EXIT and acknowledge with CMD_DONE
	MOV r1.b0, CMD_DONE
	SBCO r1.b0, CONST_PRUDRAM, v.item_start, 1
	SBCO v.sync_fails, CONST_PRUDRAM, SYNC_FAIL_POS, 4
	HALT

REPORT_ERROR_MIRROR:
	MOV r1.b0, ERROR_MIRROR_SYNC
	JMP ERROR_SET_VALUE

REPORT_ERROR_TIME_OVERRUN:
	MOV r1.b0, ERROR_TIME_OVERRUN
	JMP ERROR_SET_VALUE

REPORT_DEBUG_BREAK:
	MOV r1.b0, ERROR_DEBUG_BREAK
	JMP ERROR_SET_VALUE

ERROR_SET_VALUE:
	SBCO r1.b0, CONST_PRUDRAM, ERROR_RESULT_POS, 1
	;; signal host that we are done, code waits for this 
	MOV R31.b0, PRU0_ARM_INTERRUPT+16 ; tell that status changed.
	JMP FINISH
