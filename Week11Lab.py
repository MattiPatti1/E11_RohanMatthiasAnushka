import sys
import time
import numpy as np
import matplotlib.pyplot as plt
import csv

# 1. Setup path and imports
sys.path.append('/home/pi/cape_mca') # capemca.py directory [cite: 24]
from capemca import *

# 2. Check input arguments [cite: 29]
if len(sys.argv) < 4:
    print("Usage: python script.py <duration> <window> <output_file>")
    sys.exit(1)

devices = find_all_mcas()
print(f"Found {len(devices)} MCA device(s)")
if not devices:
    sys.exit(1)

duration = float(sys.argv[1])
window = float(sys.argv[2])
output_file_path = sys.argv[3]

# 3. Open file and create writer 
file = open(output_file_path, 'w', newline='')
csvwriter = csv.writer(file, delimiter=',')
csvwriter.writerow(['Elapsed_Time', 'Total_Counts', 'CPS']) # Add a header

spectra = []
read_times = []

with CapeMCA() as mca:
    try:
        start = time.time()
        reads = 0
        next_read = start
        
        while time.time() - start < duration:
            now = time.time()
            if now < next_read:
                time.sleep(next_read - now)
                
            read_start = time.time()
            status = mca.read_status()
            spectrum = mca.read_spectrum()
            read_end = time.time()
            
            next_read = read_start + window
            elapsed = read_start - start
            
            # Saves elapsed time, total counts, and CPS as required 
            csvwriter.writerow([f"{elapsed:.2f}", status.total_count, status.cps])
            file.flush() # Forces the data to save immediately
            
            # Printing to screen as required 
            print(f"[{elapsed:6.1f}s] read {reads+1}: {status.cps} cps, totalCount={status.total_count:g}")
            
            spec_data = spectrum[1:]
            spectra.append(spec_data)
            read_times.append(elapsed)
            reads += 1
            
        print(f"\nCompleted {reads} reads.")
        
    except Exception as e:
        print(f"\nError: {e}")

# Close the file at the very end
file.close()
print(f"Data saved to {output_file_path}. Device closed, exiting.")

# (Your plotting code below remains the same...)
