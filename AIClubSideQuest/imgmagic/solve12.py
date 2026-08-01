import cv2
import numpy as np

img = cv2.imread("peacock_intercept.png", cv2.IMREAD_COLOR)

# Median blur and subtract
blur = cv2.medianBlur(img, 7)
diff = cv2.absdiff(img, blur)

# Enhance the difference
enhanced = diff * 20
cv2.imwrite("diff_median.png", enhanced)

# Also check for a specific color!
# If the text was written with exactly RGB = (1, 1, 1) or something, 
# maybe it stands out in a specific color range?
# Let's write a script that finds the most frequent pixel differences
diff_flat = diff.reshape(-1, 3)
unique, counts = np.unique(diff_flat, axis=0, return_counts=True)
# sort by counts
sorted_idx = np.argsort(counts)
print("Most common absolute differences between original and median blur (B, G, R):")
for i in range(-1, -11, -1):
    print(f"{unique[sorted_idx[i]]}: {counts[sorted_idx[i]]} pixels")

