#%% Step 1

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

labels = [
    "pm1_standard", "pm25_standard", "pm10_standard",
    "Temperature", "Gas", "Humidity", "Pressure", "Altitude"
]

INSIDE_FILE = "data/Week5Data_Inside.csv"
OUTSIDE_FILE = "data/Week5Data_Outside.csv"

OUTDOOR_OFFSET_SECONDS = 30 # Walking from the lab to outside took approx 30s

### 1.1 Comparing inside and Outside Data

inside_df = pd.read_csv(INSIDE_FILE)
outside_df = pd.read_csv(OUTSIDE_FILE)

inside_data = inside_df.iloc[2:].reset_index(drop=True)

outside_data = outside_df.iloc[2 + OUTDOOR_OFFSET_SECONDS:].reset_index(drop=True)

min_length = min(len(inside_data), len(outside_data))
inside_data = inside_data.iloc[:min_length]
outside_data = outside_data.iloc[:min_length]

### 1.2

for label in labels:
    
    if label not in inside_data.columns or label not in outside_data.columns:
        continue

    in_vals = inside_data[label].dropna()
    out_vals = outside_data[label].dropna()

    mean_in = np.mean(in_vals)
    std_in = np.std(in_vals, ddof=1)

    mean_out = np.mean(out_vals)
    std_out = np.std(out_vals, ddof=1)

    unc_in = std_in / np.sqrt(len(in_vals))
    unc_out = std_out / np.sqrt(len(out_vals))

    combined_unc = np.sqrt(unc_in**2 + unc_out**2)
    sigma_sep = abs(mean_in - mean_out) / combined_unc

    print(f"{label} ")
    print(f"Inside:  {mean_in:.2f} +/- {unc_in:.2f}  (std = {std_in:.2f})")
    print(f"Outside: {mean_out:.2f} +/- {unc_out:.2f}  (std = {std_out:.2f})")
    print(f"Separation: {sigma_sep:.2f} sigma")


### 1.3

    plt.figure(figsize=(8,4))

    min_val = min(in_vals.min(), out_vals.min())
    max_val = max(in_vals.max(), out_vals.max())
    bins = np.linspace(min_val, max_val, 30)

    plt.hist(in_vals, bins=bins, alpha=0.5, label="Inside")
    plt.hist(out_vals, bins=bins, alpha=0.5, label="Outside")

    plt.title(f"{label}: Indoor vs Outdoor ({sigma_sep:.2f}σ)")
    plt.xlabel(label)
    plt.ylabel("Frequency")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()

    print("For the most part, the data deviates from Gaussian Distributions. Some of the particulate matter data exhibit normal behavior with a central peak and somewhat symmetric tails. However most of the PM data is heavy skewed, reflecting clean air conditions as those values rarley rose above noise. Some data, like prussure remained nearly constant through the entire time span. As the dataset conatins significantly more than 30 data points we can use the Central Limit Theroem. ")


#%% Step 2


#%% Step 3 Comparing to a third location near a vent
VENT_FILE = "data/Week6Data_Vent.csv"

### 3.1 
vent_df = pd.read_csv(VENT_FILE)
vent_data = vent_df.iloc[1:].reset_index(drop=True)

min_length = min(len(outside_data), len(vent_data))
outside_data = outside_data.iloc[:min_length]
vent_data = vent_data.iloc[:min_length]

for label in labels:
    
    if label not in outside_data.columns or label not in vent_data.columns:
        continue

    out_vals = outside_data[label].dropna()
    vent_vals = vent_data[label].dropna()
    mean_out = np.mean(out_vals)
    std_out = np.std(out_vals, ddof=1)
    mean_vent = np.mean(vent_vals)
    std_vent = np.std(vent_vals, ddof=1)
    unc_out = std_out / np.sqrt(len(out_vals))
    unc_vent = std_vent / np.sqrt(len(vent_vals))

    combined_unc = np.sqrt(unc_out**2 + unc_vent**2)
    sigma_sep = abs(mean_out - mean_vent) / combined_unc

    print(f"{label}")
    print(f"Normal Outside: {mean_out:.2f} +/- {unc_out:.2f}  (std = {std_out:.2f})")
    print(f"Vent Location:  {mean_vent:.2f} +/- {unc_vent:.2f}  (std = {std_vent:.2f})")
    print(f"Separation: {sigma_sep:.2f} sigma")


### 3.3 
    plt.figure(figsize=(8,4))

    min_val = min(out_vals.min(), vent_vals.min())
    max_val = max(out_vals.max(), vent_vals.max())
    bins = np.linspace(min_val, max_val, 30)

    plt.hist(out_vals, bins=bins, alpha=0.5, label="Normal Outside")
    plt.hist(vent_vals, bins=bins, alpha=0.5, label="Vent Location")

    plt.title(f"{label}: Outside vs Vent ({sigma_sep:.2f}σ)")
    plt.xlabel(label)
    plt.ylabel("Frequency")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()
