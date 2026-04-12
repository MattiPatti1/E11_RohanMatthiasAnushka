import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

data_dir = os.getcwd() 
print("Looking for files in:", data_dir)

files = {
    'Original': os.path.join(data_dir, 'Week11FiestaWare.csv'),
    'Al1':      os.path.join(data_dir, 'Week11FiestaWareAl1.csv'),
    'Al2':      os.path.join(data_dir, 'Week11FiestaWareAl2.csv'),
    'Al3':      os.path.join(data_dir, 'Week11FiestaWareAl3.csv'),
    'Al4':      os.path.join(data_dir, 'Week11FiestaWareAl4.csv'),
    'W1':       os.path.join(data_dir, 'Week11FiestaWareTungsten1.csv'),
    'W2':       os.path.join(data_dir, 'Week11FiestaWareTungsten2.csv'),
    'W3':       os.path.join(data_dir, 'Week11FiestaWareTungsten3.csv'),
}

# Thicknesses in mm
al_thickness = {'Original': 0, 'Al1': 1, 'Al2': 2, 'Al3': 3, 'Al4': 4}
w_thickness  = {'Original': 0, 'W1': 10, 'W2': 20, 'W3': 30}

def get_intervals(filepath):
    df = pd.read_csv(filepath, header=None, names=['timestamp', 'cumulative'])
    df['cumulative'] = pd.to_numeric(df['cumulative'], errors='coerce')
    df = df.dropna()
    if df['cumulative'].is_monotonic_increasing:
        return df['cumulative'].diff().dropna()
    else:
        return df['cumulative']

def get_total_counts(filepath):
    df = pd.read_csv(filepath, header=None, names=['timestamp', 'cumulative'])
    df['cumulative'] = pd.to_numeric(df['cumulative'], errors='coerce')
    df = df.dropna()
    if df['cumulative'].is_monotonic_increasing:
        return df['cumulative'].iloc[-1] - df['cumulative'].iloc[0]
    else:
        return df['cumulative'].sum()

counts = {}
for name, filepath in files.items():
    counts[name] = get_total_counts(filepath)

for name, c in counts.items():
    print(f"{name}: {c:.0f} counts")


#histograms
def get_intervals(filepath):
    df = pd.read_csv(filepath, header=None, names=['timestamp', 'cumulative'])
    df['cumulative'] = pd.to_numeric(df['cumulative'], errors='coerce')
    df = df.dropna()
    if df['cumulative'].is_monotonic_increasing:
        return df['cumulative'].diff().dropna()
    else:
        return df['cumulative']

fig, ax = plt.subplots(figsize=(8, 5))

for name, filepath in files.items():
    intervals = get_intervals(filepath)
    mu = intervals.mean()
    sigma = intervals.std()
    theoretical_sigma = np.sqrt(mu)
    ax.hist(intervals, alpha=0.5, bins=6,
            label=f"{name} (μ={mu:.1f}, σ={sigma:.1f}, √μ={theoretical_sigma:.1f})")

ax.set_xlabel("Counts per interval")
ax.set_ylabel("Frequency")
ax.set_title("Histogram of counts per interval — all measurements")
ax.legend(fontsize=7)
plt.tight_layout()
plt.show()

#Part 1analysis: The standard deviation and mean are close for all the measurements, shows that the data follows Poisson counting statisitcs.
#The general trend is that the counts per interval decrease as absorber thickness increases, which is what is to be expected with more mateirals meaning more attenuation.

#Part 2: As absorber thickness increases, the mean counts per interval decrease, which aligns with the attentuation of radiation through material. 

#Total counts vs absorber thickness

al_counts = {
    0:  counts['Original'],
    1:  counts['Al1'],
    2:  counts['Al2'],
    3:  counts['Al3'],
    4:  counts['Al4'],
}

w_counts = {
    0:  counts['Original'],
    10: counts['W1'],
    20: counts['W2'],
    30: counts['W3'],
}

al_x = np.array(list(al_counts.keys()))
al_y = np.array(list(al_counts.values()))
al_err = np.sqrt(al_y)

w_x = np.array(list(w_counts.keys()))
w_y = np.array(list(w_counts.values()))
w_err = np.sqrt(w_y)

fig, ax = plt.subplots(figsize=(8, 5))

ax.errorbar(al_x, al_y, yerr=al_err, fmt='o-', label='Aluminum (mm)', capsize=5)
ax.errorbar(w_x,  w_y,  yerr=w_err,  fmt='s-', label='Tungsten (mm)',  capsize=5)

ax.set_yscale('log')
ax.set_xlabel('Absorber thickness (mm)')
ax.set_ylabel('Total counts (log scale)')
ax.set_title('Total counts vs absorber thickness')
ax.legend()
plt.tight_layout()
plt.show()

#Step4

# Aluminum
al_x_arr = np.array([0, 1, 2, 3, 4])
al_y_arr = np.array([counts['Original'], counts['Al1'], counts['Al2'], counts['Al3'], counts['Al4']])

# Tungsten
w_x_arr = np.array([0, 10, 20, 30])
w_y_arr = np.array([counts['Original'], counts['W1'], counts['W2'], counts['W3']])

# Fit a line to ln(N) vs x
al_coeffs = np.polyfit(al_x_arr, np.log(al_y_arr), 1)
w_coeffs  = np.polyfit(w_x_arr,  np.log(w_y_arr),  1)

mu_al = -al_coeffs[0]  # slope = -mu
mu_w  = -w_coeffs[0]

print(f"Aluminum absorption coefficient:  mu = {mu_al:.4f} /mm")
print(f"Tungsten absorption coefficient:  mu = {mu_w:.4f} /mm")
print()
print(f"In /cm: mu_Al = {mu_al*10:.4f} /cm")
print(f"In /cm: mu_W  = {mu_w*10:.4f} /cm")


