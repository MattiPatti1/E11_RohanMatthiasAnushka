import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

inside  = pd.read_csv('/Users/anushkaghorpade/Downloads/Week5Data_Inside.csv',  parse_dates=['timestamp'])
outside = pd.read_csv('/Users/anushkaghorpade/Downloads/Week5Data_Outside.csv', parse_dates=['timestamp'])

inside  = inside.iloc[1:].reset_index(drop=True)
outside = outside.iloc[1:].reset_index(drop=True)

sensor_cols = [
    ('Temperature',   'Temperature (°C)'),
    ('Humidity',      'Humidity (%)'),
    ('Pressure',      'Pressure (hPa)'),
    ('Gas',           'Gas Resistance (Ω)'),
    ('pm1_standard',  'PM1.0 (µg/m³)'),
    ('pm25_standard', 'PM2.5 (µg/m³)'),
    ('pm10_standard', 'PM10 (µg/m³)'),
]

#Part 1 

fig, axes = plt.subplots(len(sensor_cols), 1, figsize=(12, 4 * len(sensor_cols)))
fig.suptitle('Sensor Readings — Time Series', fontsize=16)

for ax, (col, label) in zip(axes, sensor_cols):
    ax.plot(inside['timestamp'],  inside[col],  label='Inside',  color='steelblue')
    ax.plot(outside['timestamp'], outside[col], label='Outside', color='tomato')
    ax.set_ylabel(label)
    ax.set_xlabel('Time')
    ax.legend()
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

#Part 2
fig, axes = plt.subplots(len(sensor_cols), 1, figsize=(10, 4 * len(sensor_cols)))
fig.suptitle('Histograms — Inside vs Outside', fontsize=16)

for ax, (col, label) in zip(axes, sensor_cols):
    ax.hist(inside[col],  bins=30, alpha=0.55, label='Inside',  color='steelblue', edgecolor='white')
    ax.hist(outside[col], bins=30, alpha=0.55, label='Outside', color='tomato',    edgecolor='white')
    ax.set_xlabel(label)
    ax.set_ylabel('Count')
    ax.legend()
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

#Part 3

print(f"\n{'Sensor':<18} {'Mean_In':>10} {'Mean_Out':>10} {'σ_mean_In':>12} {'σ_mean_Out':>12} {'Separation':>12} {'>3σ?':>7}")
print('-' * 90)

for col, label in sensor_cols:
    vi = inside[col].dropna()
    vo = outside[col].dropna()

    mean_in,  mean_out  = vi.mean(), vo.mean()
    sigma_mean_in  = vi.std() / np.sqrt(len(vi))
    sigma_mean_out = vo.std() / np.sqrt(len(vo))

    sigma_diff = np.sqrt(sigma_mean_in**2 + sigma_mean_out**2)
    separation = abs(mean_in - mean_out) / sigma_diff if sigma_diff > 0 else np.inf

    flag = 'YES' if separation > 3 else 'NO'
    print(f"{label:<18} {mean_in:>10.3f} {mean_out:>10.3f} {sigma_mean_in:>12.5f} {sigma_mean_out:>12.5f} {separation:>12.2f} {flag:>7}")
