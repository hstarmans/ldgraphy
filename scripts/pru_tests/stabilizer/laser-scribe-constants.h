/* -*- mode: c++; c-basic-offset: 4; indent-tabs-mode: nil; -*-
 * (c) 2017 Henner Zeller <h.zeller@acm.org>
 *
 * This file is part of LDGraphy http://github.com/hzeller/ldgraphy
 *
 * LDGraphy is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * LDGraphy is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with LDGraphy.  If not, see <http://www.gnu.org/licenses/>.
 */
#ifndef LASER_SCRIBE_CONSTANTS_H
#define LASER_SCRIBE_CONSTANTS_H

// Command list
#define CMD_EMPTY              0
#define CMD_SCAN_DATA          1
#define CMD_SCAN_DATA_NO_SLED  2
#define CMD_EXIT               3
#define CMD_DONE               4

// Error list
#define ERROR_NONE         0
#define ERROR_DEBUG_BREAK  1  // For debugging 'breakpoints'
#define ERROR_MIRROR_SYNC  2  // Mirror failed to sync.
#define ERROR_TIME_OVERRUN 3  // state machine did not finish within TICK_DELAY


#define CPU_SPEED  200000000       // Hz  PRU is 200 MHz
#define TICK_DELAY 500            // CPU cycles between each loop         


// Each mirror segment is this number of pixel ticks long (only the first
// 8*SCANLINE_DATA_SIZE are filled with pixels, the rest is dead part of the
// segment).

#define TICKS_PER_MIRROR_SEGMENT 2500
#define JITTER_ALLOW TICKS_PER_MIRROR_SEGMENT/400
#define TICKS_START 875 // start exposure at 20 percent
#define FACETS 4

// The data per segment is sent in a bit-array. 
#define SCANLINE_HEADER_SIZE 1   // A single byte containing the command.
#define SCANLINE_DATA_SIZE 171   
#define SCANLINE_ITEM_SIZE (SCANLINE_HEADER_SIZE + SCANLINE_DATA_SIZE)
#define QUEUE_LEN 8
#define ERROR_RESULT_POS 0       // byte 0 = error
#define SYNC_FAIL_POS   1        // byte 1-4 = sync fails
#define START_RINGBUFFER 5       // byte 5 ... lines


#define SPINUP_TICKS 600000 // 1.5 seconds

#define MAX_WAIT_STABLE_TICKS 450000 // 1.125 seconds, laser on waiting for sync error if expires
#define END_OF_DATA_WAIT_TICKS 300000 // 0.75 seconds, no data in time reset to idle, +1 sync fail

#endif // LASER_SCRIBE_CONSTANTS_H
