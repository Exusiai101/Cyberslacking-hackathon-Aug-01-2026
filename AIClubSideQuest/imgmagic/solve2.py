import cv2
import numpy as np
import string

img = cv2.imread("peacock_intercept.png", cv2.IMREAD_COLOR)

def find_ascii(bits, name):
    print(f"\n--- Checking {name} ---")
    # Check all 8 offsets
    for offset in range(8):
        # We need to take a multiple of 8 bits after the offset
        b = bits[offset:]
        # Trim to multiple of 8
        length = len(b) - (len(b) % 8)
        b = b[:length]
        
        bytes_data = np.packbits(b)
        
        # also try little endian packbits
        # bytes_data_le = np.packbits(b, bitorder='little')
        
        for data, endian in [(bytes_data, "Big Endian")]:
            # Find contiguous printable characters
            s = ""
            for byte in data:
                if 32 <= byte <= 126:
                    s += chr(byte)
                else:
                    if len(s) >= 9:
                        print(f"Offset {offset}, {endian}: {s}")
                    s = ""
            if len(s) >= 9:
                print(f"Offset {offset}, {endian}: {s}")

# Method 1: All channels, flatten
find_ascii(img.flatten() & 1, "LSB All Channels (flatten)")

# Method 2: Per channel
b, g, r = cv2.split(img)
find_ascii(b.flatten() & 1, "LSB Blue Channel")
find_ascii(g.flatten() & 1, "LSB Green Channel")
find_ascii(r.flatten() & 1, "LSB Red Channel")

# What about column major instead of row major?
find_ascii(img.transpose(1, 0, 2).flatten() & 1, "LSB All Channels (Col Major)")
find_ascii(b.T.flatten() & 1, "LSB Blue Channel (Col Major)")
find_ascii(g.T.flatten() & 1, "LSB Green Channel (Col Major)")
find_ascii(r.T.flatten() & 1, "LSB Red Channel (Col Major)")

