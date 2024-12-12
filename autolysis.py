import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.impute import SimpleImputer
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest
import numpy as np
import openai
from dotenv import load_dotenv
import hashlib
import json
import requests

# Load environment variables for LLM token
load_dotenv()  # Ensure .env file contains AIPROXY_TOKEN
openai.api_key = os.getenv("AIPROXY_TOKEN")
openai.api_base = "https://aiproxy.sanand.workers.dev/openai/v1"  # Proxy URL

# Define constants
IMAGE_SIZE = (512 / 100, 512 / 100)  # Convert pixels to inches (DPI = 100)
CACHE_FILE = "api_cache.json"  # Cache file to store previous API responses
MAX_FILE_SIZE_MB = 10  # Maximum allowed file size in MB for processing
ENCODINGS = ['utf-8', 'ISO-8859-1', 'latin1', 'utf-16', 'utf-16le', 'utf-16be', 'windows-1252']  # List of encodings to try

# Initialize cache
CACHE = {}
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r") as f:
        try:
            CACHE = json.load(f)
        except json.JSONDecodeError:
            CACHE = {}

# Helper function to hash requests and create cache keys
def generate_cache_key(content, filename):
    """Generate a unique cache key based on content and filename."""
    combined_data = {"content": content, "filename": filename}
    return hashlib.md5(json.dumps(combined_data, sort_keys=True).encode()).hexdigest()

# Function to save cache to a file
def update_cache():
    """Save the cached API responses to a JSON file."""
    with open(CACHE_FILE, "w") as f:
        json.dump(CACHE, f, indent=2)

# Function to make requests to OpenAI API with caching
def query_llm(content, filename):
    """Send data to OpenAI API and return the response, using cache when available."""
    cache_key = generate_cache_key(content, filename)

    # Check if cached
    if cache_key in CACHE:
        print("Using cached response.")
        return CACHE[cache_key]

    # Prepare request
    headers = {
        "Authorization": f"Bearer {openai.api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "Assist in dataset analysis."},
            {"role": "user", "content": content}
        ],
        "temperature": 0.7,
    }

    # Send request
    response = requests.post(openai.api_base + "/chat/completions", headers=headers, json=payload)

    if response.status_code == 200:
        result = response.json()
        CACHE[cache_key] = result  # Save response in cache
        update_cache()  # Persist cache to disk
        return result
    else:
        raise RuntimeError(f"LLM request failed with status {response.status_code}: {response.text}")

class AutolysisAnalyzer:
    def __init__(self, csv_file):
        """
        Initializes the analyzer with the dataset and sets up necessary variables.
        """
        self.csv_file = csv_file
        self.data = None
        self.results = {}
        self.output_dir = self.ensure_output_directory()

    def ensure_output_directory(self):
        """
        Creates the output directory based on the CSV filename.
        """
        base_name = os.path.splitext(os.path.basename(self.csv_file))[0]
        output_dir = os.path.join(os.getcwd(), base_name)
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    def check_file_size(self):
        """
        Check the file size to ensure it is within acceptable limits.
        """
        file_size_mb = os.path.getsize(self.csv_file) / (1024 * 1024)  # Convert bytes to MB
        if file_size_mb > MAX_FILE_SIZE_MB:
            raise ValueError(f"File size exceeds the {MAX_FILE_SIZE_MB} MB limit. The file size is {file_size_mb:.2f} MB.")

    def load_data(self):
        """
        Loads the dataset and handles different encodings and file size checks.
        """
        for encoding in ENCODINGS:
            try:
                self.data = pd.read_csv(self.csv_file, encoding=encoding)
                print(f"Dataset loaded successfully with encoding '{encoding}'")
                return
            except Exception as e:
                print(f"Error loading dataset with encoding {encoding}: {e}")
        
        raise ValueError("Failed to load dataset with supported encodings")

    def basic_analysis(self):
        """
        Performs basic statistical analysis on the dataset and stores results.
        """
        if self.data is None:
            raise ValueError("Dataset not loaded. Please load the dataset first.")

        print("\nPerforming Basic Analysis...")

        # Impute missing values with the mean
        numeric_data = self.data.select_dtypes(include='number')
        imputer = SimpleImputer(strategy='mean')
        numeric_data_imputed = imputer.fit_transform(numeric_data)
        self.data[numeric_data.columns] = numeric_data_imputed

        # Summary Statistics
        summary_stats = self.data.describe(include='all').to_string()
        self.results['Summary Statistics'] = summary_stats
        print("Summary Statistics:\n", summary_stats)

        # Missing Values
        missing_values = self.data.isnull().sum().to_string()
        self.results['Missing Values'] = missing_values
        print("Missing Values:\n", missing_values)

        # Correlation Matrix
        if numeric_data.shape[1] > 1:
            correlation_matrix = numeric_data.corr()
            sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm')
            plt.title('Correlation Matrix')
            plt.savefig(os.path.join(self.output_dir, "correlation_matrix.png"))
            plt.close()
            self.results['Correlation Matrix'] = correlation_matrix.to_string()
        
        # Outlier Detection using Isolation Forest
        if numeric_data.shape[0] > 5:
            iso_forest = IsolationForest(random_state=42)
            outlier_labels = iso_forest.fit_predict(numeric_data)
            outliers = (outlier_labels == -1).sum()
            self.results['Outliers (Isolation Forest)'] = f"Detected {outliers} outliers"
            print(f"Isolation Forest Outliers: {outliers}")

        # Clustering
        if numeric_data_imputed.shape[0] > 5:
            n_clusters = min(3, numeric_data_imputed.shape[0])
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(numeric_data_imputed)
            self.data['Cluster'] = clusters
            self.results['Clustering'] = self.data['Cluster'].value_counts().to_string()
            sns.scatterplot(x=numeric_data.columns[0], y=numeric_data.columns[1], hue=clusters, data=self.data)
            plt.title('Clustering Results')
            plt.savefig(os.path.join(self.output_dir, "clustering_results.png"))
            plt.close()

        # LLM Request for Dataset Insights
        dataset_prompt = f"""Analyze the following dataset with columns: {list(self.data.columns)}. 
        Provide suggestions for key visualizations and additional insights. Use simple JSON format in the response."""
        dataset_insights = query_llm(dataset_prompt, self.csv_file)
        self.results['LLM Insights'] = dataset_insights
        print("LLM Insights:\n", dataset_insights)

    def regression_analysis(self):
        """
        Perform regression analysis if the dataset is suitable.
        """
        numeric_data = self.data.select_dtypes(include='number')
        if numeric_data.shape[1] > 1:
            independent_vars = numeric_data.iloc[:, :-1]
            dependent_var = numeric_data.iloc[:, -1]
            model = LinearRegression()
            model.fit(independent_vars, dependent_var)
            self.results['Regression Coefficients'] = model.coef_.tolist()
            print("Regression Analysis:\n", self.results['Regression Coefficients'])

            # LLM Request for Regression Insights
            regression_prompt = f"""Given the following regression coefficients: {self.results['Regression Coefficients']},
            suggest insights and actionable recommendations."""
            regression_suggestions = query_llm(regression_prompt, self.csv_file)
            self.results['Regression Insights'] = regression_suggestions
            print("Regression Insights from LLM:\n", regression_suggestions)

    def generate_report(self):
        """
        Generate a README.md report that summarizes the analysis and includes images.
        """
        readme_content = f"# Automated Analysis Report for {self.csv_file}\n"
        readme_content += "## Dataset Overview\n"
        readme_content += f"Columns and Types:\n{self.data.dtypes}\n\n"
        readme_content += f"Summary Statistics:\n{self.results['Summary Statistics']}\n\n"
        readme_content += f"Missing Values:\n{self.results['Missing Values']}\n\n"
        readme_content += f"Outliers (Isolation Forest):\n{self.results.get('Outliers (Isolation Forest)', 'Not performed')}\n\n"
        readme_content += f"Clustering Results:\n{self.results.get('Clustering', 'Not performed')}\n\n"
        readme_content += f"Regression Analysis Coefficients:\n{self.results.get('Regression Coefficients', 'Not performed')}\n\n"
        readme_content += f"LLM Insights:\n{self.results.get('LLM Insights', 'No insights provided')}\n\n"
        readme_content += f"Regression Insights:\n{self.results.get('Regression Insights', 'No insights provided')}\n\n"
        readme_content += "## Visualizations\n"
        readme_content += "![Correlation Matrix](correlation_matrix.png)\n"
        readme_content += "![Clustering Results](clustering_results.png)\n"
        
        with open(os.path.join(self.output_dir, "README.md"), "w") as f:
            f.write(readme_content)

    def execute(self):
        """
        Executes the entire analysis pipeline, including data loading, analysis, visualization, and report generation.
        """
        self.load_data()
        self.basic_analysis()
        self.regression_analysis()
        self.generate_report()
        print(f"Analysis complete. Results saved in {self.output_dir}")

# Running the analysis with the file passed as argument
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python autolysis.py <dataset.csv>")
        sys.exit(1)

    csv_file = sys.argv[1]
    analyzer = AutolysisAnalyzer(csv_file)
    analyzer.execute()