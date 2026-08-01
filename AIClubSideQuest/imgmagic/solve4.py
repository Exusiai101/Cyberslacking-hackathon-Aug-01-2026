import cv2
import numpy as np

img = cv2.imread("peacock_intercept.png", cv2.IMREAD_COLOR)

for c_idx, c_name in enumerate(["Blue", "Green", "Red"]):
    plane = (img[:, :, c_idx] & 1)
    
    col_sums = np.sum(plane, axis=0)
    row_sums = np.sum(plane, axis=1)
    
    # Expected sum
    expected_col = plane.shape[0] / 2
    expected_row = plane.shape[1] / 2
    
    max_col_dev = np.max(np.abs(col_sums - expected_col))
    max_row_dev = np.max(np.abs(row_sums - expected_row))
    
    print(f"{c_name} LSB - Max Col Deviation: {max_col_dev}, Max Row Deviation: {max_row_dev}")
    
    # Check other bit planes as well!
    for bit in range(1, 8):
        plane_bit = (img[:, :, c_idx] >> bit) & 1
        c_sums = np.sum(plane_bit, axis=0)
        r_sums = np.sum(plane_bit, axis=1)
        max_c_dev = np.max(np.abs(c_sums - expected_col))
        max_r_dev = np.max(np.abs(r_sums - expected_row))
        if max_c_dev > 100 or max_r_dev > 100:
            print(f"  Bit {bit} - Max Col Dev: {max_c_dev}, Max Row Dev: {max_r_dev}")

