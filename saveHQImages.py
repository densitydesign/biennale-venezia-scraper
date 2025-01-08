import os
import glob
import json
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from PIL import Image
from io import BytesIO

def download_and_resize_images(json_folder_path):
    """Download images from JSON files, modify URL parameter 'k', resize them, and save them in the 'img_224' folder."""
    # Folders for original and resized images
    output_folder = 'output_imgs'
    resized_folder = 'img_224'
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(resized_folder, exist_ok=True)

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

        # Iterate over each item in the JSON array
        for index, item in enumerate(data):
            image_url = item.get('imageUrl')
            if not image_url:
                print(f"  [Skipping] No 'imageUrl' in item {index} of {json_file}")
                continue

            # Parse and modify the URL
            parsed_url = urlparse(image_url)
            query_params = parse_qs(parsed_url.query)

            # Change the 'k' parameter to 'image'
            query_params['k'] = ['image']
            modified_query = urlencode(query_params, doseq=True)

            # Reconstruct the modified URL
            modified_url = urlunparse(
                (parsed_url.scheme, parsed_url.netloc, parsed_url.path, parsed_url.params, modified_query, parsed_url.fragment)
            )

            # Extract the 'c' value from the query string
            c_value = query_params.get('c', [''])[0]  # If 'c' not present, this will be ''

            if not c_value:
                print(f"  [Skipping] No 'c' parameter found in URL: {image_url}")
                continue

            # Download the image
            try:
                response = requests.get(modified_url, timeout=10)
                response.raise_for_status()
                image = Image.open(BytesIO(response.content))
            except (requests.RequestException, IOError) as e:
                print(f"  [Error] Failed to download or process {modified_url}: {e}")
                continue

            # Resize the image
            try:
                max_dimension = 224
                image.thumbnail((max_dimension, max_dimension), Image.ANTIALIAS)  # Use ANTIALIAS for compatibility
                resized_path = os.path.join(resized_folder, f"{c_value}.jpg")
                image.save(resized_path, "JPEG", quality=80)
                print(f"  [Resized and Saved] {modified_url} => {resized_path}")
            except Exception as e:
                print(f"  [Error] Failed to resize/save image {c_value}: {e}")
                continue

if __name__ == "__main__":
    # Change 'output' to the path containing your JSON files if needed
    download_and_resize_images('output')