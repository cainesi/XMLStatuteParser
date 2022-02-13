// Copyright (C) 2022  Ian Caines
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

//library of c-functions used by the xml statute parser

#include<stdio.h>
#include<stdlib.h>

//macros for bitfield manipulation
#include <limits.h>		/* for CHAR_BIT */
#define BITMASK(b) (1 << ((b) % CHAR_BIT))
#define BITSLOT(b) ((b) / CHAR_BIT)
#define BITSET(a, b) ((a)[BITSLOT(b)] |= BITMASK(b))
#define BITCLEAR(a, b) ((a)[BITSLOT(b)] &= ~BITMASK(b))
#define BITTEST(a, b) ((a)[BITSLOT(b)] & BITMASK(b))
#define BITNSLOTS(nb) ((nb + CHAR_BIT - 1) / CHAR_BIT)

int linesplit(char *src, int src_n,int *tokenStart, int *tokenEnd, void *numTokens) {
    //Function to split a unicode string into pieces by commas, ignoring commas appearing inside quote marks.
    //Fills in the provided tokenStart/tokenEnd with the start and end points (in unicode) of the tokens, and writes the total number of tokens to numTokens.

    //special unicode characters that this function needs to recognize
    //comma - 002C
    //double quotes - unicode 0022
    //double left 201C - ignored for now
    //double right 201D - ignored for now
    //french left 00AB - ignored for now
    //french right 00BB - ignored for now
    //check top bytes first: (assume little-endian)
  
    int tokenCnt = 0;
    int lastTokenStart = 0;
    int inQuotes = 0;
    int *tmp;
    int c;
    int ptr;
    for(c = 0; c < src_n; c++){ //iterate over (unicode) elements of the source string
        ptr = c * 4; // byte position of the unicode element we're looking at.

        if (src[ptr+3] != 0 || src[ptr+2] != 0) { continue; }
        if (src[ptr+1] != 0) { continue;}
        if (src[ptr] == 0x22) {// quotation mark
            inQuotes ^= 1;
        }
        else if (src[ptr] == 0x2c) {
            if (inQuotes) {continue;} // ignore comma in quotation mark
            tokenStart[tokenCnt] = lastTokenStart;
            tokenEnd[tokenCnt] = c;
            lastTokenStart = c + 1;
            tokenCnt += 1;
        }
    }
    //add on a final token, for the text following the last comma
    tokenStart[tokenCnt] = lastTokenStart;
    tokenEnd[tokenCnt] = c;
    tokenCnt += 1;
    tmp = (int *) numTokens;
    *tmp = tokenCnt;
    return 0;
}