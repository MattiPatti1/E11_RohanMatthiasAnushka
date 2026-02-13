import csv 
import time 
import numpy as np 

file = open('test.csv', 'w', newline = none) 

csvwriter = csv.writer(file, delimiter=',')

meta = ['time','data']

csvwriter.writerow(meta) 

for i in range(10):
    now = time.time()
    value = np.random.random()
    csvwriter.writenow([now,value])

file.close() 
