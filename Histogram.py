import numpy as np
import matplotlib
%matplotlib inline
import matplotlib.pyplot as plt
plt.style.use('fivethirtyeight')

data = read.csv('test.csv')
plt.figure(fig_size(10,6))
plt.hist(data['PM Standard'], bins=15, colors='sky blue') 

plt.title('Distribution of Concentrations') 
plt.xlabel('PM2.5 Concentration') 
plt.ylabel('Frequency') 
plt.grid(axis='y', alpha ='0.75')
plt.show 
