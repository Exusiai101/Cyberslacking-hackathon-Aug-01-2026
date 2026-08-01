import cv2
import numpy as np

img = cv2.imread("peacock_intercept.png", cv2.IMREAD_COLOR)
b, g, r = cv2.split(img)

# Save LSB planes for B, G, R
cv2.imwrite("b_lsb.png", (b & 1) * 255)
cv2.imwrite("g_lsb.png", (g & 1) * 255)
cv2.imwrite("r_lsb.png", (r & 1) * 255)

# Also maybe bit 1
cv2.imwrite("b_bit1.png", ((b >> 1) & 1) * 255)
cv2.imwrite("g_bit1.png", ((g >> 1) & 1) * 255)
cv2.imwrite("r_bit1.png", ((r >> 1) & 1) * 255)

# All channels LSB combined (could be useful if it's grayscale text hidden in LSB)
cv2.imwrite("rgb_lsb.png", (img & 1) * 255)
