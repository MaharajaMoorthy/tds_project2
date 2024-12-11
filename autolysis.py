import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Set the default size for generated images
IMAGE_SIZE = (512 / 100, 512 / 100)  # Convert pixels to inches (DPI = 100)

def ensure_output_directory(csv_file):
    """
    Ensures that the output directory exists based on the CSV filename.
    """
    base_name = os.path.splitext(os.path.basename(csv_file))[0]
    output_dir = os.path.join(os.getcwd(), base_name)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def save_chart(output_dir, filename, plot_func):
    """
    Helper function to save charts with consistent size and naming.
    """
    filepath = os.path.join(output_dir, filename)
    plt.figure(figsize=IMAGE_SIZE)
    plot_func()
    plt.xticks(rotation=90)  # Rotate x-axis labels to prevent overlap
    plt.savefig(filepath, dpi=100, bbox_inches='tight')
    plt.close()
    print(f"Saved chart: {filepath}")

def analyze_data(data, output_dir):
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

    # 4. Outlier Detection
    print("\nOutlier Detection (Numeric Columns):")
    if not numeric_cols.empty:
        for col in numeric_cols.columns:
            mean, std = numeric_cols[col].mean(), numeric_cols[col].std()
            outliers = data[(data[col] > mean + 3 * std) | (data[col] < mean - 3 * std)]
            print(f"{col}: {len(outliers)} potential outliers detected.")

    # 5. Correlation Analysis
    correlation = None
    if numeric_cols.shape[1] > 1:  # Ensure there are at least two numeric columns
        print("\nCorrelation Matrix:")
        correlation = numeric_cols.corr()
        print(correlation)

    # 6. Categorical Column Analysis
    print("\nCategorical Column Analysis:")
    if not categorical_cols.empty:
        for col in categorical_cols.columns:
            unique_values = data[col].nunique()
            mode = data[col].mode()[0]
            mode_frequency = (data[col].value_counts(normalize=True).iloc[0] * 100)
            print(f"{col}: Unique values = {unique_values}, Mode = {mode} ({mode_frequency:.2f}%)")
    else:
        print("No categorical columns found for analysis.")

    # 7. Date Column Analysis
    print("\nDate Column Analysis:")
    if date_cols:
        for col in date_cols:
            data[col] = pd.to_datetime(data[col], errors='coerce')
            print(f"\nSummary for '{col}':")
            print(data[col].describe())
        if 'year' not in data.columns:
            data['year'] = data[date_cols[0]].dt.year
        if 'month' not in data.columns:
            data['month'] = data[date_cols[0]].dt.month
        print("\nEntries per Year:")
        print(data['year'].value_counts().sort_index())
        print("\nEntries per Month:")
        print(data['month'].value_counts().sort_index())

    # Define a priority queue for charts
    chart_queue = []

    # Add charts based on priority
    if correlation is not None:
        chart_queue.append(("correlation_heatmap.png", lambda: sns.heatmap(correlation, annot=True, fmt=".2f", cmap="coolwarm")))

    if not numeric_cols.empty:
        chart_queue.append(("outlier_boxplot.png", lambda: sns.boxplot(data=numeric_cols)))
        chart_queue.append(("numeric_histograms.png", lambda: numeric_cols.hist(bins=15, figsize=(12, 8))))

    if not categorical_cols.empty:
        chart_queue.append(("categorical_distribution.png", lambda: sns.barplot(
            data=data[categorical_cols].melt(), x="variable", y="value", estimator=len, ci=None
        )))

    if date_cols:
        chart_queue.append(("yearly_trend.png", lambda: data['year'].value_counts().sort_index().plot(kind='line', marker='o')))

    # Save only the top 5 charts
    for i, (filename, plot_func) in enumerate(chart_queue[:5]):
        save_chart(output_dir, filename, plot_func)

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

        # Embed generated images
        f.write("## Visualizations\n")
        for chart in ["correlation_heatmap.png", "outlier_boxplot.png", "numeric_histograms.png", "categorical_distribution.png", "yearly_trend.png"]:
            chart_path = os.path.join(output_dir, chart)
            if os.path.exists(chart_path):
                f.write(f"![{chart}]({chart})\n\n")

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
    results = analyze_data(data, output_dir)

    # Generate README.md
    generate_readme(data, csv_file, output_dir)
    print("Analysis complete.")

if __name__ == "__main__":
    main()
