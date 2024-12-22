#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json

def combine_json_files(input_dir, output_file):
    """
    Read all JSON files from input_dir (each expected to be an array of objects),
    combine them into a single list, and write that list to output_file.
    """
    all_items = []

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".json"):
            full_path = os.path.join(input_dir, filename)
            with open(full_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Each file is a list of objects, so we extend the main list
                all_items.extend(data)

    with open(output_file, "w", encoding="utf-8") as out:
        json.dump(all_items, out, ensure_ascii=False, indent=2)

    print("Combined {} JSON files into '{}'.".format(len(os.listdir(input_dir)), output_file))


def main():
    # Directory containing the JSON files
    input_dir = "output"
    # File where we want to save the merged JSON data
    output_file = "combined_data.json"

    combine_json_files(input_dir, output_file)

if __name__ == "__main__":
    main()