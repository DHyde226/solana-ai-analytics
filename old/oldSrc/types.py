import pandas as pd

# --- CONFIGURE THIS ---
file_path = "global_transactions.csv"   # change to your file name
column_name = "type"         # name of the column to inspect
# ------------------------

# Read the CSV file
df = pd.read_csv(file_path)

# Get all unique values from the column
unique_types = df[column_name].dropna().unique()

# Print them nicely
print(f"Unique values in column '{column_name}':")
for val in unique_types:
    print("-", val)

print(f"\nTotal unique types: {len(unique_types)}")
