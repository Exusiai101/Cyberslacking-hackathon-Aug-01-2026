import cv2
import numpy as np

img = cv2.imread("peacock_intercept.png", cv2.IMREAD_COLOR)
b, g, r = cv2.split(img)

# Save the lower bits of the Blue channel, fully amplified
cv2.imwrite("blue_bit0.png", (b & 1) * 255)
cv2.imwrite("blue_bit1.png", ((b >> 1) & 1) * 255)
cv2.imwrite("blue_bit2.png", ((b >> 2) & 1) * 255)
cv2.imwrite("blue_bit3.png", ((b >> 3) & 1) * 255)

# Also try extracting just the remainder modulo small numbers
cv2.imwrite("blue_mod2.png", (b % 2) * 255)
cv2.imwrite("blue_mod4.png", (b % 4) * 85)
cv2.imwrite("blue_mod8.png", (b % 8) * 36)

# Histogram equalize the blue channel to see if it makes it pop
b_eq = cv2.equalizeHist(b)
cv2.imwrite("blue_eq.png", b_eq)

# Do the same for all channels just in case they are better separated this way
img_mod8 = (img % 8) * 32
cv2.imwrite("img_mod8.png", img_mod8)
