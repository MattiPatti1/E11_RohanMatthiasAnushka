import pandas as pd
import matplotlib.pyplot as plt
import csv
import time
import numpy as np
import sys

arguments = sys.argv
print(arguments)

data_path = arguments[1]
runtime = int(arguments[2])

file = open(data_path, 'w', newline=None)

csvwriter=csv.writer(file, delimiter = ',')

meta = ['time,' 'data']
csvwriter.writerow(meta)

for i in range(runtime):
    time.sleep(1)
    now = time.time()
    value = np.random.random()
    csvwriter.writerow([now,value])

file.close()

'''
data = pd.read_csv('test.csv', comment='#')

plt.figure(figsize=(10, 6))
plt.hist(data['pm25_standard'], bins=15)

plt.title('Distribution of Concentrations')
plt.xlabel('PM2.5 Concentration')
plt.ylabel('Frequency')
plt.grid(axis='y', alpha=0.75)

plt.show()
'''