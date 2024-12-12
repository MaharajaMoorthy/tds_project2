# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas",
#   "seaborn",
#   "matplotlib",
#   "requests",
#   "scikit-learn",
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
    token = os.environ.get("AIPROXY_TOKEN")
    if not token:
        raise EnvironmentError("AIPROXY_TOKEN environment variable is not set.")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    cache_key = hash_request(data, filename)

    # Check cache
    if cache_key in CACHE:
        print("Using cached response.")
        return CACHE[cache_key]

    # Make API call
    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        result = response.json()
        CACHE[cache_key] = result  # Save to cache
        save_cache()  # Persist cache to file
        return result
    else:
        raise RuntimeError(f"OpenAI API request failed: {response.status_code} {response.text}")

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
    Move all .png and .md files in the current directory into a specified folder.

    Parameters:
    folder_name (str): Name of the folder to create and move files into.
    """
    current_dir = os.getcwd()  # Get the current directory
    target_dir = os.path.join(current_dir, folder_name)

    # Create the target folder if it doesn't exist
    os.makedirs(target_dir, exist_ok=True)

    # List all files in the current directory
    files_to_move = [file for file in os.listdir(current_dir) if file.endswith(('.png', '.md'))]

    # Move each file to the target directory
    for file in files_to_move:
        src_path = os.path.join(current_dir, file)
        dest_path = os.path.join(target_dir, file)
        shutil.move(src_path, dest_path)
        print(f"Moved: {file} -> {folder_name}")

    if not files_to_move:
        print("No .png or .md files found to move.")

def basic_analysis(df):
    """Perform basic analysis on the dataset."""
    df_description = df.describe(include='all').to_markdown()
    insights = {
        "missing_values": df.isnull().sum().to_markdown(),
        "outliers": detect_outliers(df),
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

def ask_llm_for_columns_and_visualizations(df, filename):
    """Ask the LLM to recommend relevant columns and visualizations."""
    prompt = f"""
    You are analyzing a dataset in the current directory with the following columns:
    {', '.join(df.columns)}

    Based on the dataset, provide Python code for visualizations such as correlation matrices and outlier boxplots. Save the visualizations as files and do not display them. Format the response as:
    {{
        "columns": ["col1", "col2", "col3"],
        "visualizations": ["code_for_visualization_1", "code_for_visualization_2"]
    }}
    """
    cache_key = hash_request(prompt, filename)

    # Check if the prompt response is cached
    if cache_key in CACHE:
        print("Using cached response.")
        content = CACHE[cache_key]["choices"][0]["message"]["content"]
        return json.loads(content)

    token = os.getenv("AIPROXY_TOKEN")
    if not token:
        raise EnvironmentError("AIPROXY_TOKEN environment variable is not set.")

    url = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
    response = requests.post(
        url,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        },
        json={
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": "Provide Python code for visualizations that can help understand the relationships in the data provided. Provide the response in JSON format without escape characters."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        }
    )

    if response.status_code != 200:
        raise RuntimeError(f"Error from LLM API: {response.status_code} {response.text}")

    response_data = response.json()
    CACHE[cache_key] = response_data
    save_cache()
    print("Response cached.")

    content = response_data["choices"][0]["message"]["content"]
    return json.loads(content)

def generate_visualizations(df, filename):
    """
    Generate visualizations for the dataset, including boxplots, heatmaps, and histograms.
    """
    numeric_columns = df.select_dtypes(include=['number']).columns.tolist()

    if not numeric_columns:
        print("No numeric columns found for generating visualizations.")
        return

    # Generate Boxplots
    print("Generating boxplots...")
    generate_boxplots(df, 'outlier_boxplots.png')

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
            continue

    # Save the boxplots to a file
    plt.tight_layout()
    try:
        plt.savefig(output_file, bbox_inches='tight')
        print(f"Boxplots saved as {output_file}")
    except Exception as e:
        print(f"Error saving boxplots: {e}")
    finally:
        plt.close()

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

        # Perform basic analysis
        summary, insights = basic_analysis(df)
        print("Basic analysis completed.")

        # Generate visualizations
        generate_visualizations(df, args.filename)
        print("Visualizations generated successfully.")

        # Generate narrative
        markdown = narrate_story(summary, insights, args.filename)
        print("Narrative generated successfully.")

        # Save outputs
        save_outputs(markdown)
        print("Outputs saved successfully.")

        # Organize files into a folder
        organize_files_into_folder(args.filename[:-4])
        print(f"All outputs organized into folder: {args.filename[:-4]}")

    except Exception as e:
        print(f"An error occurred during execution: {e}")


if __name__ == "__main__":
    main()

