# scripts/final_analysis.py

import pandas as pd
from pathlib import Path
from scipy.stats import ttest_ind
import numpy as np

def analyze_creativity_data(data_path: Path):
    """
    Loads, cleans, processes, and analyzes the creativity survey data.
    This version includes a data cleaning step to remove incomplete responses.
    """
    if not data_path.exists():
        print(f"Error: Data file not found at {data_path}")
        return

    df = pd.read_csv(data_path, skiprows=[1, 2])

    # --- 1. Data Cleaning Step ---
    # Define the IDs of incomplete responses to remove.
    # R_1Lq9U4e6GYOblJF: Answered no rating questions.
    # R_7dEogB7kEaGRZvT: Skipped 5 questions in the second block.
    # R_6rJcG07hgMZEwTM: Skipped the entire second block.
    ids_to_remove = ['R_1Lq9U4e6GYOblJF', 'R_7dEogB7kEaGRZvT', 'R_6rJcG07hgMZEwTM']
    
    # Filter the DataFrame, keeping only the complete responses.
    original_rows = len(df)
    df = df[~df['ResponseId'].isin(ids_to_remove)]
    print(f"--- Data Cleaning ---")
    print(f"Removed {original_rows - len(df)} incomplete survey entries. Analyzing {len(df)} remaining entries.\n")

    # --- 2. Define Image Source Maps ---
    # These maps correctly identify which image is Human vs. AI for each set.
    source_map_A = {'1':{'1':'human','2':'ai'}, '2':{'1':'ai','2':'human'}, '3':{'1':'ai','2':'human'}, '4':{'1':'human','2':'ai'}, '5':{'1':'human','2':'ai'}}
    source_map_B = {'1':{'1':'human','2':'ai'}, '2':{'1':'human','2':'ai'}, '3':{'1':'ai','2':'human'}, '4':{'1':'ai','2':'human'}, '5':{'1':'human','2':'ai'}}

    # --- 3. Process Data and Categorize Scores ---
    scores = {"unlabeled_human": [], "unlabeled_ai": [], "labeled_human": [], "labeled_ai": []}

    for _, row in df.iterrows():
        is_version1 = not pd.isnull(row['AU1_1'])
        is_version2 = not pd.isnull(row['BU1_1'])

        for i in range(1, 6):
            pair_num = str(i)
            if is_version1: # Unlabeled A, Labeled B
                scores[f"unlabeled_{source_map_A[pair_num]['1']}"].append(row[f'AU{i}_1'])
                scores[f"unlabeled_{source_map_A[pair_num]['2']}"].append(row[f'AU{i}_2'])
                scores[f"labeled_{source_map_B[pair_num]['1']}"].append(row[f'BL{i}_1'])
                scores[f"labeled_{source_map_B[pair_num]['2']}"].append(row[f'BL{i}_2'])
            elif is_version2: # Unlabeled B, Labeled A
                scores[f"unlabeled_{source_map_B[pair_num]['1']}"].append(row[f'BU{i}_1'])
                scores[f"unlabeled_{source_map_B[pair_num]['2']}"].append(row[f'BU{i}_2'])
                scores[f"labeled_{source_map_A[pair_num]['1']}"].append(row[f'AL{i}_1'])
                scores[f"labeled_{source_map_A[pair_num]['2']}"].append(row[f'AL{i}_2'])

    # Remove any remaining missing values (NaNs) from the lists.
    for key, value in scores.items():
        scores[key] = [item for item in value if not pd.isnull(item)]

    # --- 4. Calculate and Print Descriptive Statistics ---
    print("--- Descriptive Statistics (Cleaned Data) ---")
    for group_name, data in scores.items():
        print(f"{group_name.replace('_', ' ').title()}:")
        print(f"  Mean Rating = {np.mean(data):.2f}")
        print(f"  Standard Deviation = {np.std(data, ddof=1):.2f}")
        print(f"  Number of Ratings (n) = {len(data)}\n")

    # --- 5. Calculate and Print Statistical Significance Tests ---
    print("\n--- Statistical Significance Tests (t-tests) (Cleaned Data) ---")
    
    def perform_and_print_ttest(g1_name, g2_name, data):
        g1, g2 = data[g1_name], data[g2_name]
        # Use Welch's t-test, which does not assume equal variance.
        stat, p_value = ttest_ind(g1, g2, equal_var=False)
        print(f"Comparison: {g1_name.replace('_', ' ').title()} vs. {g2_name.replace('_', ' ').title()}")
        print(f"  t-statistic = {stat:.3f}")
        print(f"  p-value = {p_value:.4f}")
        print(f"  Result: The difference is {'statistically significant' if p_value < 0.05 else 'not statistically significant'}.\n")

    perform_and_print_ttest("unlabeled_human", "unlabeled_ai", scores)
    perform_and_print_ttest("unlabeled_ai", "labeled_ai", scores)
    perform_and_print_ttest("unlabeled_human", "labeled_human", scores)

if __name__ == "__main__":
    # Define the path to the data file relative to the script's location.
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "data"
    file_path = DATA_DIR / "Creativity Project_November 12, 2025_13.09.csv"
    
    if file_path.exists():
        analyze_creativity_data(file_path)
    else:
        print(f"Error: File not found at the expected path: {file_path}")