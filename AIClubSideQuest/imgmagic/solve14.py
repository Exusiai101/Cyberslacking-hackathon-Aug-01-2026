import cv2
import numpy as np

img = cv2.imread("peacock_intercept.png", cv2.IMREAD_COLOR)
row_sums = np.sum(img, axis=(1, 2)) % 256
s = ""
for val in row_sums[:200]:
    if 32 <= val <= 126:
        s += chr(val)
    else:
        s += "."
print("Row sums mod 256:", s)

col_sums = np.sum(img, axis=(0, 2)) % 256
s = ""
for val in col_sums[:200]:
    if 32 <= val <= 126:
        s += chr(val)
    else:
        s += "."
print("Col sums mod 256:", s)
