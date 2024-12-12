import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.impute import SimpleImputer
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest, RandomForestRegressor
import numpy as np
import openai
from dotenv import load_dotenv
import hashlib
import json
import requests
import argparse

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
    combined_data = {"content": content, "filename": filename}
    return hashlib.md5(json.dumps(combined_data, sort_keys=True).encode()).hexdigest()

# Function to save cache to a file
def update_cache():
    with open(CACHE_FILE, "w") as f:
        json.dump(CACHE, f, indent=2)

# Function to make requests to OpenAI API with caching
def query_llm(content, filename):
    cache_key = generate_cache_key(content, filename)
    if cache_key in CACHE:
        print("Using cached response.")
        return CACHE[cache_key]

    try:
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
        response = requests.post(openai.api_base + "/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        CACHE[cache_key] = result
        update_cache()
        return result
    except requests.exceptions.RequestException as e:
        print(f"Error querying LLM: {e}")
        return {"error": str(e)}

class AutolysisAnalyzer:
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.data = None
        self.results = {}
        self.output_dir = self.ensure_output_directory()

    def ensure_output_directory(self):
        base_name = os.path.splitext(os.path.basename(self.csv_file))[0]
        output_dir = os.path.join(os.getcwd(), base_name)
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    def load_data(self):
        for encoding in ENCODINGS:
            try:
                self.data = pd.read_csv(self.csv_file, encoding=encoding)
                print(f"Dataset loaded successfully with encoding '{encoding}'")
                return
            except Exception as e:
                print(f"Failed with encoding {encoding}: {e}")
        raise ValueError(f"Dataset could not be loaded. Tried encodings: {', '.join(ENCODINGS)}")

    def detect_outliers_iqr(self):
        outliers = {}
        for column in self.data.select_dtypes(include='number').columns:
            Q1 = self.data[column].quantile(0.25)
            Q3 = self.data[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers[column] = self.data[(self.data[column] < lower_bound) | (self.data[column] > upper_bound)].shape[0]
        self.results['Outliers (IQR)'] = outliers

    def feature_importance(self):
        numeric_data = self.data.select_dtypes(include='number')
        if numeric_data.shape[1] > 1:
            X = numeric_data.iloc[:, :-1]
            y = numeric_data.iloc[:, -1]
            model = RandomForestRegressor(random_state=42)
            model.fit(X, y)
            importance = dict(zip(X.columns, model.feature_importances_))
            self.results['Feature Importance'] = importance

    def basic_analysis(self):
        if self.data is None:
            raise ValueError("Dataset not loaded. Please load the dataset first.")
        numeric_data = self.data.select_dtypes(include='number')
        imputer = SimpleImputer(strategy='mean')
        numeric_data_imputed = imputer.fit_transform(numeric_data)
        self.data[numeric_data.columns] = numeric_data_imputed
        self.results['Summary Statistics'] = self.data.describe(include='all').to_string()
        self.results['Missing Values'] = self.data.isnull().sum().to_string()
        if numeric_data.shape[1] > 1:
            sns.heatmap(numeric_data.corr(), annot=True, cmap='coolwarm')
            plt.title('Correlation Matrix')
            plt.tight_layout()
            plt.savefig(os.path.join(self.output_dir, "correlation_matrix.png"))
            plt.close()

    def interpret_visualizations(self):
        for img_file in ["correlation_matrix.png", "clustering_results.png"]:
            img_path = os.path.join(self.output_dir, img_file)
            if os.path.exists(img_path):
                prompt = f"Analyze this visualization and provide insights: {img_path}"
                insights = query_llm(prompt, img_path)
                self.results[f"{img_file} Insights"] = insights

    def generate_report(self):
        readme_content = f"# Automated Analysis Report for {os.path.basename(self.csv_file)}\n\n"
        readme_content += "## Dataset Overview\n"
        readme_content += f"Columns and Types:\n\n{self.data.dtypes.to_string()}\n\n"
        readme_content += f"### Summary Statistics\n```\n{self.results['Summary Statistics']}\n```\n\n"
        readme_content += f"### Missing Values\n```\n{self.results['Missing Values']}\n```\n\n"
        readme_content += "## Visualizations\n"
        readme_content += "![Correlation Matrix](correlation_matrix.png)\n"
        if "correlation_matrix.png Insights" in self.results:
            readme_content += f"### Correlation Matrix Insights:\n{self.results['correlation_matrix.png Insights']}\n\n"
        with open(os.path.join(self.output_dir, "README.md"), "w") as f:
            f.write(readme_content)

    def execute(self, verbose=False, skip_visualizations=False):
        self.load_data()
        self.basic_analysis()
        if verbose:
            print(self.results)
        if not skip_visualizations:
            self.interpret_visualizations()
        self.generate_report()
        print(f"Analysis complete. Results saved in {self.output_dir}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated analysis for datasets.")
    parser.add_argument("csv_file", help="Path to the CSV file.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output.")
    parser.add_argument("--skip-visualizations", action="store_true", help="Skip generating visualizations.")
    args = parser.parse_args()

    analyzer = AutolysisAnalyzer(args.csv_file)
    analyzer.execute(verbose=args.verbose, skip_visualizations=args.skip_visualizations)
