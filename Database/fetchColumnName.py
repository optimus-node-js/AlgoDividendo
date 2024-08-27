import pandas as pd
import os
# Path to the directory containing the CSV file
csv_directory = "D:\\AlgoDividend\\Database\\"
csv_file = 'EQT0.csv'  # Update the file name if needed

# Read the CSV file into a DataFrame
file_path = os.path.join(csv_directory, csv_file)
df = pd.read_csv(file_path)

# Print column names to identify the correct column
print(df.columns)
