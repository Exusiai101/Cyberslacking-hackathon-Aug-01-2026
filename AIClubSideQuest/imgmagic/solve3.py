import cv2
import numpy as np

img = cv2.imread("peacock_intercept.png", cv2.IMREAD_COLOR)
flat = img.flatten()

# Get the first 1000 LSBs
lsbs = flat[:1000] & 1

# Try to group by 8
bytes_arr = np.packbits(lsbs)
s = ""
for b in bytes_arr:
    if 32 <= b <= 126:
        s += chr(b)
    else:
        s += "."
print("Flat LSBs packed as bytes (8 bits):", s)

# Try group by 7 (ASCII is 7-bit)
s7 = ""
for i in range(0, len(lsbs) - 7, 7):
    bits = lsbs[i:i+7]
    val = 0
    for bit in bits:
        val = (val << 1) | bit
    if 32 <= val <= 126:
        s7 += chr(val)
    else:
        s7 += "."
print("Flat LSBs packed as bytes (7 bits big endian):", s7)

s7_le = ""
for i in range(0, len(lsbs) - 7, 7):
    bits = lsbs[i:i+7]
    val = 0
    for j, bit in enumerate(bits):
        val |= (bit << j)
    if 32 <= val <= 126:
        s7_le += chr(val)
    else:
        s7_le += "."
print("Flat LSBs packed as bytes (7 bits little endian):", s7_le)

# Print the actual LSBs of the first few pixels to see if there's a pattern
print("First 100 LSBs:", "".join(map(str, lsbs[:100])))
