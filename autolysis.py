import os
import sys
import pandas as pd

def ensure_output_directory(csv_file):
    """
    Ensures that the output directory exists based on the CSV filename.
    """
    base_name = os.path.splitext(os.path.basename(csv_file))[0]
    output_dir = os.path.join(os.getcwd(), base_name)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def analyze_data(data):
    """
    Perform generic analysis on the dataset and print key insights.
    """
    print("\nPerforming Basic Analysis...")

    # 1. Data Types and Column Information
    print("\nDataset Columns and Types:")
    print(data.dtypes)

    # 2. Summary Statistics
    print("\nSummary Statistics:")
    summary = data.describe(include='all')  # Include all columns (numeric and non-numeric)
    print(summary)

    # 3. Missing Values
    print("\nMissing Values:")
    missing = data.isnull().sum()  # Count missing values per column
    print(missing)

    # 4. Correlation Analysis
    correlation = None
    if data.select_dtypes(include='number').shape[1] > 1:  # Ensure there are numeric columns
        print("\nCorrelation Matrix:")
        correlation = data.corr()  # Generate correlation matrix
        print(correlation)

    # 5. Outlier Detection
    print("\nOutlier Detection:")
    numeric_cols = data.select_dtypes(include='number')
    if not numeric_cols.empty:
        outliers = (numeric_cols > (numeric_cols.mean() + 3 * numeric_cols.std())) | \
                   (numeric_cols < (numeric_cols.mean() - 3 * numeric_cols.std()))
        print("Potential Outliers Detected (True indicates outliers):")
        print(outliers.any(axis=0))  # Identify columns with potential outliers

    return {
        "summary": summary,
        "missing": missing,
        "correlation": correlation
    }

def main():
    print("Script started...")  # Debugging print
    print(f"Command-line arguments: {sys.argv}")  # Debugging
    # Ensure a CSV filename is provided
    if len(sys.argv) != 2:
        print("Error: Missing required argument. Usage: python autolysis.py <dataset.csv>")
        sys.exit(1)
    print("CSV argument provided.")

    # Get the filename
    csv_file = sys.argv[1]
    print(f"Received filename: {csv_file}")

    # Check if file exists
    if not os.path.exists(csv_file):
        print(f"Error: File '{csv_file}' not found.")
        sys.exit(1)
    print(f"File '{csv_file}' exists.")

    # Load the dataset
    try:
        data = pd.read_csv(csv_file)
        print("Dataset loaded successfully!")
        print("Preview of the dataset:")
        print(data.head())
    except Exception as e:
        print(f"Error reading '{csv_file}': {e}")
        sys.exit(1)

    # Check if dataset is empty
    if data.empty:
        print("Error: The dataset is empty. Exiting...")
        sys.exit(1)

    # Perform data analysis
    print("Performing data analysis...")
    results = analyze_data(data)
    print("\nAnalysis Results:")
    print("Summary Statistics:")
    print(results['summary'])

    print("\nMissing Values:")
    print(results['missing'])

    if results['correlation'] is not None:
        print("\nCorrelation Matrix:")
        print(results['correlation'])

    print("Analysis complete.")
