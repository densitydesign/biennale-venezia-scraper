import os
import json
import requests
from urllib.parse import urlparse, parse_qs

def download_images_from_json(json_file_path):
    # Load the JSON data
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Create output folder if it doesn't exist
    output_folder = 'output_imgs'
    os.makedirs(output_folder, exist_ok=True)

    # Iterate over the items in the JSON
    for index, item in enumerate(data):
        image_url = item.get('imageUrl')
        if not image_url:
            print(f"Item at index {index} does not have 'imageUrl'. Skipping.")
            continue

        # Parse the 'c' value from the URL query string
        parsed_url = urlparse(image_url)
        query_params = parse_qs(parsed_url.query)  # returns a dict: {'c': ['25453'], 'k': ['thumb']}
        c_value = query_params.get('c', [''])[0]   # Extract 'c' parameter's value or an empty string if not found

        if not c_value:
            # If there's no 'c' param, we could skip or choose a default naming
            print(f"No 'c' parameter found in URL {image_url}, skipping.")
            continue

        try:
            print(f"Downloading image from {image_url}...")
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to download {image_url}. Error: {e}")
            continue

        # Use the 'c' value as the filename
        # e.g. 25453.jpg
        filename = os.path.join(output_folder, f"{c_value}.jpg")

        # Save the image data to the file
        with open(filename, 'wb') as img_file:
            img_file.write(response.content)

        print(f"Saved image to {filename}")

if __name__ == "__main__":
    # Replace 'my_images.json' with the path to your JSON file
    download_images_from_json('combined_data.json')