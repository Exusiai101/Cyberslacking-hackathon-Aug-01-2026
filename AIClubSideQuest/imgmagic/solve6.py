import cv2
import numpy as np

img = cv2.imread("peacock_intercept.png", cv2.IMREAD_COLOR)

for c_idx, c_name in enumerate(["Blue", "Green", "Red"]):
    plane = img[:, :, c_idx] & 1
    
    # We can use cv2.boxFilter to compute the sum of 32x32 blocks!
    box_sum = cv2.boxFilter(plane.astype(np.float32), -1, (32, 32), normalize=False)
    
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(box_sum)
    print(f"{c_name} LSB 32x32 block sums - Min: {min_val} at {min_loc}, Max: {max_val} at {max_loc}")
