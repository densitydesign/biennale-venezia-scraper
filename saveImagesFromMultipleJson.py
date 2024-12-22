import os
import glob
import json
import requests
from urllib.parse import urlparse, parse_qs

def download_images_from_folder(json_folder_path):
    """Iterate over all JSON files in `json_folder_path` and download images
       based on the 'c' parameter in the 'imageUrl' field.
    """
    # Folder where images will be saved
    output_folder = 'output_imgs'
    os.makedirs(output_folder, exist_ok=True)
    
    # Find all JSON files in the specified folder
    json_files = glob.glob(os.path.join(json_folder_path, '*.json'))
    if not json_files:
        print(f"No JSON files found in folder: {json_folder_path}")
        return
    
    # Iterate over each JSON file
    for json_file in json_files:
        print(f"Processing file: {json_file}")
        
        # Load the JSON array
        with open(json_file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)  # Should be a list of items
            except json.JSONDecodeError as e:
                print(f"Failed to parse {json_file}: {e}")
                continue
        
        # Iterate over each item (object) in the JSON array
        for index, item in enumerate(data):
            image_url = item.get('imageUrl')
            if not image_url:
                print(f"  [Skipping] No 'imageUrl' in item {index} of {json_file}")
                continue
            
            # Extract the 'c' value from the query string
            parsed_url = urlparse(image_url)
            query_params = parse_qs(parsed_url.query)
            c_value = query_params.get('c', [''])[0]  # If 'c' not present, this will be ''
            
            if not c_value:
                print(f"  [Skipping] No 'c' parameter found in URL: {image_url}")
                continue
            
            # Download the image
            try:
                response = requests.get(image_url, timeout=10)
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"  [Error] Failed to download {image_url}: {e}")
                continue
            
            # Save the image using the 'c' value as filename (e.g., 25453.jpg)
            filename = os.path.join(output_folder, f"{c_value}.jpg")
            with open(filename, 'wb') as img_file:
                img_file.write(response.content)
            
            print(f"  [Saved] {image_url} => {filename}")

if __name__ == "__main__":
    # Change 'output' to the path containing your JSON files if needed
    download_images_from_folder('output')