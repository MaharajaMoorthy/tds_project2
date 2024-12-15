# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas",          # For data manipulation and analysis
#   "seaborn",         # For creating visualizations (e.g., heatmaps, boxplots)
#   "matplotlib",      # For generating charts and saving visualizations
#   "requests",        # For API calls to interact with the LLM
#   "scikit-learn",    # For outlier detection (e.g., IsolationForest) and clustering
#   "tabulate",        # For creating Markdown tables in reports
#   "numpy",           # For numerical computations and efficient data handling
#   "networkx",        # For network analysis (if using graph-based analysis)
# ]
# ///


import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import json
import hashlib
import argparse
import requests
import re
import base64
import shutil
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
import networkx as nx
import base64

CACHE_FILE = "api_cache.json"

# Load or initialize cache
if os.path.exists(CACHE_FILE):
    print("Loading cache from file...")
    with open(CACHE_FILE, "r") as f:
        try:
            CACHE = json.load(f)
            print(f"Cache loaded with {len(CACHE)} entries.")
        except json.JSONDecodeError:
            print("Cache file is corrupted. Initializing a new cache.")
            CACHE = {}
else:
    print("No cache file found. Initializing a new cache.")
    CACHE = {}

# Function to upload PNG files
def upload_png_files():
    """
    Read and encode all .png files in the current directory.
    Returns a dictionary with filenames as keys and base64-encoded content as values.
    """
    png_files = [f for f in os.listdir('.') if f.endswith('.png')]
    if not png_files:
        print("No PNG files found to upload.")
        return {}

    encoded_files = {}
    for file in png_files:
        try:
            with open(file, "rb") as f:
                encoded_files[file] = base64.b64encode(f.read()).decode('utf-8')
            print(f"Successfully encoded: {file}")
        except Exception as e:
            print(f"Failed to encode {file}: {e}")
    return encoded_files

def save_cache():
    """Save the cache to a file."""
    with open(CACHE_FILE, "w") as f:
        json.dump(CACHE, f, indent=2)
    print("Cache saved successfully.")

def hash_request(data, filename):
    """Generate a hash for the data and filename to use as a cache key."""
    combined_data = {"data": data, "filename": filename}
    return hashlib.md5(json.dumps(combined_data, sort_keys=True).encode()).hexdigest()

def make_openai_request(data, filename):
    """Make a request to OpenAI API with caching."""
    url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
    token = os.getenv("AIPROXY_TOKEN")
    
    if not token:
        raise EnvironmentError("AIPROXY_TOKEN environment variable is not set.")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # Generate a unique cache key
    cache_key = hash_request(data, filename)

    # Check cache
    if cache_key in CACHE:
        print("Using cached response.")
        return CACHE[cache_key]

    # Print data before sending to check for issues
    print("Request Data:", data)  # Check the structure of the data being sent
    
    # Make the API request
    response = requests.post(url, headers=headers, json=data)  # 'json=data' ensures proper JSON formatting

    # Handle the response
    if response.status_code == 200:
        result = response.json()
        CACHE[cache_key] = result  # Save to cache
        save_cache()  # Persist cache to file
        return result
    else:
        print(f"Error: {response.status_code}")
        print(f"Response Body: {response.text}")  # Full response body for debugging
        raise RuntimeError(f"OpenAI API request failed: {response.status_code} {response.text}")

def load_data(filename):
    """Load the dataset from a CSV file with dynamic encoding detection."""
    encodings = [
        'utf-8', 'utf-8-sig', 'latin1', 'ISO-8859-1', 'ISO-8859-2', 
        'ISO-8859-15', 'cp1252', 'cp1251', 'cp850', 'ascii'
    ]
    for encoding in encodings:
        try:
            print(f"Trying to load dataset with encoding: {encoding}")
            return pd.read_csv(filename, encoding=encoding, on_bad_lines='skip')
        except UnicodeDecodeError:
            print(f"Encoding {encoding} failed. Trying the next one...")
    raise RuntimeError(f"Error loading {filename}: Unable to decode file with the tried encodings.")

def organize_files_into_folder(folder_name):
    """
    Move all .png and .md files in the current directory into a specified folder inside the eval directory.
    """
    current_dir = os.getcwd()  # Get the current directory
    # Ensure we're using the correct path for your eval subfolder.
    target_dir = os.path.join(current_dir, "eval", folder_name)  # Target folder inside eval subfolder

    os.makedirs(target_dir, exist_ok=True)  # Ensure target folder exists

    files_to_move = [file for file in os.listdir(current_dir) if file.endswith(('.png', '.md'))]

    for file in files_to_move:
        src_path = os.path.join(current_dir, file)
        dest_path = os.path.join(target_dir, file)
        shutil.move(src_path, dest_path)
        print(f"Moved: {file} -> {folder_name}")

    if not files_to_move:
        print("No .png or .md files found to move.")

def detect_columns(df):
    """Detect key columns in the dataset to adjust analysis."""
    columns_info = {
        'time_column': None,
        'geo_columns': None,
        'categorical_columns': [],
        'numeric_columns': []
    }

    if 'date' in df.columns.str.lower() or 'time' in df.columns.str.lower():
        columns_info['time_column'] = df.select_dtypes(include=['datetime']).columns.tolist()

    geo_candidates = [col for col in df.columns if 'lat' in col.lower() or 'long' in col.lower()]
    if len(geo_candidates) == 2:
        columns_info['geo_columns'] = geo_candidates

    columns_info['categorical_columns'] = df.select_dtypes(include=['object']).columns.tolist()
    columns_info['numeric_columns'] = df.select_dtypes(include=['number']).columns.tolist()

    return columns_info

def generate_dynamic_prompt(df):
    """Generate a dynamic prompt based on dataset structure."""
    columns_info = detect_columns(df)
    
    prompt = f"""You are analyzing a dataset with the following structure:
    - Time Column: {columns_info['time_column']}
    - Geographic Columns: {columns_info['geo_columns']}
    - Categorical Columns: {columns_info['categorical_columns']}
    - Numeric Columns: {columns_info['numeric_columns']}
    
    Please perform the following analyses:
    1. **Clustering**: Based on the numeric columns.
    2. **Feature Importance**: Correlation with the target column (if provided).
    3. **Time Series Analysis**: If a time column exists, analyze trends over time.
    4. **Geospatial Analysis**: If geographic columns exist, analyze distribution by location.
    5. **Correlation Analysis**: Analyze relationships between numeric columns.

    Please suggest further steps for any additional patterns you notice."""
    
    return prompt

def detect_outliers(df):
    """
    Detect outliers using the IQR method.
    Returns a list of dictionaries with outlier details for each numeric column.
    """
    outlier_info = []
    for column in df.select_dtypes(include=['number']).columns:
        Q1 = df[column].quantile(0.25)
        Q3 = df[column].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]
        outlier_count = len(outliers)
        outlier_info.append({
            "column": column,
            "outlier_count": outlier_count,
            "lower_bound": lower_bound,
            "upper_bound": upper_bound
        })
        print(f"Outliers detected in column '{column}': {outlier_count} "
              f"(Lower Bound: {lower_bound}, Upper Bound: {upper_bound})")
    return outlier_info

def basic_analysis(df):
    """Perform basic analysis on the dataset."""
    df_description = df.describe(include='all').to_markdown()  # Basic summary statistics
    insights = {
        "missing_values": df.isnull().sum().to_markdown(),
        "outliers": detect_outliers(df),  # Assuming you want to keep outlier detection from Block 2
        'column': df.columns.tolist(),
        'data_type': df.dtypes.to_markdown(),
        'numerical_features': df.select_dtypes(include=['number']).columns.tolist(),
        'numerical_missing_values': df[df.select_dtypes(include=['number']).columns].isnull().sum().to_markdown(),
        'numerical_unique_values': df[df.select_dtypes(include=['number']).columns].nunique().to_markdown(),
        'categories_features': df.select_dtypes(include=['object']).columns.tolist(),
        'categorical_missing_values': df[df.select_dtypes(include=['object']).columns].isnull().sum().to_markdown(),
        'categorical_unique': df[df.select_dtypes(include=['object']).columns].nunique().to_markdown(),
        'sample_data': df.head(10).to_markdown(),
    }
    return df_description, insights

def impute_missing_values(df):
    """Impute missing values using the mean for numeric columns."""
    numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
    imputer = SimpleImputer(strategy='mean')  # Using mean imputation
    df[numeric_columns] = imputer.fit_transform(df[numeric_columns])
    return df

def advanced_analysis(df, target_column=None, num_clusters=3):
    """
    Perform advanced analysis on the dataset, including clustering, feature importance, 
    outlier detection, PCA, and additional analysis like time series or geospatial analysis.
    """
    results = {}

    # 1. Impute missing values
    df = impute_missing_values(df)  # Impute missing values before proceeding

    # 2. Clustering (KMeans)
    if len(df.select_dtypes(include=['number']).columns) > 1:
        print("Performing Clustering...")
        numeric_data = df.select_dtypes(include=['number'])
        kmeans = KMeans(n_clusters=num_clusters, random_state=42)
        df['Cluster'] = kmeans.fit_predict(numeric_data)  # Apply clustering

        results['clustering'] = f"Clustering completed with {num_clusters} clusters."

    # 3. Feature Importance (Correlation with target column)
    if target_column in df.columns:
        print("Calculating Feature Importance...")
        correlations = df.corr()[target_column].sort_values(ascending=False)
        results['feature_importance'] = correlations

    # 4. Outlier Detection using Isolation Forest
    print("Detecting Outliers...")
    isolation_forest = IsolationForest(random_state=42)
    numeric_data_for_outliers = df.select_dtypes(include=['number'])
    df['Outlier_Score'] = isolation_forest.fit_predict(numeric_data_for_outliers)  # Outlier detection
    outliers = df[df['Outlier_Score'] == -1]
    results['outliers'] = f"{len(outliers)} outliers detected using Isolation Forest."

    # 5. PCA (Principal Component Analysis)
    print("Performing PCA...")
    if len(df.select_dtypes(include=['number']).columns) > 1:
        pca = PCA(n_components=2)
        pca_result = pca.fit_transform(numeric_data_for_outliers)
        results['pca'] = {
            "explained_variance_ratio": pca.explained_variance_ratio_,
            "components": pca_result
        }

    # Additional steps for time series analysis or geospatial analysis can be added here
    # For example:
    # if 'time_column' in df.columns:
    #     results['time_series_analysis'] = perform_time_series_analysis(df['time_column'])

    return results

def analyze_visualization_with_llm(image_file):
    """Send image to LLM for interpretation or analysis using AIProxy."""
    
    try:
        # Open the image file
        with open(image_file, "rb") as img_file:
            # Prepare the payload with the image
            files = {"file": (image_file, img_file, "image/png")}
            data = {
                "model": "gpt-4o-mini",  # Use the appropriate model
                "messages": [
                    {"role": "system", "content": "You are a data analysis assistant."},
                    {"role": "user", "content": "Please analyze the following chart:"}
                ],
                "temperature": 0.5
            }

            # Make the request to AIProxy using your predefined URL and token
            response = make_openai_request(data, image_file)  # Using the make_openai_request function

            # Check if the response was successful
            if response and response.get("choices"):
                print("Analysis Response: ", response['choices'][0]['message']['content'])
                return response['choices'][0]['message']['content']
            else:
                print("Error: Response was not valid or did not contain analysis.")
                return None
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

def generate_visualizations(df, filename):
    """
    Generate visualizations for the dataset, including boxplots, heatmaps, and histograms,
    and send the images for analysis.
    """
    numeric_columns = df.select_dtypes(include=['number']).columns.tolist()

    if not numeric_columns:
        print("No numeric columns found for generating visualizations.")
        return

    # Generate Boxplots
    print("Generating boxplots...")
    generate_boxplots(df, 'outlier_boxplots.png')

    # Analyze Boxplot visualization with LLM
    analyze_visualization_with_llm('outlier_boxplots.png')

    # Generate Heatmap
    if len(numeric_columns) > 1:  # Heatmap requires at least two numeric columns
        try:
            print("Generating heatmap for correlation matrix...")
            correlation_matrix = df[numeric_columns].corr()
            plt.figure(figsize=(10, 8))
            sns.heatmap(correlation_matrix, annot=True, fmt=".2f", cmap="coolwarm", square=True)
            plt.title("Correlation Heatmap")
            plt.savefig('correlation_heatmap.png', bbox_inches='tight')
            plt.close()
            print("Heatmap saved as correlation_heatmap.png")

            # Analyze Heatmap visualization with LLM
            analyze_visualization_with_llm('correlation_heatmap.png')
        except Exception as e:
            print(f"Error generating heatmap: {e}")

    # Generate Histograms
    try:
        print("Generating histograms for numeric columns...")
        plt.figure(figsize=(15, 10))
        for i, column in enumerate(numeric_columns):
            plt.subplot((len(numeric_columns) + 2) // 3, 3, i + 1)
            sns.histplot(df[column], kde=True, bins=30)
            plt.title(f'Histogram of {column}')
        plt.tight_layout()
        plt.savefig('histograms.png', bbox_inches='tight')
        plt.close()
        print("Histograms saved as histograms.png")

        # Analyze Histogram visualization with LLM
        analyze_visualization_with_llm('histograms.png')
    except Exception as e:
        print(f"Error generating histograms: {e}")

    # Validate generated visualizations
    validate_visualizations(['outlier_boxplots.png', 'correlation_heatmap.png', 'histograms.png'])

def validate_visualizations(expected_files):
    """
    Check if all expected visualization files are created.
    """
    missing_files = [file for file in expected_files if not os.path.exists(file)]
    if missing_files:
        print(f"Missing visualization files: {', '.join(missing_files)}")
    else:
        print(f"All visualizations generated successfully: {', '.join(expected_files)}")

def generate_boxplots(df, output_file):
    """
    Generate boxplots for all numeric columns in the dataset and save as a single image.
    """
    numeric_columns = df.select_dtypes(include=['number']).columns.tolist()

    if not numeric_columns:
        print("No numeric columns found for generating boxplots.")
        return

    # Create a boxplot for each numeric column
    plt.figure(figsize=(15, 5 * len(numeric_columns)))
    for i, column in enumerate(numeric_columns):
        try:
            plt.subplot((len(numeric_columns) + 2) // 3, 3, i + 1)
            sns.boxplot(y=df[column])
            plt.title(f'Boxplot of {column}')
        except Exception as e:
            print(f"Error creating boxplot for column '{column}': {e}")
            continue  # Skip to the next column if there is an error

    # Adjust layout to ensure everything fits without overlap
    plt.tight_layout()

    # Attempt to save the generated plots as a PNG image
    try:
        plt.savefig(output_file, bbox_inches='tight')  # Save the plot to a PNG file
        print(f"Boxplots saved as {output_file}")
    except Exception as e:
        print(f"Error saving boxplots: {e}")
    finally:
        plt.close()  # Close the plot to free resources

def narrate_story(summary, insights, filename):
    """
    Generate a narrative story using the OpenAI API.
    Includes dataset summary, insights, and references to generated PNG files.
    """
    png_files = upload_png_files()
    print(f"Uploading {len(png_files)} PNG files.")

    # Build prompt for narrative generation
    prompt = (f"Analyze the dataset based on the following summary statistics and insights:\n\n"
              f"Summary:\n{json.dumps(summary, indent=2)}\n\n"
              f"Insights:\n"
              f"- Missing Values: {insights['missing_values']}\n"
              f"- Outliers: {insights['outliers']}\n"
              f"- Columns: {insights['column']}\n"
              f"- Data Types: {insights['data_type']}\n"
              f"- Numerical Features: {insights['numerical_features']}\n"
              f"- Categorical Features: {insights['categories_features']}\n\n"
              f"Write a detailed overview explaining key insights, "
              f"how outliers might impact the results, and suggest potential actions to handle them.")

    # Add images to the request payload
    image_list = []
    for key, value in png_files.items():
        image_dict = {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{value}"
            }
        }
        image_list.append(image_dict)

    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "Analyze the dataset based on the summary and insights provided."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.5
    }

    response = make_openai_request(data, filename)

    # Extract and return the narrative content
    narrative = response["choices"][0]["message"]["content"]
    print("Narrative generated successfully.")
    return narrative

def save_outputs(markdown):
    """Save the generated Markdown and plots."""
    with open("README.md", "w") as f:
        f.write(markdown)

def main():
    """
    Main function to orchestrate dataset analysis, visualization, narrative generation,
    and output organization.
    """
    parser = argparse.ArgumentParser(description="Autolysis: Automated Dataset Analysis")
    parser.add_argument("filename", type=str, help="Input CSV file")
    args = parser.parse_args()

    try:
        # Load the dataset
        df = load_data(args.filename)
        print(f"Dataset loaded successfully with {len(df)} rows and {len(df.columns)} columns.")

        # Validate the dataset
        if df.empty:
            raise ValueError("The dataset is empty. Please provide a valid dataset.")

        # Detect columns (categorical, numeric, time, geo)
        columns_info = detect_columns(df)
        print(f"Detected columns: {columns_info}")

        # Generate dynamic prompt based on dataset structure
        prompt = generate_dynamic_prompt(df)
        print("Generated dynamic prompt for analysis.")

        # Perform basic analysis
        summary, insights = basic_analysis(df)  # Basic analysis of the dataset
        print("Basic analysis completed.")

        # Perform advanced analysis
        results = advanced_analysis(df)  # Advanced analysis including clustering, PCA, etc.
        print("Advanced analysis results:", results)

        # Generate visualizations
        generate_visualizations(df, args.filename)  # Visualizations like boxplots, heatmaps, and histograms
        print("Visualizations generated successfully.")

        # Analyze the visualizations with LLM (Boxplots, Heatmaps, etc.)
        analyze_visualization_with_llm('outlier_boxplots.png')
        analyze_visualization_with_llm('correlation_heatmap.png')
        analyze_visualization_with_llm('histograms.png')
        print("Visualization analysis with LLM completed.")

        # Generate narrative from the basic analysis results
        markdown = narrate_story(summary, insights, args.filename)  # Generates a detailed narrative
        print("Narrative generated successfully.")

        # Save outputs (Markdown and images)
        save_outputs(markdown)  # Save markdown content (e.g., README.md)
        print("Outputs saved successfully.")

        # Organize files into a folder
        organize_files_into_folder(args.filename[:-4])  # Organize files into a folder based on the filename
        print(f"All outputs organized into folder: {args.filename[:-4]}")

    except Exception as e:
        print(f"An error occurred during execution: {e}")

if __name__ == "__main__":
    main()

