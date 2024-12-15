# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas",          # For data manipulation and analysis
#   "seaborn",         # For creating visualizations (e.g., heatmaps, boxplots, histograms)
#   "matplotlib",      # For generating charts and saving visualizations
#   "requests",        # For API calls to interact with the LLM
#   "scikit-learn",    # For clustering (KMeans), outlier detection (IsolationForest), and PCA
#   "tabulate",        # For creating Markdown tables in reports
#   "numpy",           # For numerical computations and efficient data handling
#   "Pillow",          # For resizing images before LLM analysis
#   "networkx",        # For network analysis (if using graph-based analysis in future iterations)
# ]
# ///


import os
from io import BytesIO
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import json
import hashlib
import argparse
import requests
import base64
import shutil
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
import base64
import logging
from PIL import Image


# Setup basic configuration for logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global initialization
CACHE_FILE = "api_cache.json"
CACHE = None

def load_cache():
    """Load or initialize the cache."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cache = json.load(f)
                logging.info(f"Cache loaded with {len(cache)} entries.")
                return cache
        except json.JSONDecodeError:
            logging.warning("Cache file is corrupted. Initializing a new cache.")
            return {}
    else:
        logging.info("No cache file found. Initializing a new cache.")
        return {}

def save_cache():
    """Save the global cache to a file."""
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(CACHE, f, indent=2)
        logging.info("Cache saved successfully.")
    except Exception as e:
        logging.error(f"Failed to save cache with error: {e}")

def check_cache(key):
    """Check if a response is in the global cache."""
    if key in CACHE:
        logging.info("Using cached response.")
        return CACHE[key]
    return None

# Initialize CACHE globally
CACHE = load_cache()


def load_data(filename):
    """Load the dataset from a CSV file with dynamic encoding detection."""
    encodings = [
        'utf-8', 'utf-8-sig', 'latin1', 'ISO-8859-1', 'ISO-8859-2', 
        'ISO-8859-15', 'cp1252', 'cp1251', 'cp850', 'ascii'
    ]
    for encoding in encodings:
        try:
            logging.info(f"Trying to load dataset with encoding: {encoding}")
            return pd.read_csv(filename, encoding=encoding, on_bad_lines='skip')
        except UnicodeDecodeError as e:
            logging.error(f"Encoding {encoding} failed with error: {e}. Trying the next one...")
    logging.critical(f"Error loading {filename}: Unable to decode file with the tried encodings.")
    raise RuntimeError(f"Error loading {filename}: Unable to decode file with the tried encodings.")

def make_openai_request(data, filename, debug=False, retries=3, timeout=10):
    """
    Make a request to the OpenAI API with caching, dynamic prompt generation, and error handling.

    Parameters:
    - data: dict
        The JSON payload for the API request.
    - filename: str
        A filename used to generate the cache key.
    - debug: bool
        If True, prints the request data for debugging.
    - retries: int
        Number of retry attempts for transient failures.
    - timeout: int
        Timeout duration (in seconds) for the API request.

    Returns:
    - dict: The response from the OpenAI API if successful.
    """
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

    # Check the cache
    cached_response = CACHE.get(cache_key)
    if cached_response:
        logging.info("Using cached response.")
        return cached_response

    # Debugging option
    if debug:
        logging.debug(f"Request Data: {json.dumps(data, indent=2)}")

    # Make the API request with retries
    for attempt in range(1, retries + 1):
        try:
            logging.info(f"Attempt {attempt}: Sending request to OpenAI API...")
            response = requests.post(url, headers=headers, json=data, timeout=timeout)

            if response.status_code == 200:
                result = response.json()

                # Validate response structure
                if not isinstance(result, dict) or "choices" not in result:
                    logging.error(f"Unexpected response structure: {result}")
                    raise ValueError("Invalid response structure received from LLM.")

                CACHE[cache_key] = result  # Save to cache
                save_cache()  # Persist cache to file
                logging.info("API request successful. Response cached.")
                return result
            else:
                logging.error(f"API request failed with status {response.status_code}: {response.text}")
                raise RuntimeError(f"API request failed: {response.status_code} {response.text}")

        except requests.RequestException as e:
            logging.warning(f"Request failed on attempt {attempt}. Error: {e}")
            if attempt == retries:
                logging.critical("All retry attempts failed. Aborting.")
                raise
        except Exception as e:
            logging.error(f"Unexpected error occurred: {e}")
            raise

# Helper function to hash requests (ensure it's available in your script)
def hash_request(data, filename):
    """
    Generate a hash for the data and filename to use as a cache key.
    """
    combined_data = {"data": data, "filename": filename}
    return hashlib.md5(json.dumps(combined_data, sort_keys=True).encode()).hexdigest()

def organize_files_into_folder(folder_name):
    """
    Move all .png and .md files in the current directory into the folder specified inside the 'eval' directory.
    Ensure that the folder name matches the expected structure (including .csv).
    """
    # Get the directory where the current script (autolysis.py) is located
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Absolute path of the script directory
    
    # Include the .csv extension in the folder name to match the evaluation folder
    target_dir = os.path.join(script_dir, "eval", folder_name + ".csv")  # Expect folder to match the dataset filename

    os.makedirs(target_dir, exist_ok=True)  # Ensure target folder exists

    files_to_move = [file for file in os.listdir(script_dir) if file.endswith(('.png', '.md'))]

    for file in files_to_move:
        src_path = os.path.join(script_dir, file)
        dest_path = os.path.join(target_dir, file)
        shutil.move(src_path, dest_path)
        print(f"Moved: {file} -> {folder_name}")

    if not files_to_move:
        print("No .png or .md files found to move.")

def basic_analysis(df):
    """Perform basic analysis on the dataset."""
    if df.select_dtypes(include=[np.number]).empty:
        logging.warning("No numeric columns available for operations.")
        return "No numeric data available", {}
    else:
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
            'num_rows': len(df),
            'num_columns': len(df.columns)
        }
        return df_description, insights

def impute_missing_values(df, numeric_strategy='mean', categorical_strategy='most_frequent', placeholder="Unknown"):
    """
    Impute missing values in the dataset.
    
    Parameters:
    - df: pandas.DataFrame
        The dataset to preprocess.
    - numeric_strategy: str, optional (default='mean')
        Strategy for imputing numeric columns ('mean', 'median', 'most_frequent').
    - categorical_strategy: str, optional (default='most_frequent')
        Strategy for imputing categorical columns ('most_frequent', 'constant').
    - placeholder: str, optional (default='Unknown')
        Placeholder value for 'constant' strategy in categorical columns.
    
    Returns:
    - df: pandas.DataFrame
        The dataset with imputed values.
    """
    # Handle numeric columns
    numeric_columns = df.select_dtypes(include=['number']).columns.tolist()
    if numeric_columns:
        numeric_imputer = SimpleImputer(strategy=numeric_strategy)
        df[numeric_columns] = numeric_imputer.fit_transform(df[numeric_columns])
    
    # Handle categorical columns
    categorical_columns = df.select_dtypes(include=['object']).columns.tolist()
    if categorical_columns:
        if categorical_strategy == 'constant':
            categorical_imputer = SimpleImputer(strategy='constant', fill_value=placeholder)
        else:
            categorical_imputer = SimpleImputer(strategy=categorical_strategy)
        df[categorical_columns] = categorical_imputer.fit_transform(df[categorical_columns])
    
    return df

def detect_columns(df, time_keywords=None, geo_keywords=None):
    """
    Detect key columns in the dataset to adjust analysis.
    
    Parameters:
    - df: pandas.DataFrame
        The dataset to analyze.
    - time_keywords: list of str, optional
        Keywords for identifying time-related columns. Default is ['date', 'time'].
    - geo_keywords: list of str, optional
        Keywords for identifying geospatial columns. Default is ['lat', 'long'].
    
    Returns:
    - columns_info: dict
        A dictionary containing detected column types.
    """
    # Default keywords if none are provided
    time_keywords = time_keywords or ['date', 'time']
    geo_keywords = geo_keywords or ['lat', 'long']

    # Initialize the column info dictionary
    columns_info = {
        'time_column': [],
        'geo_columns': [],
        'categorical_columns': [],
        'numeric_columns': []
    }

    # Detect time-related columns
    for keyword in time_keywords:
        time_cols = [col for col in df.columns if keyword.lower() in col.lower()]
        columns_info['time_column'].extend(time_cols)
    columns_info['time_column'] = list(set(columns_info['time_column']))  # Remove duplicates

    # Detect geospatial columns
    geo_candidates = [col for col in df.columns if any(geo in col.lower() for geo in geo_keywords)]
    if len(geo_candidates) >= 2:
        columns_info['geo_columns'] = geo_candidates[:2]  # Pick the first two candidates

    # Detect categorical and numeric columns
    columns_info['categorical_columns'] = df.select_dtypes(include=['object']).columns.tolist()
    columns_info['numeric_columns'] = df.select_dtypes(include=['number']).columns.tolist()

    return columns_info

def generate_dynamic_prompt(df):
    """
    Generate a dynamic prompt based on the dataset's structure for LLM analysis.

    Parameters:
    - df (pandas.DataFrame): The dataset to analyze.

    Returns:
    - prompt (str): A structured prompt guiding the LLM analysis.
    """
    # Detect key columns using detect_columns
    columns_info = detect_columns(df)
    
    # Construct the prompt based on detected columns
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
    
    Suggest additional steps or patterns observed in the dataset for further exploration."""
    
    print("Generated Prompt for Analysis:")
    print(prompt)
    return prompt

def perform_clustering(df, num_clusters=3):
    """Perform KMeans clustering on the dataset."""
    if len(df.select_dtypes(include=['number']).columns) > 1:
        kmeans = KMeans(n_clusters=num_clusters, random_state=42)
        df['Cluster'] = kmeans.fit_predict(df.select_dtypes(include=['number']))
        return df

def perform_pca(df):
    """Conduct PCA analysis on the dataset."""
    pca = PCA(n_components=2)
    pca_result = pca.fit_transform(df.select_dtypes(include=['number']))
    return pca.explained_variance_ratio_, pca_result

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

def perform_time_series_analysis(df, time_column):
    """Perform time series analysis on the dataset."""
    if time_column in df.columns:
        # Convert the time_column to datetime, coercing errors to NaT (not a time)
        df[time_column] = pd.to_datetime(df[time_column], errors='coerce')

        # Optional: Handle rows where time_column is NaT (if necessary)
        # df = df.dropna(subset=[time_column])  # Uncomment to drop rows where datetime conversion failed

        df.set_index(time_column, inplace=True)

        # Check if there are any numeric columns to perform rolling mean
        if df.select_dtypes(include=[np.number]).empty:
            logging.warning("No numeric columns available for rolling mean calculation.")
            return None
        else:
            # Calculate rolling mean using the first numeric column found
            first_numeric_column = df.select_dtypes(include=[np.number]).columns[0]
            df['rolling_mean'] = df[first_numeric_column].rolling(window=12).mean()  # Example for monthly data
            df['rolling_mean'].plot(title="Rolling Mean of Time Series")
            plt.show()
            return df['rolling_mean']

def perform_geospatial_analysis(df, lat_col, lon_col):
    """Perform geospatial analysis on the dataset."""
    if lat_col in df.columns and lon_col in df.columns:
        plt.figure(figsize=(10, 6))
        plt.scatter(df[lon_col], df[lat_col], alpha=0.5)
        plt.title('Geospatial Distribution of Data Points')
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.show()

def advanced_analysis(df, num_clusters=3, time_col=None, lat_col=None, lon_col=None):
    """Coordinate advanced data analysis techniques including time series and geospatial analysis."""
    df = impute_missing_values(df, numeric_strategy='mean', categorical_strategy='most_frequent')# Impute missing values before performing analysis
    column_info = detect_columns(df)  # Detect important columns for targeted analysis
    
    results = {}
    if len(df.select_dtypes(include=['number']).columns) > 1:
        df = perform_clustering(df, num_clusters)
        results['clustering'] = "Clustering completed."
        variance_ratio, components = perform_pca(df)
        results['pca'] = {"explained_variance_ratio": variance_ratio, "components": components.tolist()}
        outliers = detect_outliers(df)
        results['outliers'] = f"{len(outliers)} outliers detected."

    if column_info['time_column']:  # Check for time columns for time series analysis
        for col in column_info['time_column']:
            if col in df.columns:
                results[f'time_series_analysis_{col}'] = perform_time_series_analysis(df, col)

    if column_info['geo_columns']:  # Check for geo columns for geospatial analysis
        lat_col, lon_col = column_info['geo_columns']
        perform_geospatial_analysis(df, lat_col, lon_col)
        results['geospatial'] = "Geospatial analysis performed."

    return results

def generate_boxplots(df, output_file="outlier_boxplots.png"):
    """
    Generate boxplots for all numeric columns in the dataset and save as a single image.
    
    Parameters:
    - df: pandas.DataFrame
        The input dataset.
    - output_file: str
        The filename to save the boxplots.
    """
    numeric_columns = df.select_dtypes(include=['number']).columns.tolist()

    if not numeric_columns:
        print("No numeric columns found for generating boxplots.")
        return

    # Create a boxplot for each numeric column
    plt.figure(figsize=(15, 5 * len(numeric_columns)))  # Dynamically adjust height
    for i, column in enumerate(numeric_columns):
        try:
            plt.subplot((len(numeric_columns) + 2) // 3, 3, i + 1)
            sns.boxplot(y=df[column])
            plt.title(f'Boxplot of {column}')
            plt.xlabel("Values")
            plt.ylabel(column)
        except Exception as e:
            print(f"Error creating boxplot for column '{column}': {e}")
            continue

    plt.tight_layout()

    try:
        plt.savefig(output_file, bbox_inches='tight')  # Save as a PNG file
        print(f"Boxplots saved as {output_file}")
    except Exception as e:
        print(f"Error saving boxplots: {e}")
    finally:
        plt.close()

def extract_boxplot_insights(df):
    """
    Extract key insights from the data used to generate boxplots.

    Parameters:
    - df (pandas.DataFrame): The input dataset.

    Returns:
    - dict: A dictionary of insights for each numeric column.
    """
    insights = {}
    numeric_columns = df.select_dtypes(include=['number']).columns.tolist()

    for column in numeric_columns:
        try:
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]
            
            insights[column] = {
                "min": df[column].min(),
                "max": df[column].max(),
                "median": df[column].median(),
                "Q1": Q1,
                "Q3": Q3,
                "outlier_count": len(outliers),
            }
        except Exception as e:
            logging.error(f"Error extracting boxplot insights for {column}: {e}")
    
    return insights

def generate_heatmap(df, output_file="correlation_heatmap.png"):
    """
    Generate a heatmap for the correlation matrix of numeric columns and save as an image.
    
    Parameters:
    - df: pandas.DataFrame
        The input dataset.
    - output_file: str
        The filename to save the heatmap.
    """
    numeric_columns = df.select_dtypes(include=['number']).columns.tolist()

    if len(numeric_columns) < 2:
        print("Insufficient numeric columns for generating a heatmap.")
        return

    correlation_matrix = df[numeric_columns].corr()

    plt.figure(figsize=(10, 8))
    sns.heatmap(correlation_matrix, annot=True, fmt=".2f", cmap="coolwarm", square=True)
    plt.title("Correlation Heatmap")
    plt.xlabel("Features")
    plt.ylabel("Features")

    try:
        plt.savefig(output_file, bbox_inches='tight')  # Save as a PNG file
        print(f"Heatmap saved as {output_file}")
    except Exception as e:
        print(f"Error saving heatmap: {e}")
    finally:
        plt.close()

def extract_heatmap_insights(df):
    """
    Extract key insights from the correlation heatmap.

    Parameters:
    - df (pandas.DataFrame): The input dataset.

    Returns:
    - str: A summary of the most significant correlations.
    """
    numeric_columns = df.select_dtypes(include=['number']).columns.tolist()

    if len(numeric_columns) < 2:
        return "Not enough numeric columns for correlation analysis."

    correlation_matrix = df[numeric_columns].corr()
    sorted_correlations = correlation_matrix.unstack().sort_values(ascending=False)

    # Exclude self-correlations (diagonal)
    filtered_correlations = sorted_correlations[sorted_correlations < 1.0]
    top_positive = filtered_correlations.head(3)
    top_negative = filtered_correlations.tail(3)

    insights = "Top Correlations:\n"
    insights += "Highest Positive Correlations:\n"
    for (col1, col2), value in top_positive.items():
        insights += f"- {col1} and {col2}: {value:.2f}\n"

    insights += "Highest Negative Correlations:\n"
    for (col1, col2), value in top_negative.items():
        insights += f"- {col1} and {col2}: {value:.2f}\n"

    return insights

def generate_histograms(df, output_file="histograms.png"):
    """
    Generate histograms for numeric columns in the dataset and save as an image.
    
    Parameters:
    - df: pandas.DataFrame
        The input dataset.
    - output_file: str
        The filename to save the histograms.
    """
    numeric_columns = df.select_dtypes(include=['number']).columns.tolist()

    if not numeric_columns:
        print("No numeric columns found for generating histograms.")
        return

    plt.figure(figsize=(15, 10))  # Dynamically adjust height
    for i, column in enumerate(numeric_columns):
        try:
            plt.subplot((len(numeric_columns) + 2) // 3, 3, i + 1)
            sns.histplot(df[column], kde=True, bins=30)
            plt.title(f'Histogram of {column}')
            plt.xlabel(column)
            plt.ylabel("Frequency")
        except Exception as e:
            print(f"Error creating histogram for column '{column}': {e}")
            continue

    plt.tight_layout()

    try:
        plt.savefig(output_file, bbox_inches='tight')  # Save as a PNG file
        print(f"Histograms saved as {output_file}")
    except Exception as e:
        print(f"Error saving histograms: {e}")
    finally:
        plt.close()

def extract_histogram_insights(df):
    """
    Extract key insights from histograms.

    Parameters:
    - df (pandas.DataFrame): The input dataset.

    Returns:
    - dict: A dictionary of insights for each numeric column.
    """
    insights = {}
    numeric_columns = df.select_dtypes(include=['number']).columns.tolist()

    for column in numeric_columns:
        try:
            skewness = df[column].skew()
            kurtosis = df[column].kurt()
            insights[column] = {
                "mean": df[column].mean(),
                "std_dev": df[column].std(),
                "skewness": skewness,
                "kurtosis": kurtosis,
                "distribution_type": "Normal" if abs(skewness) < 0.5 else "Skewed",
            }
        except Exception as e:
            logging.error(f"Error extracting histogram insights for {column}: {e}")

    return insights

def generate_visualizations(df):
    """
    Generate visualizations, extract insights, resize them for LLM compatibility, and include metadata.

    Parameters:
    - df: pandas.DataFrame
        The dataset to analyze.

    Returns:
    - List of tuples containing:
        1. Original image file paths (validated).
        2. Resized image objects (BytesIO) for sending to the LLM.
        3. Textual descriptions of the visualizations.
        4. Extracted insights from the charts.
    """
    visualization_files = []
    visualizations_metadata = []
    extracted_insights = []

    try:
        # Step 1: Generate Visualizations
        boxplot_file = "outlier_boxplots.png"
        generate_boxplots(df, boxplot_file)
        visualization_files.append(boxplot_file)
        visualizations_metadata.append("Boxplots: Summary of numeric column distributions, highlighting potential outliers.")
        extracted_insights.append(extract_boxplot_insights(df))

        heatmap_file = "correlation_heatmap.png"
        generate_heatmap(df, heatmap_file)
        visualization_files.append(heatmap_file)
        visualizations_metadata.append("Heatmap: Correlation matrix of numeric columns, showing relationships between variables.")
        extracted_insights.append(extract_heatmap_insights(df))

        histogram_file = "histograms.png"
        generate_histograms(df, histogram_file)
        visualization_files.append(histogram_file)
        visualizations_metadata.append("Histograms: Frequency distribution of numeric columns, including potential data patterns.")
        extracted_insights.append(extract_histogram_insights(df))

        logging.info("All visualizations generated successfully.")

        # Step 2: Validate Original Visualization Files
        validated_files, missing_files = validate_visualizations(visualization_files)
        if missing_files:
            logging.warning(f"Some visualizations could not be validated: {', '.join(missing_files)}")
            visualization_files = validated_files  # Keep only valid files

        # Step 3: Resize Images for LLM Compatibility (In-Memory Only)
        resized_images = []
        for vis_file in visualization_files:
            try:
                resized_image = resize_image_for_llm_memory(vis_file)
                if resized_image:
                    resized_images.append(resized_image)
                else:
                    logging.warning(f"Failed to resize image: {vis_file}")
            except Exception as e:
                logging.error(f"Error resizing image {vis_file}: {e}")

        # Combine and Return Results
        result = {
                "validated_files": validated_files,
                "resized_images": resized_images,
                "metadata": visualizations_metadata,
                "insights": extracted_insights
        }
        return result

    except Exception as e:
        logging.error(f"Error generating visualizations: {e}")
        return []


def validate_visualizations(files_to_check):
    """
    Validate the existence of visualization files.

    Parameters:
    - files_to_check (list of str): List of file paths expected to exist.

    Returns:
    - validated_files (list of str): List of files that exist.
    - missing_files (list of str): List of files that are missing.
    """
    validated_files = [file for file in files_to_check if os.path.exists(file)]
    missing_files = [file for file in files_to_check if file not in validated_files]

    # Log validation results
    if missing_files:
        print(f"Missing visualization files: {', '.join(missing_files)}")
    else:
        print(f"All visualizations validated successfully: {', '.join(validated_files)}")

    return validated_files, missing_files

def resize_image_for_llm_memory(image_path, target_size=(512, 512)):
    """
    Resize an image to the required size for LLM compatibility, 
    return it as a base64-encoded string for sending to the LLM.
    
    Parameters:
    - image_path (str): The path to the image file.
    - target_size (tuple): Desired dimensions (default: 512x512 pixels).
    
    Returns:
    - str: Base64-encoded resized image, or None if an error occurs.
    """
    try:
        # Open the image using PIL
        with Image.open(image_path) as img:
            # Resize the image to the target size
            resized_img = img.resize(target_size)

            # Convert the resized image to a BytesIO object
            image_memory = BytesIO()
            resized_img.save(image_memory, format="PNG")
            image_memory.seek(0)  # Reset the stream position for reading

            # Convert the image in memory to base64 for API compatibility
            encoded_image = base64.b64encode(image_memory.getvalue()).decode('utf-8')

            logging.info(f"Image resized and encoded to base64 successfully: {image_path}")
            return encoded_image
    except FileNotFoundError:
        logging.error(f"File not found: {image_path}")
        return None
    except Exception as e:
        logging.error(f"Error resizing and encoding image {image_path}: {e}")
        return None

def upload_png_files(directory="."):
    """
    Read and encode all .png files in the specified directory.

    Parameters:
    - directory: str
        Path to the directory to scan for PNG files (default: current directory).

    Returns:
    - dict: A dictionary with filenames as keys and base64-encoded content as values.
    """
    try:
        png_files = [f for f in os.listdir(directory) if f.endswith('.png')]
        if not png_files:
            logging.warning("No PNG files found to upload.")
            return {}

        encoded_files = {}
        for file in png_files:
            try:
                with open(os.path.join(directory, file), "rb") as f:
                    encoded_files[file] = base64.b64encode(f.read()).decode('utf-8')
                logging.info(f"Successfully encoded: {file}")
            except Exception as e:
                logging.error(f"Failed to encode {file}: {e}")
        return encoded_files

    except Exception as e:
        logging.error(f"Error accessing directory {directory}: {e}")
        return {}

def analyze_visualization_with_llm(image_data, metadata, extracted_insights, filename):
    """
    Send a visualization image (in-memory) and its metadata to the LLM for interpretation or analysis.
    If the image encoding fails or token size is too large, send metadata and insights only.

    Parameters:
    - image_data: BytesIO or str
        In-memory image object (resized image) or a base64-encoded string.
    - metadata: str
        Description or insights about the visualization.
    - extracted_insights: str
        Extracted insights from the chart (e.g., boxplot insights, heatmap correlations).
    - filename: str
        The original dataset filename for context in the request.

    Returns:
    - dict: Analysis results including LLM response and metadata.
    """
    try:
        # Check if the image_data is a BytesIO object or a base64-encoded string
        if isinstance(image_data, BytesIO):
            # Extract bytes if it's a BytesIO object
            image_bytes = image_data.getvalue()
            encoded_image = base64.b64encode(image_bytes).decode('utf-8')  # Ensure it's base64 encoded
        elif isinstance(image_data, str):  # If it's already a base64 string
            encoded_image = image_data  # It's already base64, no need to decode
        else:
            encoded_image = None  # In case the image data is not valid

        # Prepare the payload for the LLM request
        data = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are a data analysis assistant."},
                {
                    "role": "user",
                    "content": (
                        f"The following chart is part of an analysis on the dataset `{filename}`.\n"
                        f"Metadata:\n{metadata}\n"
                        f"Extracted Insights:\n{extracted_insights}\n"
                        f"The image data is included below for your analysis."
                    ),
                },
            ],
            "temperature": 0.5,
            "functions": [
                {
                    "name": "analyze_chart",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            #"image_bytes": {"type": "string", "description": "Base64 or Hex-encoded image data"},
                            "metadata": {"type": "string", "description": "Chart description or additional context"},
                            "extracted_insights": {"type": "string", "description": "Extracted insights from the chart"}
                        },
                        "required": ["metadata", "extracted_insights"]
                    }
                }
            ],
        }

        # Add image data to payload if encoding is successful
        if encoded_image:
            data["functions"][0]["parameters"]["properties"]["image_bytes"] = encoded_image
        else:
            # If image encoding fails, send metadata and insights as fallback
            data["functions"][0]["parameters"]["properties"].pop("image_bytes", None)
            logging.warning("Image encoding failed, sending metadata and insights.")

        # Check if token size is too large before sending to LLM
        total_tokens = len(json.dumps(data))  # Calculate the size of the payload
        MAX_TOKEN_LIMIT = 10000  # Max token limit for the model (adjust as necessary)

        if total_tokens > MAX_TOKEN_LIMIT:
            logging.warning(f"Payload size exceeds token limit of {MAX_TOKEN_LIMIT}. Skipping image data.")
            data["functions"][0]["parameters"]["properties"].pop("image_bytes", None)  # Remove image data
            data["messages"][1]["content"] = f"Token limit exceeded. Here are the insights:\n{extracted_insights}"

        # Make the request to the LLM
        response = make_openai_request(data, filename)

        # Validate and process the response
        if response and "choices" in response:
            analysis_result = response["choices"][0]["message"]["content"]
            logging.info(f"LLM Analysis Response: {analysis_result}")
            return {"metadata": metadata, "llm_response": analysis_result}
        else:
            logging.error(f"Invalid LLM response: {response}")
            return {"metadata": metadata, "llm_response": "No valid response from LLM."}

    except Exception as e:
        logging.error(f"Error analyzing visualization with LLM: {e}")
        return {"metadata": metadata, "llm_response": f"Error: {e}"}

def narrate_story(summary, insights, advanced_results, visualization_data, filename):
    """
    Generate a narrative story using the OpenAI API, incorporating analysis results, insights, and visualizations.
    
    Parameters:
    - summary: str
        The dataset summary statistics from basic analysis.
    - insights: dict
        Key insights from basic analysis.
    - advanced_results: dict
        Results from advanced analysis (e.g., clustering, PCA, outliers).
    - visualization_data: list of tuples
        List containing (validated_file_path, metadata, llm_response) for visualizations.
    - filename: str
        The name of the dataset file for contextual reference.

    Returns:
    - markdown: str
        The complete Markdown narrative generated by the LLM.
    """
    # Step 1: Build Markdown structure
    markdown = f"# Analysis Report for `{filename}`\n\n"
    markdown += "## Dataset Overview\n"
    markdown += f"- **Number of Rows**: {insights.get('num_rows', 'N/A')}\n"
    markdown += f"- **Number of Columns**: {insights.get('num_columns', 'N/A')}\n"
    markdown += f"- **Columns**:\n  - " + "\n  - ".join(insights['column']) + "\n\n"

    markdown += "## Sample Data\n"
    markdown += f"{insights.get('sample_data', 'No sample data available')}\n\n"

    markdown += "## Key Insights from Analysis\n"
    markdown += "### Basic Analysis\n"
    markdown += f"- **Missing Values**:\n{insights['missing_values']}\n\n"
    markdown += "- **Outliers**:\n"
    for outlier in insights['outliers']:
        markdown += f"  - Column `{outlier['column']}`: {outlier['outlier_count']} outliers detected (Range: {outlier['lower_bound']} to {outlier['upper_bound']})\n"

    markdown += "### Advanced Analysis\n"
    if advanced_results.get('clustering'):
        markdown += f"- **Clustering**: {advanced_results['clustering']}\n"
    if advanced_results.get('pca'):
        pca_info = advanced_results['pca']
        markdown += f"- **PCA**: Explained Variance Ratios: {pca_info['explained_variance_ratio']}\n"
    if advanced_results.get('outliers'):
        markdown += f"- **Outliers**: {advanced_results['outliers']}\n"

    if advanced_results.get('time_series'):
        markdown += "- **Time Series Analysis**: Time-based patterns observed. See time-series plots.\n"
    if advanced_results.get('geospatial'):
        markdown += "- **Geospatial Analysis**: Geospatial patterns observed in the data. See geospatial plots.\n\n"

    # Step 2: Add Visualizations and Insights
    markdown += "## Visualizations and Insights\n"
    for entry in visualization_data:  # Iterate over the list of dictionaries
        image_path = entry["validated_file"]
        metadata = entry["metadata"]
        llm_response = entry["llm_response"]
        markdown += f"![{os.path.basename(image_path)}]({image_path})\n"
        markdown += f"- **Chart Description**: {metadata}\n"
        markdown += f"- **LLM Analysis**: {llm_response}\n\n"

    # Step 3: Add Recommendations
    markdown += "## Recommendations and Next Steps\n"
    markdown += "- **Data Quality**: Address missing values and outliers for cleaner analysis.\n"
    markdown += "- **Future Exploration**: Use clustering and PCA insights for segmentation and dimensionality reduction.\n"
    markdown += "- **Operational Use**: Leverage time-series patterns for forecasting and geospatial trends for targeted decision-making.\n"

    # Step 4: Send to LLM for Refinement
    prompt = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are an expert data analyst creating a Markdown-formatted report."},
            {"role": "user", "content": f"Refine this Markdown narrative:\n{markdown}"}
        ],
        "temperature": 0.5
    }

    try:
        response = make_openai_request(prompt, filename)
        if response and response.get("choices"):
            markdown = response['choices'][0]['message']['content']
            logging.info("Final Markdown narrative generated successfully.")
        else:
            logging.warning("LLM did not return a valid response. Using initial Markdown.")
    except Exception as e:
        logging.error(f"Error interacting with LLM: {e}. Using initial Markdown.")

    # Step 5: Save Markdown
    try:
        with open("README.md", "w") as f:
            f.write(markdown)
        logging.info("Narrative saved to README.md successfully.")
    except Exception as e:
        logging.error(f"Error saving README.md: {e}")

    return markdown

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
        # Step 1: Load the dataset
        df = load_data(args.filename)
        print(f"Dataset loaded successfully with {len(df)} rows and {len(df.columns)} columns.")

        # Validate the dataset
        if df.empty:
            raise ValueError("The dataset is empty. Please provide a valid dataset.")

        # Step 2: Perform basic analysis
        summary, insights = basic_analysis(df)
        print("Basic analysis completed.")

        # Step 3: Perform advanced analysis
        advanced_results = advanced_analysis(df)
        print("Advanced analysis completed.")

        # Step 4: Generate visualizations, resize, and extract insights
        visualization_data = generate_visualizations(df)
        print(f"Visualizations generated successfully. Insights extracted from charts.")


        # Step 5: Analyze visualizations with LLM
        llm_feedback = []

        # Access dictionary keys directly
        for i in range(len(visualization_data["validated_files"])):  # Assuming all lists are of the same length
            validated_file = visualization_data["validated_files"][i]
            resized_image = visualization_data["resized_images"][i]
            metadata = visualization_data["metadata"][i]
            extracted_insights = visualization_data["insights"][i]
            
            # Process each visualization
            feedback = analyze_visualization_with_llm(resized_image, metadata, extracted_insights, args.filename)  # Include extracted_insights
            llm_feedback.append({
                "validated_file": validated_file,
                "metadata": metadata,
                "llm_response": feedback["llm_response"],
                "extracted_insights": extracted_insights
            })

        print("Visualization analysis with LLM completed.")

        # Step 6: Generate narrative using insights, advanced results, and visualization feedback
        markdown = narrate_story(
            summary=summary,
            insights=insights,
            advanced_results=advanced_results,
            visualization_data=llm_feedback,
            filename=args.filename
        )
        print("Narrative generated successfully.")

        # Step 7: Save outputs
        save_outputs(markdown)
        print("Outputs saved successfully.")

        # Step 8: Organize files into a folder
        organize_files_into_folder(args.filename[:-4])
        print(f"All outputs organized into folder: {args.filename[:-4]}")

    except Exception as e:
        logging.error(f"An error occurred during execution: {e}")

if __name__ == "__main__":
    main()





