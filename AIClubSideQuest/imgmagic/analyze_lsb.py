import cv2
import numpy as np

img = cv2.imread("peacock_intercept.png", cv2.IMREAD_COLOR)
b, g, r = cv2.split(img)

def analyze(plane, name):
    zeros = np.sum(plane == 0)
    ones = np.sum(plane == 1)
    print(f"{name}: 0s: {zeros}, 1s: {ones}, ratio: {ones/(zeros+ones):.4f}")

analyze(b & 1, "Blue LSB")
analyze(g & 1, "Green LSB")
analyze(r & 1, "Red LSB")
