import cv2
import numpy as np
import string

img = cv2.imread("peacock_intercept.png", cv2.IMREAD_COLOR)

valid_chars = set(bytearray(string.ascii_letters + string.digits, 'ascii'))

def find_text_in_pixels(arr, name):
    # arr is 1D uint8 array
    # find sequences of 9+ valid chars
    count = 0
    s = ""
    for v in arr:
        if v in valid_chars:
            s += chr(v)
        else:
            if len(s) >= 9:
                print(f"[{name}] {s}")
            s = ""
    if len(s) >= 9:
        print(f"[{name}] {s}")

find_text_in_pixels(img.flatten(), "Flat RGB")
find_text_in_pixels(img[:,:,0].flatten(), "Blue")
find_text_in_pixels(img[:,:,1].flatten(), "Green")
find_text_in_pixels(img[:,:,2].flatten(), "Red")

# Check rows? (already covered by flatten)
# Check columns?
find_text_in_pixels(img.transpose(1, 0, 2).flatten(), "Flat RGB Col")
