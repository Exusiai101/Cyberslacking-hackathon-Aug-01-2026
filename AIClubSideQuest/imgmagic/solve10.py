import cv2
import numpy as np

img = cv2.imread("peacock_intercept.png", cv2.IMREAD_COLOR)

# 1. Grayscale Equalization
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
gray_eq = cv2.equalizeHist(gray)
cv2.imwrite("gray_eq.png", gray_eq)

# 2. HSV Equalization
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
hsv[:, :, 2] = cv2.equalizeHist(hsv[:, :, 2])
color_eq = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
cv2.imwrite("color_eq.png", color_eq)

# 3. Contrast Stretching (just multiply)
# If the hidden text is in the lower bits, we can just shift them up
img_shifted = img << 4 # Shift left by 4 bits
cv2.imwrite("img_shifted.png", img_shifted)

# 4. Difference between adjacent pixels (Edge detection / Gradient)
diff_x = cv2.absdiff(img[:, 1:], img[:, :-1])
cv2.imwrite("diff_x.png", diff_x * 10) # Multiply by 10 to make it visible
