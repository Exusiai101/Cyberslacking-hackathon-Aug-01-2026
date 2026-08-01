import cv2
import numpy as np

img = cv2.imread("peacock_intercept.png", cv2.IMREAD_COLOR)

def try_decode(bits, name):
    bytes_data = np.packbits(bits)
    s = ""
    for b in bytes_data:
        if 32 <= b <= 126:
            s += chr(b)
        else:
            s += "."
    
    if len(s) > 0 and s.count(".") < len(s) * 0.8:  # if at least 20% printable
        print(f"[{name}] {s[:100]}")

# 1 bit per row (first pixel)
try_decode(img[:, 0, 0] & 1, "Row LSB Blue")
try_decode(img[:, 0, 1] & 1, "Row LSB Green")
try_decode(img[:, 0, 2] & 1, "Row LSB Red")

# 1 bit per column (first row)
try_decode(img[0, :, 0] & 1, "Col LSB Blue")
try_decode(img[0, :, 1] & 1, "Col LSB Green")
try_decode(img[0, :, 2] & 1, "Col LSB Red")

# 1 bit per diagonal
min_dim = min(img.shape[0], img.shape[1])
diag_pixels = img[np.arange(min_dim), np.arange(min_dim)]
try_decode(diag_pixels[:, 0] & 1, "Diag LSB Blue")
try_decode(diag_pixels[:, 1] & 1, "Diag LSB Green")
try_decode(diag_pixels[:, 2] & 1, "Diag LSB Red")

# Center row?
mid_row = img.shape[0] // 2
try_decode(img[mid_row, :, 0] & 1, "Mid Row LSB Blue")

