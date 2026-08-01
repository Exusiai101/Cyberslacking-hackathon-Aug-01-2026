import cv2
import numpy as np

img = cv2.imread("peacock_intercept.png", cv2.IMREAD_COLOR)

def find_long_strings(bits, name):
    for offset in range(8):
        b = bits[offset:]
        length = len(b) - (len(b) % 8)
        b = b[:length]
        
        bytes_data = np.packbits(b)
        
        # Big Endian
        s = ""
        for byte in bytes_data:
            if 32 <= byte <= 126:
                s += chr(byte)
            else:
                if len(s) >= 12:
                    print(f"[{name} - Offset {offset}] {s}")
                s = ""
        if len(s) >= 12:
            print(f"[{name} - Offset {offset}] {s}")

find_long_strings(img.flatten() & 1, "LSB All Channels")
for i, c in enumerate(["Blue", "Green", "Red"]):
    find_long_strings(img[:,:,i].flatten() & 1, f"LSB {c}")

find_long_strings(img.transpose(1, 0, 2).flatten() & 1, "LSB All Channels (Col)")
for i, c in enumerate(["Blue", "Green", "Red"]):
    find_long_strings(img[:,:,i].T.flatten() & 1, f"LSB {c} (Col)")
