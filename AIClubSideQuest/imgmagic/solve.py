import cv2
import numpy as np

img = cv2.imread("peacock_intercept.png", cv2.IMREAD_COLOR)

def extract_and_print(bits, name):
    bytes_data = np.packbits(bits)
    s = ""
    for b in bytes_data[:500]:
        if 32 <= b <= 126:
            s += chr(b)
        else:
            s += "."
    print(f"\n--- {name} ---")
    print(s[:200])
    
# Method 1: All channels, flatten
extract_and_print(img.flatten() & 1, "LSB All Channels")

# Method 2: Per channel
b, g, r = cv2.split(img)
extract_and_print(b.flatten() & 1, "LSB Blue Channel")
extract_and_print(g.flatten() & 1, "LSB Green Channel")
extract_and_print(r.flatten() & 1, "LSB Red Channel")

# Method 3: Top left to bottom right vs other ways?
# The flatten is row-major.

# Method 4: Pack bits with little endian?
def extract_and_print_le(bits, name):
    bytes_data = np.packbits(bits, bitorder='little')
    s = ""
    for b in bytes_data[:500]:
        if 32 <= b <= 126:
            s += chr(b)
        else:
            s += "."
    print(f"\n--- {name} (Little Endian) ---")
    print(s[:200])

extract_and_print_le(img.flatten() & 1, "LSB All Channels")
