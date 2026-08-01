import cv2
import numpy as np

img = cv2.imread("peacock_intercept.png", cv2.IMREAD_COLOR)

def check_magic(bits, name):
    bytes_data = np.packbits(bits)
    hex_str = bytes_data[:16].tobytes().hex().upper()
    print(f"{name} (Big Endian): {hex_str[:8]}... ({hex_str})")
    
    bytes_le = np.packbits(bits, bitorder='little')
    hex_le = bytes_le[:16].tobytes().hex().upper()
    print(f"{name} (Little Endian): {hex_le[:8]}... ({hex_le})")

b, g, r = cv2.split(img)

check_magic(img.flatten() & 1, "All (BGR)")
check_magic(np.stack((r, g, b), axis=-1).flatten() & 1, "All (RGB)")

check_magic(b.flatten() & 1, "Blue")
check_magic(g.flatten() & 1, "Green")
check_magic(r.flatten() & 1, "Red")

# Check column major
check_magic(img.transpose(1, 0, 2).flatten() & 1, "All (BGR) Col-Major")

# Check Bit 1 as well?
check_magic((img.flatten() >> 1) & 1, "All (BGR) Bit 1")
