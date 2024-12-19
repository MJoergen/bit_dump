#!/usr/bin/env python3

# This decodes an FPGA bitstream from AMD/Xilinx, based on ug470_7Series_Config,
# Chapter 5 "Configuration Details".

from typing import List
import sys

OPCODE_STR = ["NOP", "READ", "WRITE", "RESERVED"]
ADDR_STR   = ["CRC     ", "FAR     ", "FDRI    ", "FDRO    ", "CMD     ", "CTL0    ", "MASK    ", "STAT    ",
              "LOUT    ", "COR0    ", "MFWR    ", "CBC     ", "IDCODE  ", "AXSS    ", "COR1    ", "--------",
              "WBSTAR  ", "TIMER   ", "--------", "RBCRC_SW", "--------", "--------", "BOOTSTS ", "--------",
              "CTL1    ", "--------", "--------", "--------", "--------", "--------", "--------", "BSPI    "]
CMD_STR    = ["NULL     ", "WCFG     ", "MFW      ", "DGHIGH   ", "RCFG     ", "START    ", "RCAP     ", "RCRC     ",
              "AGHIGH   ", "SWITCH   ", "GRESTORE ", "SHUTDOWN ", "GCAPTURE ", "DESYNC   ", "---------", "IPROG    ",
              "CRCC     ", "LTIMER   ", "BSPI_READ", "FALL_EDGE"]

def get_bits(val:int, left:int, right:int):
    return (val >> right) & ((2 << (left-right))-1)

def decode_single_word(opcode_str: str, addr: int, arg: bytes):
    addr_str = ADDR_STR[addr]
    data_int = (arg[0] << 24) + (arg[1] << 16) + (arg[2] << 8) + arg[3]
    if addr == 4 and data_int < 24:
        # CMD
        cmd_str = CMD_STR[data_int]
        print(f"Type 1: {opcode_str} {addr_str} {cmd_str}")
    elif addr == 1:
        # FAR
        s = f"Type 1: {opcode_str} {addr_str} "
        s += f"BLOCK_TYPE({get_bits(data_int, 25, 23)}) "
        s += f"BOTTOM({    get_bits(data_int, 22, 22)}) "
        s += f"ROW({       get_bits(data_int, 21, 17)}) "
        s += f"COLUMN({    get_bits(data_int, 16,  7)}) "
        s += f"MINOR({     get_bits(data_int,  6,  0)}) "
        print(s)
    elif addr == 5:
        # CTL0
        s = f"Type 1: {opcode_str} {addr_str} "
        s += f"EFUSE_KEY({  get_bits(data_int, 31, 31)}) "
        s += f"ICAP_SELECT({get_bits(data_int, 30, 30)}) "
        s += f"OVERTEMP({   get_bits(data_int, 12, 12)}) "
        s += f"FALLBACK({   get_bits(data_int, 10, 10)}) "
        s += f"GLUTMASK_B({ get_bits(data_int,  8,  8)}) "
        s += f"FARSRC({     get_bits(data_int,  7,  7)}) "
        s += f"DEC({        get_bits(data_int,  6,  6)}) "
        s += f"SBITS({      get_bits(data_int,  5,  4)}) "
        s += f"PERSIST({    get_bits(data_int,  3,  3)}) "
        s += f"GTS_USR_B({  get_bits(data_int,  0,  0)}) "
        print(s)
    elif addr == 9:
        # COR0
        s = f"Type 1: {opcode_str} {addr_str} "
        s += f"PWRDWN_STAT({get_bits(data_int, 27, 27)}) "
        s += f"DONE_PIPE({  get_bits(data_int, 25, 25)}) "
        s += f"DRIVE_DONE({ get_bits(data_int, 24, 24)}) "
        s += f"SINGLE({     get_bits(data_int, 23, 23)}) "
        s += f"OSCFSEL({    get_bits(data_int, 22, 17)}) "
        s += f"SSCLKSRC({   get_bits(data_int, 16, 15)}) "
        s += f"DONE_CYCLE({ get_bits(data_int, 14, 12)}) "
        s += f"MATCH_CYCLE({get_bits(data_int, 11,  9)}) "
        s += f"LOCK_CYCLE({ get_bits(data_int,  8,  6)}) "
        s += f"GTS_CYCLE({  get_bits(data_int,  5,  3)}) "
        s += f"GWE_CYCLE({  get_bits(data_int,  2,  0)}) "
        print(s)
    elif addr == 14:
        # COR1
        s = f"Type 1: {opcode_str} {addr_str} "
        s += f"PERSIST({      get_bits(data_int, 17, 17)}) "
        s += f"RBCRC_ACTION({ get_bits(data_int, 16, 15)}) "
        s += f"RBCRC_NO_PIN({ get_bits(data_int,  9,  9)}) "
        s += f"RBCRC_EN({     get_bits(data_int,  8,  8)}) "
        s += f"BPI_1ST({      get_bits(data_int,  3,  2)}) "
        s += f"BPI_PAGE_SIZE({get_bits(data_int,  1,  0)}) "
        print(s)
    else:
        print(f"Type 1: {opcode_str} {addr_str} {arg.hex()}")

def main(args: List[str]):
    with open(args[0], 'rb') as f:
        data = f.read()
    for idx in range(len(data)-4):
        if data[idx:idx+4] == b'\xaa\x99\x55\x66':
            # Found sync word
            break
    else:
        print("Sync word not found")
        sys.exit(-1)
    idx += 4
    while idx <= len(data)-4:
        d = data[idx:idx+4]
        if d[0] & 0xE0 == 0x20:
            opcode = (d[0] >> 3) & 3
            opcode_str = OPCODE_STR[opcode]
            addr = ((d[1] & 3) << 3) + ((d[2] >> 5) & 0x7)
            addr_str = ADDR_STR[addr]
            wordcount = ((d[2] & 7) << 8) + d[3]
            if opcode != 0:
                print(d.hex(), end=' ')
                if wordcount == 0:
                    print(f"Type 1: {opcode_str} {addr_str}")
                elif wordcount == 1:
                    decode_single_word(opcode_str, addr, data[idx+4:idx+8])
                else:
                    print(f"Type 1: {opcode_str} {addr_str} {wordcount} words")
            idx += wordcount*4
        elif d[0] & 0xE0 == 0x40:
            wordcount = ((d[0] & 7) << 24) + (d[1] << 16) + (d[2] << 8) + d[3]
            print(d.hex(), end=' ')
            print(f"Type 2, wordcount={wordcount}")
            idx += wordcount*4
        else:
            print(d.hex(), end=' ')
            print("INVALID Type")
            sys.exit(-1)
        idx += 4



if __name__ == "__main__":
    main(sys.argv[1:])

