/* -*- mode: c++; c-basic-offset: 4; indent-tabs-mode: nil; -*-
 * (c) 2019 Rik Starmans  <info@hexastorm.com>
 * 
 * Removed constansts as they are loaded in via Python.
 *
 * (c) 2017 Henner Zeller <h.zeller@acm.org>
 *
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

// The data per segment is sent in a bit-array. 
#define SCANLINE_HEADER_SIZE 1   // A single byte containing the command.
#define ERROR_RESULT_POS     0   // byte 0 = error
#define START_RINGBUFFER     1   // byte 1 ... lines

#endif // LASER_SCRIBE_CONSTANTS_H
