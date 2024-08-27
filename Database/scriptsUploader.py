import os
import pandas as pd
from pymongo import MongoClient

# MongoDB connection string
mongo_uri = "mongodb+srv://SupremeRahul:***REDACTED***@clusternse.wpf8cel.mongodb.net/"
client = MongoClient(mongo_uri)
db = client['AlgoTrading']
collection = db['dassss']

# Path to the directory containing the CSV file
csv_directory = "D:\\AlgoDividend\\Database\\"
csv_file = 'EQT1.csv'  # Handling one CSV file with 6000+ documents

# Read the CSV file into a DataFrame
file_path = os.path.join(csv_directory, csv_file)
df = pd.read_csv(file_path)

# Create 'symbol' field by adjusting 'Security Id' as needed
df['symbol'] = df['Security Id'].apply(lambda x: x.replace('#', '-EQ') if x.endswith('#') else x + '-EQ')

# Convert DataFrame to a list of dictionaries
data = df.to_dict(orient='records')

# Insert data into MongoDB
collection.insert_many(data)

print("Data uploaded successfully.")
