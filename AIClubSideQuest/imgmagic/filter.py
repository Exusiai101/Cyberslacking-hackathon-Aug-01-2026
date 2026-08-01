import re
with open("output.txt") as f:
    lines = f.readlines()
    for line in lines:
        if "---" in line:
            print(line.strip())
            continue
        
        # split by ': ' to get the string part
        parts = line.split(": ", 1)
        if len(parts) == 2:
            s = parts[1].strip()
            if len(s) == 9 and s.isalnum():
                print(f"FOUND ALNUM 9: {line.strip()}")
            elif len(s) == 9:
                # also print if it's 9 chars long exactly just in case
                pass
            
            # Or if it contains a 9 char alnum string
            matches = re.findall(r'[a-zA-Z0-9]{9}', s)
            for m in matches:
                print(f"FOUND MATCH {m} in: {line.strip()}")
