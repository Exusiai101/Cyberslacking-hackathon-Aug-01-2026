import cv2
import numpy as np

img = cv2.imread("peacock_intercept.png", cv2.IMREAD_COLOR)
b, g, r = cv2.split(img)

# Print missing values in each channel
missing_b = [i for i in range(256) if np.sum(b == i) == 0]
missing_g = [i for i in range(256) if np.sum(g == i) == 0]
missing_r = [i for i in range(256) if np.sum(r == i) == 0]

print(f"Missing B: {missing_b}")
print(f"Missing G: {missing_g}")
print(f"Missing R: {missing_r}")
