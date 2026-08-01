with open("peacock_intercept.png", "rb") as f:
    f.read(8) # signature
    while True:
        length_bytes = f.read(4)
        if not length_bytes: break
        length = int.from_bytes(length_bytes, 'big')
        chunk_type = f.read(4).decode('ascii', errors='replace')
        print(f"Chunk: {chunk_type}, length: {length}")
        f.read(length) # skip data
        f.read(4) # skip crc
