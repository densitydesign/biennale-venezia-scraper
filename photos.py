import os
import sys
import json
import requests
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup

def scrape_page(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        print("Error fetching URL {}: {}".format(url, e))
        return None

    base_url = url
    soup = BeautifulSoup(response.text, 'html.parser')
    
    results = []
    # Loop through each "risultato"
    for result in soup.select('.risultato'):
        # Extract the first image
        img_tag = result.select_one('.scheda-foto img')
        if img_tag and img_tag.get('src'):
            image_url = urljoin(base_url, img_tag['src'])
        else:
            image_url = ''

        # Extract title and title URL
        h3_link = result.select_one('h3 a')
        if h3_link:
            title = h3_link.get_text(strip=True)
            title_url = urljoin(base_url, h3_link['href'])
        else:
            title = ''
            title_url = ''

        record = {
            'title': title,
            'titleUrl': title_url,
            'imageUrl': image_url,
            'details': []
        }

        # Extract rows of data
        rows = result.select('.tabella .riga')
        for row in rows:
            definition = row.select_one('.def')
            definition_text = definition.get_text(strip=True) if definition else ''

            dato_div = row.select_one('.dato')
            if not dato_div:
                continue

            link = dato_div.select_one('a')
            if link:
                # If dato contains a link
                value = link.get_text(strip=True)
                raw_link = urljoin(base_url, link['href'])
                parsed_url = urlparse(raw_link)
                query_params = parse_qs(parsed_url.query)
                
                scheda_param = query_params.get('scheda', [None])[0]
                scheda_link = None
                if scheda_param:
                    # Reconstruct URL with only the 'scheda' param
                    scheda_link = "{}://{}{}?scheda={}".format(
                        parsed_url.scheme, 
                        parsed_url.netloc, 
                        parsed_url.path, 
                        scheda_param
                    )

                record['details'].append({
                    'definition': definition_text,
                    'value': value,
                    'originalLink': raw_link,
                    'schedaParam': scheda_param,
                    'schedaLink': scheda_link
                })
            else:
                # If dato contains just text
                value = dato_div.get_text(strip=True)
                # If definition is "Soggetto", split by comma
                if definition_text.lower() == 'soggetto':
                    value = [v.strip() for v in value.split(',')]
                
                record['details'].append({
                    'definition': definition_text,
                    'value': value
                })

        results.append(record)

    return results

def main():
    # Parse command line arguments
    if len(sys.argv) != 3:
        print("Usage: script.py <start_page> <end_page>")
        sys.exit(1)

    try:
        start_page = int(sys.argv[1])
        end_page = int(sys.argv[2])
    except ValueError:
        print("Please provide integer values for start_page and end_page.")
        sys.exit(1)

    # Ensure the output directory exists
    os.makedirs('output', exist_ok=True)

    base_url = "https://asacdati.labiennale.org/it/fondi/fototeca/sem-ricerca.php?cerca=1&p="

    for p in range(start_page, end_page + 1):
        page_url = "{}{}".format(base_url, p)
        print("Scraping page {}: {}".format(p, page_url))
        
        data = scrape_page(page_url)
        if data is not None:
            if len(data) > 0:
                # Save to JSON file
                output_file = os.path.join('output', "page_{}.json".format(p))
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print("Page {} scraped successfully, data saved to {}".format(p, output_file))
            else:
                print("Page {}: No results found.".format(p))
        else:
            print("Page {}: Failed to scrape page.".format(p))

if __name__ == "__main__":
    main()