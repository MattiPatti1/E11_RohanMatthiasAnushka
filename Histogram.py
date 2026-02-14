import pandas as pd
import matplotlib.pyplot as plt

data = pd.read_csv('test.csv', comment='#')

plt.figure(figsize=(10, 6))
plt.hist(data['pm25_standard'], bins=15)

plt.title('Distribution of Concentrations')
plt.xlabel('PM2.5 Concentration')
plt.ylabel('Frequency')
plt.grid(axis='y', alpha=0.75)

plt.show()
