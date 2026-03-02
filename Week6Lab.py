# ==========================================
# PART 1: Setup & Indoor vs Outdoor Analysis
# ==========================================

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# --- Configuration ---
labels = [
    "pm1_standard", "pm25_standard", "pm10_standard",
    "Temperature", "Gas", "Humidity", "Pressure", "Altitude"
]

INSIDE_FILE = "data/Week5Data_Inside.csv"
OUTSIDE_FILE = "data/Week5Data_Outside.csv"
OUTDOOR_OFFSET_SECONDS = 30   # Remove first 30 seconds of travel time

# --- Helper Functions ---

def load_and_slice(file, skip_rows=2, offset=0, match_length=None):
    """Loads CSV, skips startup noise, cuts offset, and matches length."""
    df = pd.read_csv(file)
    # Skip startup rows (usually first 2)
    df = df.iloc[skip_rows:].reset_index(drop=True)

    # Apply offset (e.g. for outside travel time)
    if offset > 0:
        df = df.iloc[offset:].reset_index(drop=True)

    # Cut to match the length of the other dataset if needed
    if match_length:
        df = df.iloc[:match_length]

    return df

def compute_stats(vals):
    """Returns Mean, Std Dev, and Uncertainty (Standard Error)."""
    mean = np.mean(vals)
    std = np.std(vals, ddof=1)
    mean_unc = std / np.sqrt(len(vals))
    return mean, std, mean_unc

def sigma_separation(m1, u1, m2, u2):
    """Calculates Sigma Separation."""
    # Avoid division by zero
    combined_unc = np.sqrt(u1**2 + u2**2)
    if combined_unc == 0:
        return 0
    return abs(m1 - m2) / combined_unc

def plot_histogram(vals1, vals2, label1, label2, quantity, sigma):
    """Generates the Histogram Plot."""
    plt.figure(figsize=(8,4))

    min_val = min(vals1.min(), vals2.min())
    max_val = max(vals1.max(), vals2.max())
    
    # Handle case where data is flat (all zeros)
    if min_val == max_val:
        bins = np.linspace(min_val - 0.5, max_val + 0.5, 30)
    else:
        bins = np.linspace(min_val, max_val, 30)

    plt.hist(vals1, bins=bins, alpha=0.5, label=label1, color='red')
    plt.hist(vals2, bins=bins, alpha=0.5, label=label2, color='blue')

    plt.title(f"{quantity}: {label1} vs {label2} ({sigma:.2f}σ)")
    plt.xlabel(quantity)
    plt.ylabel("Frequency")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.show()

def compare_datasets(df1, df2, name1, name2, step_name):
    """Loops through labels and compares two datasets."""
    print(f"\n================ {step_name} ================\n")

    for label in labels:
        if label not in df1.columns or label not in df2.columns:
            continue

        vals1 = df1[label].dropna()
        vals2 = df2[label].dropna()
        
        if len(vals1) == 0 or len(vals2) == 0:
            continue

        m1, s1, u1 = compute_stats(vals1)
        m2, s2, u2 = compute_stats(vals2)

        sigma = sigma_separation(m1, u1, m2, u2)

        print(f"--- {label} ---")
        print(f"{name1}: {m1:.2f} ± {u1:.2f}")
        print(f"{name2}: {m2:.2f} ± {u2:.2f}")
        print(f"Separation: {sigma:.2f} sigma")

        plot_histogram(vals1, vals2, name1, name2, label, sigma)

# --- EXECUTION: Part 1 ---

# 1. Load Data
inside_data = load_and_slice(INSIDE_FILE, skip_rows=2)
outside_data = load_and_slice(
    OUTSIDE_FILE,
    skip_rows=2,
    offset=OUTDOOR_OFFSET_SECONDS,
    match_length=len(inside_data)
)

# 2. Run Comparison
compare_datasets(
    inside_data,
    outside_data,
    "Inside",
    "Outside",
    "STEP 1: Indoor vs Outdoor"
)