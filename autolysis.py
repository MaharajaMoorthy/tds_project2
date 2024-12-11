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

def save_chart(output_dir, filename, plot_func, title=None, xlabel=None, ylabel=None, legend=False):
    """
    Saves a chart with consistent size and annotations such as titles and labels.
    """
    filepath = os.path.join(output_dir, filename)
    plt.figure(figsize=IMAGE_SIZE)
    plot_func()
    if title:
        plt.title(title)
    if xlabel:
        plt.xlabel(xlabel)
    if ylabel:
        plt.ylabel(ylabel)
    if legend:
        plt.legend()
    plt.xticks(rotation=90)  # Rotate x-axis labels to prevent overlap
    plt.savefig(filepath, dpi=100, bbox_inches='tight')
    plt.close()
    print(f"Saved chart: {filepath}")

def analyze_data(data, output_dir):
    """
    Perform a detailed analysis of the dataset and generate relevant insights and visualizations.
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
            if not data[col].isnull().all():
                yearly_counts = data[col].dt.year.value_counts().sort_index()
                print(f"\nEntries per Year for {col}:")
                print(yearly_counts)
                monthly_counts = data[col].dt.month.value_counts().sort_index()
                print(f"\nEntries per Month for {col}:")
                print(monthly_counts)

    # Generate visualizations dynamically
    chart_queue = []

    if correlation is not None:
        chart_queue.append(("correlation_heatmap.png", lambda: sns.heatmap(correlation, annot=True, fmt=".2f", cmap="coolwarm"),
                           "Correlation Heatmap", "Variables", "Correlation Coefficient", False))

    if not numeric_cols.empty:
        chart_queue.append(("outlier_boxplot.png", lambda: sns.boxplot(data=numeric_cols),
                           "Boxplot of Numeric Columns", "Columns", "Values", False))
        chart_queue.append((
    "numeric_histograms.png",lambda: (numeric_cols.hist(bins=15, figsize=(12, 8)),  # Create the histograms
        plt.suptitle("Numeric Data Distribution")    # Add the title
    ), None, None, None, False
))


    if date_cols:
        for col in date_cols:
            if not data[col].isnull().all():
                chart_queue.append((
                    f"{col}_yearly_trend.png",
                    lambda: data[col].dt.year.value_counts().sort_index().plot(kind="line", marker="o"),
                    f"Yearly Trend for {col}", "Year", "Count", False
                ))

    for i, (filename, plot_func, title, xlabel, ylabel, legend) in enumerate(chart_queue[:5]):
        save_chart(output_dir, filename, plot_func, title, xlabel, ylabel, legend)

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

        # Add correlation matrix
        numeric_cols = data.select_dtypes(include="number")
        if numeric_cols.shape[1] > 1:
            f.write("## Correlation Matrix\n")
            f.write(numeric_cols.corr().to_markdown() + "\n\n")

        # Embed generated images
        f.write("## Visualizations\n")
        for chart in os.listdir(output_dir):
            if chart.endswith(".png"):
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

    # Attempt to read the file with multiple encodings
    encodings = ['utf-8', 'ISO-8859-1', 'latin1', 'utf-16', 'utf-16le', 'utf-16be', 'windows-1252']
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
