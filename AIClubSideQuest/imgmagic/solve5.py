import cv2
import numpy as np

img = cv2.imread("peacock_intercept.png", cv2.IMREAD_COLOR)

# Extract first 1000 pixels
flat_pixels = img.reshape(-1, 3)[:1000]

# Try different parities
parities_sum = np.sum(flat_pixels, axis=1) & 1
parities_xor = (flat_pixels[:, 0] ^ flat_pixels[:, 1] ^ flat_pixels[:, 2]) & 1

def decode_bits(bits, name):
    # Pack into bytes
    b = np.packbits(bits)
    s = ""
    for val in b:
        if 32 <= val <= 126:
            s += chr(val)
        else:
            s += "."
    print(f"{name} (8-bit): {s}")
    
    # 7-bit
    s7 = ""
    for i in range(0, len(bits) - 7, 7):
        val = 0
        for bit in bits[i:i+7]:
            val = (val << 1) | bit
        if 32 <= val <= 126:
            s7 += chr(val)
        else:
            s7 += "."
    print(f"{name} (7-bit): {s7}")

decode_bits(parities_sum, "Sum Parity")
decode_bits(parities_xor, "XOR Parity")
