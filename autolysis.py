import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

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
    Perform generic analysis on the dataset and adapt to its structure.
    """
    print("\nPerforming Basic Analysis...")

    # Identify column types
    numeric_cols = data.select_dtypes(include='number')
    categorical_cols = data.select_dtypes(include='object')
    date_cols = [col for col in data.columns if 'date' in col.lower()]

    # 1. Dataset Columns and Types
    print("\nDataset Columns and Types:")
    print(data.dtypes)

    # 2. Summary Statistics
    if not numeric_cols.empty:
        print("\nSummary Statistics (Numeric Columns):")
        print(numeric_cols.describe())
    else:
        print("\nNo numeric columns found for summary statistics.")

    # 3. Missing Values
    print("\nMissing Values:")
    missing = data.isnull().sum()
    print(missing)

    # 4. Correlation Analysis
    correlation = None
    if numeric_cols.shape[1] > 1:  # Ensure there are at least two numeric columns
        print("\nCorrelation Matrix:")
        correlation = numeric_cols.corr()
        print(correlation)

        # Create and save correlation heatmap
        plt.figure(figsize=(10, 8))
        sns.heatmap(correlation, annot=True, fmt=".2f", cmap="coolwarm")
        plt.title("Correlation Heatmap")
        plt.savefig("correlation_heatmap.png")
        plt.close()
    else:
        print("\nCorrelation Matrix: Not enough numeric columns to compute correlations.")

    # 5. Outlier Detection
    print("\nOutlier Detection (Numeric Columns):")
    if not numeric_cols.empty:
        for col in numeric_cols.columns:
            mean, std = numeric_cols[col].mean(), numeric_cols[col].std()
            outliers = data[(data[col] > mean + 3 * std) | (data[col] < mean - 3 * std)]
            print(f"{col}: {len(outliers)} potential outliers detected.")
    else:
        print("No numeric columns for outlier detection.")

    # 6. Categorical Column Analysis
    if not categorical_cols.empty:
        print("\nCategorical Column Distributions:")
        for col in categorical_cols.columns:
            print(f"\nDistribution of '{col}':")
            print(data[col].value_counts(normalize=True) * 100)
    else:
        print("\nNo categorical columns found for analysis.")

    # 7. Date Column Analysis
    if date_cols:
        print("\nDate Column Analysis:")
        for col in date_cols:
            data[col] = pd.to_datetime(data[col], errors='coerce')
            print(f"\nSummary for '{col}':")
            print(data[col].describe())

        # Analyze trends over years and months
        if 'year' not in data.columns:
            data['year'] = data[date_cols[0]].dt.year
        if 'month' not in data.columns:
            data['month'] = data[date_cols[0]].dt.month

        print("\nEntries per Year:")
        print(data['year'].value_counts().sort_index())

        print("\nEntries per Month:")
        print(data['month'].value_counts().sort_index())

        # Yearly trend visualization
        data['year'].value_counts().sort_index().plot(kind='line', marker='o')
        plt.title("Entries Per Year")
        plt.xlabel("Year")
        plt.ylabel("Count")
        plt.savefig("yearly_trend.png")
        plt.close()
    else:
        print("\nNo date columns found for analysis.")

    return {
        "summary": data.describe(include='all'),
        "missing": missing,
        "correlation": correlation
    }

def generate_readme(data, filename, output_dir):
    """
    Generate a README.md file summarizing the dataset analysis.
    """
    readme_path = os.path.join(output_dir, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("# Automated Analysis Report\n\n")
        f.write(f"Analysis for dataset: `{filename}`\n\n")
        
        # General dataset info
        f.write("## Dataset Overview\n")
        f.write(data.describe(include="all").to_markdown() + "\n\n")
        
        # Categorical column distributions
        categorical_cols = data.select_dtypes(include="object").columns
        if not categorical_cols.empty:
            f.write("## Categorical Columns Distribution\n")
            for col in categorical_cols:
                f.write(f"### Distribution of '{col}'\n")
                f.write(data[col].value_counts(normalize=True).to_markdown() + "\n\n")
        
        # Add correlation matrix
        numeric_cols = data.select_dtypes(include="number")
        if numeric_cols.shape[1] > 1:
            f.write("## Correlation Matrix\n")
            f.write(numeric_cols.corr().to_markdown() + "\n\n")

    print(f"README.md generated at {readme_path}!")


def main():
    print("Script execution started...")

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

    # List of encodings to try
    encodings = ['utf-8', 'ISO-8859-1', 'latin1', 'utf-16', 'utf-16le', 'utf-16be', 'windows-1252']

    # Attempt to read the file with each encoding
    data = None
    for encoding in encodings:
        try:
            data = pd.read_csv(csv_file, encoding=encoding)
            print(f"Dataset loaded successfully with encoding '{encoding}'!")
            print("Preview of the dataset:")
            print(data.head())
            break
        except Exception as e:
            print(f"Error reading '{csv_file}' with encoding '{encoding}': {e}")
    else:
        print(f"Failed to read the file '{csv_file}' with all supported encodings.")
        sys.exit(1)

    # Check if dataset is empty
    if data.empty:
        print("Error: The dataset is empty. Exiting...")
        sys.exit(1)

    # Ensure output directory exists
    output_dir = ensure_output_directory(csv_file)

    # Perform data analysis
    print("Performing data analysis...")
    results = analyze_data(data)

    # Generate README.md
    generate_readme(data, csv_file, output_dir)
    print("Analysis complete.")

if __name__ == "__main__":
    main()
