import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

#Step 2: Comparing sensors

# Our data
inside  = pd.read_csv('/Users/anushkaghorpade/Downloads/Week5Data_Inside.csv',  parse_dates=['timestamp'])
outside = pd.read_csv('/Users/anushkaghorpade/Downloads/Week5Data_Outside.csv', parse_dates=['timestamp'])

inside  = inside.iloc[1:].reset_index(drop=True)
outside = outside.iloc[1:].reset_index(drop=True)

# Other group's data 
url_indoors  = "https://raw.githubusercontent.com/jack-nelson795/E11_Jack_James_Sam/refs/heads/main/Week4LabSubmission/air_weather_indoors.csv"
url_outdoors = "https://raw.githubusercontent.com/jack-nelson795/E11_Jack_James_Sam/refs/heads/main/air_weather_outdoors.csv"

their_inside  = pd.read_csv(url_indoors).iloc[1:].reset_index(drop=True)
their_outside = pd.read_csv(url_outdoors).iloc[1:].reset_index(drop=True)

print("Our inside rows:",    len(inside))
print("Our outside rows:",   len(outside))
print("Their inside rows:",  len(their_inside))
print("Their outside rows:", len(their_outside))

print("\nTheir columns:", their_inside.columns.tolist())

shared_cols = [
    ('Temperature',   'Tempreature',   'Temperature (°C)'),
    ('Humidity',      'Humidity',      'Humidity (%)'),
    ('Pressure',      'Pressure',      'Pressure (hPa)'),
    ('Gas',           'Gas',           'Gas Resistance (Ω)'),
    ('pm25_standard', 'pm25_standard', 'PM2.5 (µg/m³)'),
    ('pm10_standard', 'pm10_standard', 'PM10 (µg/m³)'),
]

def print_stats(label, vals_a, name_a, vals_b, name_b):
    mean_a, std_a, n_a = vals_a.mean(), vals_a.std(), len(vals_a)
    mean_b, std_b, n_b = vals_b.mean(), vals_b.std(), len(vals_b)
    sigma_mean_a = std_a / np.sqrt(n_a)
    sigma_mean_b = std_b / np.sqrt(n_b)
    sigma_diff   = np.sqrt(sigma_mean_a**2 + sigma_mean_b**2)
    separation   = abs(mean_a - mean_b) / sigma_diff if sigma_diff > 0 else np.inf

    print(f"\n  {label}")
    print(f"    {name_a:<20}  mean = {mean_a:.3f}  |  std = {std_a:.3f}  |  sigma_mean = {sigma_mean_a:.5f}")
    print(f"    {name_b:<20}  mean = {mean_b:.3f}  |  std = {std_b:.3f}  |  sigma_mean = {sigma_mean_b:.5f}")
    print(f"    Separation = {separation:.2f} sigma  -->  Statistically different at 3sigma? {'YES' if separation > 3 else 'NO'}")


# INSIDE COMPARISON: our inside vs their inside


print("INSIDE: Our sensors vs Their sensors")


fig, axes = plt.subplots(len(shared_cols), 1, figsize=(10, 4 * len(shared_cols)))
fig.suptitle('Inside Data — Our Sensors vs Their Sensors', fontsize=14)

for ax, (our_col, their_col, label) in zip(axes, shared_cols):
    ax.hist(inside[our_col],         bins=30, alpha=0.55, label='Our Inside',   color='steelblue', edgecolor='white')
    ax.hist(their_inside[their_col], bins=30, alpha=0.55, label='Their Inside', color='orchid',    edgecolor='white')
    ax.set_xlabel(label)
    ax.set_ylabel('Count')
    ax.legend()
    ax.grid(True, alpha=0.3)
    print_stats(label, inside[our_col], 'Our Inside', their_inside[their_col], 'Their Inside')

plt.tight_layout()
plt.show()

# OUTSIDE COMPARISON: our outside vs their outside


print("OUTSIDE: Our sensors vs Their sensors")


fig, axes = plt.subplots(len(shared_cols), 1, figsize=(10, 4 * len(shared_cols)))
fig.suptitle('Outside Data — Our Sensors vs Their Sensors', fontsize=14)

for ax, (our_col, their_col, label) in zip(axes, shared_cols):
    ax.hist(outside[our_col],         bins=30, alpha=0.55, label='Our Outside',   color='tomato',     edgecolor='white')
    ax.hist(their_outside[their_col], bins=30, alpha=0.55, label='Their Outside', color='darkorange', edgecolor='white')
    ax.set_xlabel(label)
    ax.set_ylabel('Count')
    ax.legend()
    ax.grid(True, alpha=0.3)
    print_stats(label, outside[our_col], 'Our Outside', their_outside[their_col], 'Their Outside')

plt.tight_layout()
plt.show()


#Step 4: Correlations in data

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

inside  = pd.read_csv('/Users/anushkaghorpade/Downloads/Week5Data_Inside.csv',  parse_dates=['timestamp'])
outside = pd.read_csv('/Users/anushkaghorpade/Downloads/Week5Data_Outside.csv', parse_dates=['timestamp'])
inside  = inside.iloc[1:].reset_index(drop=True)
outside = outside.iloc[1:].reset_index(drop=True)


df = pd.concat([inside, outside], ignore_index=True)


def scatter_with_correlation(ax, x, y, xlabel, ylabel, title, color='steelblue'):
    ax.scatter(x, y, alpha=0.4, s=10, color=color)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.3)

    # Pearson correlation
    r, p = stats.pearsonr(x.dropna(), y.dropna())
    ax.annotate(f'Pearson r = {r:.3f}', xy=(0.05, 0.92), xycoords='axes fraction', fontsize=10,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
    print(f"  {title}: Pearson r = {r:.3f}, p-value = {p:.3e}")

#Temperature vs Humidity
print("Temperature vs Humidity")
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle('Temperature vs Humidity', fontsize=14)

scatter_with_correlation(axes[0], inside['Temperature'],  inside['Humidity'],  'Temperature (°C)', 'Humidity (%)', 'Inside',  color='steelblue')
scatter_with_correlation(axes[1], outside['Temperature'], outside['Humidity'], 'Temperature (°C)', 'Humidity (%)', 'Outside', color='tomato')

plt.tight_layout()
plt.show()

#Temperature vs all other sensor properties
other_cols = [
    ('Pressure',      'Pressure (hPa)'),
    ('Gas',           'Gas Resistance (Ω)'),
    ('pm25_standard', 'PM2.5 (µg/m³)'),
    ('pm10_standard', 'PM10 (µg/m³)'),
    ('pm1_standard',  'PM1.0 (µg/m³)'),
]

print("\nTemperature vs Other Properties")
for col, label in other_cols:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle(f'Temperature vs {label}', fontsize=14)

    scatter_with_correlation(axes[0], inside['Temperature'],  inside[col],  'Temperature (°C)', label, 'Inside',  color='steelblue')
    scatter_with_correlation(axes[1], outside['Temperature'], outside[col], 'Temperature (°C)', label, 'Outside', color='tomato')
    plt.tight_layout()
    plt.show()

# Temperature vs PM2.5
print("\nTemperature vs PM2.5")
print("  Times match because both sensors were read in the same loop iteration,")
print("  so each row contains a temperature and PM2.5 reading from the same moment.")


fig, axes = plt.subplots(1, 2, figsize=(12, 5))
fig.suptitle('Temperature vs PM2.5 (same-time measurements)', fontsize=14)

scatter_with_correlation(axes[0], inside['Temperature'],  inside['pm25_standard'],  'Temperature (°C)', 'PM2.5 (µg/m³)', 'Inside',  color='steelblue')
scatter_with_correlation(axes[1], outside['Temperature'], outside['pm25_standard'], 'Temperature (°C)', 'PM2.5 (µg/m³)', 'Outside', color='tomato')

plt.tight_layout()
plt.show()
