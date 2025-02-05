import os
import pandas as pd

def json_to_excel(json_folder='C:/Users/adeshvijaya/pythonProject_56321/deploy/trades/Compiled', excel_file='C:/Users/adeshvijaya/pythonProject_56321/deploy/trades/combined_data.xlsx'):
    # Create an empty DataFrame to store the combined data
    combined_data = pd.DataFrame()

    # Loop through each JSON file in the specified folder
    for filename in os.listdir(json_folder):
        if filename.endswith('.json'):
            json_path = os.path.join(json_folder, filename)

            # Read JSON file into a DataFrame
            json_data = pd.read_json(json_path)

            # Append the data to the combined DataFrame
            combined_data = pd.concat([combined_data, json_data])

    # Write the combined data to an Excel file
    combined_data.to_excel(excel_file, index=False)

if __name__ == "__main__":
    json_to_excel()
