# scripts/final_analysis.py

import pandas as pd
from pathlib import Path
from scipy.stats import ttest_ind, f_oneway
import numpy as np


def analyze_bias_by_demographics(processed_data):
    """
    Calculates a bias score for each participant and analyzes if this
    bias differs significantly across demographic groups.
    """
    print("\n--- Analysis of Bias Against Labeled AI Art ---")
    
    if not processed_data:
        print("No data available for bias analysis.")
        return

    df = pd.DataFrame(processed_data)
    
    # --- THIS IS THE FIX ---
    # Create the 'category' column before it is used in the groupby function.
    df['category'] = df['source'].str.title() + " (" + df['label_status'].str.title() + ")"

    # --- Step 1: Calculate average scores for each participant ---
    # This line will now work correctly.
    participant_avg_scores = df.groupby(['ResponseId', 'category'])['rating'].mean().unstack()

    # --- Step 2: Calculate the AI Bias Score ---
    if 'Ai (Unlabeled)' in participant_avg_scores.columns and 'Ai (Labeled)' in participant_avg_scores.columns:
        participant_avg_scores['AI_bias_score'] = participant_avg_scores['Ai (Unlabeled)'] - participant_avg_scores['Ai (Labeled)']
        participant_avg_scores.dropna(subset=['AI_bias_score'], inplace=True)
    else:
        print("Could not calculate AI Bias Score due to missing 'Ai (Unlabeled)' or 'Ai (Labeled)' data.")
        return

    # --- Step 3: Merge demographic data back in ---
    demographics_df = df.drop_duplicates(subset='ResponseId').set_index('ResponseId')
    bias_df = participant_avg_scores.join(demographics_df)

    # --- Step 4: Analyze the bias score across demographics ---
    age_map = {1: '18-24', 2: '25-34', 3: '35-44', 4: '45-54', 5: '55+'}
    gender_map = {1: 'Male', 2: 'Female', 3: 'Non-binary'}
    education_map = {1: 'High School', 2: 'Some College', 3: 'Bachelor\'s', 4: 'Master\'s', 5: 'Doctorate', 6: 'Other'}

    bias_df['age_group'] = bias_df['age'].map(age_map)
    bias_df['gender_label'] = bias_df['gender'].map(gender_map)
    bias_df['education_level'] = bias_df['education'].map(education_map)

    demographics_to_analyze = {
        "Artistic Experience": "art_experience",
        "AI Experience": "ai_experience",
        "Age Group": "age_group",
        "Education Level": "education_level"
    }

    for demo_title, demo_col in demographics_to_analyze.items():
        if demo_col in bias_df.columns and not bias_df[demo_col].isnull().all():
            print(f"\n--- Average AI Bias Score by {demo_title} ---")
            avg_bias = bias_df.groupby(demo_col)['AI_bias_score'].mean()
            print(avg_bias.to_string(float_format="%.2f"))
            
            groups = [list(g.dropna()) for name, g in bias_df.groupby(demo_col)['AI_bias_score'] if len(g.dropna()) > 1]
            
            if len(groups) >= 2:
                stat, p_value = f_oneway(*groups)
                print(f"\nANOVA Result: F-statistic = {stat:.3f}, p-value = {p_value:.4f}")
                if p_value < 0.05:
                    print("Result: The difference in AI bias between these groups is statistically significant.")
                else:
                    print("Result: The difference in AI bias between these groups is not statistically significant.")
            print("-" * 50)


def analyze_creativity_data(data_path: Path):
    """
    Loads, cleans, processes, and analyzes the creativity survey data.
    """
    if not data_path.exists():
        print(f"Error: Data file not found at {data_path}")
        return

    df = pd.read_csv(data_path, skiprows=[1, 2])

    ids_to_remove = ['R_1Lq9U4e6GYOblJF', 'R_7dEogB7kEaGRZvT', 'R_6rJcG07hgMZEwTM']
    original_rows = len(df)
    df = df[~df['ResponseId'].isin(ids_to_remove)]
    print(f"--- Data Cleaning ---")
    print(f"Removed {original_rows - len(df)} incomplete entries. Analyzing {len(df)} remaining entries.\n")

    source_map_A = {'1':{'1':'human','2':'ai'}, '2':{'1':'ai','2':'human'}, '3':{'1':'ai','2':'human'}, '4':{'1':'human','2':'ai'}, '5':{'1':'human','2':'ai'}}
    source_map_B = {'1':{'1':'human','2':'ai'}, '2':{'1':'human','2':'ai'}, '3':{'1':'ai','2':'human'}, '4':{'1':'ai','2':'human'}, '5':{'1':'human','2':'ai'}}

    scores = {"unlabeled_human": [], "unlabeled_ai": [], "labeled_human": [], "labeled_ai": []}
    processed_data_for_demographics = []

    for _, row in df.iterrows():
        is_version1 = not pd.isnull(row['AU1_1'])
        is_version2 = not pd.isnull(row['BU1_1'])
        
        demographics = {
            "ResponseId": row['ResponseId'],
            "age": row.get('age'),
            "gender": row.get('gender'),
            "education": row.get('Q13'),
            "art_experience": row.get('art expirence'),
            "ai_experience": row.get('ai expirence')
        }

        for i in range(1, 6):
            pair_num = str(i)
            if is_version1:
                for img_num in ['1', '2']:
                    score_au = row.get(f'AU{i}_{img_num}')
                    if not pd.isnull(score_au):
                        source = source_map_A[pair_num][img_num]
                        scores[f"unlabeled_{source}"].append(score_au)
                        processed_data_for_demographics.append({"rating": score_au, "source": source, "label_status": "unlabeled", **demographics})
                    
                    score_bl = row.get(f'BL{i}_{img_num}')
                    if not pd.isnull(score_bl):
                        source = source_map_B[pair_num][img_num]
                        scores[f"labeled_{source}"].append(score_bl)
                        processed_data_for_demographics.append({"rating": score_bl, "source": source, "label_status": "labeled", **demographics})
            elif is_version2:
                for img_num in ['1', '2']:
                    score_bu = row.get(f'BU{i}_{img_num}')
                    if not pd.isnull(score_bu):
                        source = source_map_B[pair_num][img_num]
                        scores[f"unlabeled_{source}"].append(score_bu)
                        processed_data_for_demographics.append({"rating": score_bu, "source": source, "label_status": "unlabeled", **demographics})

                    score_al = row.get(f'AL{i}_{img_num}')
                    if not pd.isnull(score_al):
                        source = source_map_A[pair_num][img_num]
                        scores[f"labeled_{source}"].append(score_al)
                        processed_data_for_demographics.append({"rating": score_al, "source": source, "label_status": "labeled", **demographics})
    
    print("--- Descriptive Statistics (Cleaned Data) ---")
    for group_name, data in scores.items():
        if data:
            print(f"{group_name.replace('_', ' ').title()}:")
            print(f"  Mean Rating = {np.mean(data):.2f}")
            print(f"  Standard Deviation = {np.std(data, ddof=1):.2f}\n")

    print("\n--- Statistical Significance Tests (t-tests) (Cleaned Data) ---")
    
    def perform_and_print_ttest(g1_name, g2_name, data):
        g1, g2 = data[g1_name], data[g2_name]
        if not g1 or not g2:
            print(f"Skipping t-test for {g1_name} vs. {g2_name} due to insufficient data.\n")
            return
        stat, p_value = ttest_ind(g1, g2, equal_var=False)
        print(f"Comparison: {g1_name.replace('_', ' ').title()} vs. {g2_name.replace('_', ' ').title()}")
        print(f"  t-statistic = {stat:.3f}")
        print(f"  p-value = {p_value:.4f}")
        print(f"  Result: The difference is {'statistically significant' if p_value < 0.05 else 'not statistically significant'}.\n")

    perform_and_print_ttest("unlabeled_human", "unlabeled_ai", scores)
    perform_and_print_ttest("unlabeled_ai", "labeled_ai", scores)
    perform_and_print_ttest("unlabeled_human", "labeled_human", scores)
    
    analyze_bias_by_demographics(processed_data_for_demographics)


if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    DATA_DIR = BASE_DIR / "data"
    file_path = DATA_DIR / "Creativity Project_November 12, 2025_13.09.csv"
    
    if file_path.exists():
        analyze_creativity_data(file_path)
    else:
        print(f"Error: File not found at the expected path: {file_path}")