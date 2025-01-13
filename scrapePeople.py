#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script: scrape_people.py

Requirements:
    - Python 3.6 or later
    - requests >= 2.0
    - beautifulsoup4 >= 4.0

Usage:
    1. Put this script anywhere accessible.
    2. Make sure you have a folder named 'output' with JSON files in it.
    3. Run the script:  python scrape_people.py
    4. The results will be saved into a folder named 'output_people'.
"""

import os
import csv
import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs

# Adjust this if you want a short pause between HTTP requests
REQUEST_DELAY = 0.5

OUTPUT_FOLDER = "output"
PEOPLE_FOLDER = "output_people"

# Filenames for output CSVs
PERSON_IMAGE_CSV = "person_image.csv"
PERSON_INFO_CSV = "person_info.csv"


def ensure_folder_exists(folder_path):
    """Create the folder if it doesn't exist."""
    if not os.path.isdir(folder_path):
        os.makedirs(folder_path)


def load_processed_person_image(csv_path):
    """
    Reads the already processed (image_code, person_code) pairs from person_image.csv
    to avoid duplicates if the script restarts.
    """
    processed = set()
    if os.path.isfile(csv_path):
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 2:
                    image_code, person_code = row[0], row[1]
                    processed.add((image_code, person_code))
    return processed


def load_processed_person_info(csv_path):
    """
    Reads the already processed person codes from person_info.csv
    to avoid duplicates if the script restarts.
    Returns a dict mapping code -> (label, full_url).
    """
    processed = {}
    if os.path.isfile(csv_path):
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 3:
                    p_code, p_label, p_full_url = row[0], row[1], row[2]
                    processed[p_code] = (p_label, p_full_url)
    return processed


def append_to_csv(csv_path, row):
    """Append a single row to CSV (create file if needed)."""
    with open(csv_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(row)


def get_image_code_from_url(image_url):
    """
    Extracts the code (e.g., c=134756) from imageUrl.
    Example:
        https://asacdati.labiennale.org/it/fondi/fototeca/getimg.php?c=134756&k=thumb
        returns '134756'
    """
    parsed = urlparse(image_url)
    qs = parse_qs(parsed.query)
    # We assume the code is in the parameter 'c'.
    # If it's not present or has a different structure, you may need to adjust.
    if 'c' in qs and len(qs['c']) > 0:
        return qs['c'][0]
    return ""


def get_person_code_label_and_url(soup, base_url):
    """
    From the BeautifulSoup of the page, find all <a> tags whose href contains
    'ricerca/ricerca-persona.php?p='.
    Returns a list of tuples: (person_code, label, full_url).
    """
    result = []
    # Select all anchors whose href has 'ricerca/ricerca-persona.php?p=' in it
    links = soup.select('a[href*="ricerca/ricerca-persona.php?p="]')
    for link in links:
        href = link.get("href", "")
        label = link.get_text(strip=True)

        # Build absolute URL
        absolute_url = urljoin(base_url, href)

        # Extract person code from the query param p
        parsed = urlparse(absolute_url)
        qs = parse_qs(parsed.query)
        if 'p' in qs and len(qs['p']) > 0:
            p_code = qs['p'][0]
            result.append((p_code, label, absolute_url))
    return result


def main():
    ensure_folder_exists(PEOPLE_FOLDER)

    # Paths to the two output CSV files
    person_image_path = os.path.join(PEOPLE_FOLDER, PERSON_IMAGE_CSV)
    person_info_path = os.path.join(PEOPLE_FOLDER, PERSON_INFO_CSV)

    # Load already processed data (for resuming)
    processed_person_image = load_processed_person_image(person_image_path)
    processed_person_info = load_processed_person_info(person_info_path)

    # Get all JSON files in 'output' folder and sort them alphabetically
    json_files = [f for f in os.listdir(OUTPUT_FOLDER) if f.lower().endswith(".json")]
    json_files.sort()  # Sort in place alphabetically

    for json_file in json_files:
        json_path = os.path.join(OUTPUT_FOLDER, json_file)
        print("Processing JSON file:", json_path)

        with open(json_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                print("WARNING: Could not decode JSON in:", json_path)
                continue

            if not isinstance(data, list):
                print("WARNING: JSON file does not contain a list:", json_path)
                continue

            # Each item in data has title, titleUrl, imageUrl, etc.
            for item in data:
                title_url = item.get("titleUrl")
                image_url = item.get("imageUrl")
                if not title_url or not image_url:
                    continue

                # Extract code from the imageUrl
                image_code = get_image_code_from_url(image_url)
                if not image_code:
                    # If there's no code, skip
                    continue

                # We'll fetch the page at title_url and parse for persona links
                print("  Visiting page:", title_url)
                try:
                    time.sleep(REQUEST_DELAY)  # be kind to the server
                    resp = requests.get(title_url, timeout=10)
                    resp.raise_for_status()
                except requests.RequestException as e:
                    print("  Error fetching", title_url, "->", e)
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")
                # Find all person links
                people_links = get_person_code_label_and_url(soup, title_url)
                print("  Found {} people on this page.".format(len(people_links)))

                # For each person found on this page:
                for (p_code, p_label, p_full_url) in people_links:
                    # 1) Write to person_image.csv if not done before
                    if (image_code, p_code) not in processed_person_image:
                        append_to_csv(person_image_path, [image_code, p_code])
                        processed_person_image.add((image_code, p_code))

                    # 2) Write to person_info.csv if not done before
                    if p_code not in processed_person_info:
                        print("  New person found:", p_code, p_label)
                        append_to_csv(person_info_path, [p_code, p_label, p_full_url])
                        processed_person_info[p_code] = (p_label, p_full_url)

    print("Done. Results stored in:", PEOPLE_FOLDER)


if __name__ == "__main__":
    main()