import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

files = {
    'Original': 'Week11FiestaWare_Original.csv',
    'Al2':      'Week11FiestaWareAl2.csv',
    'Al3':      'Week11FiestaWareAl3.csv',
    'Tungsten1':       'Week11FiestaWareTungsten1.csv',
    'Tungsten2':       'Week11FiestaWareTungsten2.csv',
    'Tungsten3':       'Week11FiestaWareTungsten3.csv',
}

# Thicknesses in mm
al_thickness = {'Original': 0, 'Al2': 2, 'Al3': 3}
w_thickness  = {'Original': 0, 'W1': 10, 'W2': 20, 'W3': 30}

def get_total_counts(filepath):
    df = pd.read_csv(filepath, header=None, names=['timestamp', 'cumulative'])
    return df['cumulative'].iloc[-1] - df['cumulative'].iloc[0]

counts = {}
for name, filepath in files.items():
    counts[name] = get_total_counts(filepath)

for name, c in counts.items():
    print(f"{name}: {c:.0f} counts")


def get_intervals(filepath):
    df = pd.read_csv(filepath, header=None, names=['timestamp', 'cumulative'])
    return df['cumulative'].diff().dropna()

fig, ax = plt.subplots(figsize=(8, 5))

for name, filepath in files.items():
    intervals = get_intervals(filepath)
    mu = intervals.mean()
    sigma = intervals.std()
    theoretical_sigma = np.sqrt(mu)
    ax.hist(intervals, alpha=0.5, label=f"{name} (μ={mu:.1f}, σ={sigma:.1f}, √μ={theoretical_sigma:.1f})", bins=6)

ax.set_xlabel("Counts per interval")
ax.set_ylabel("Frequency")
ax.set_title("Histogram of counts per interval — all measurements")
ax.legend(fontsize=7)
plt.tight_layout()
plt.show()

#Part 1analysis: The standard deviation and mean are close for all the measurements, shows that the data follows Poisson counting statisitcs.
#The general trend is that the counts per interval decrease as absorber thickness increases, which is what is to be expected with more mateirals meaning more attenuation.

#Part 2: As absorber thickness increases, the mean counts per interval decrease, which aligns with the attentuation of radiation through material. 

