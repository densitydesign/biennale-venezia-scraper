import os
import json
import logging
import requests
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    filename='scraping.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

def scrape_page(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Error fetching URL {url}: {e}")
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
                    # Use underscore in 'ava_ricerca' as specified in the original instructions?
                    # The user wrote it previously as "ava_ricerca" but original snippet was "ava-ricerca.php".
                    # We'll assume "ava_ricerca.php" as per previous instructions or original snippet:
                    scheda_link = f"https://asacdati.labiennale.org/it/attivita/artivisive/ava-ricerca.php?scheda={scheda_param}"

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
    # Ensure the output directory exists
    os.makedirs('output', exist_ok=True)

    start_page = 1
    end_page = 10  # Adjust as needed

    # Base URL without the page parameter
    base_url = "https://asacdati.labiennale.org/it/fondi/fototeca/sem-ricerca.php?cerca=1&p="

    for p in range(start_page, end_page + 1):
        page_url = f"{base_url}{p}"
        logging.info(f"Scraping page {p}: {page_url}")
        
        data = scrape_page(page_url)
        if data is not None:
            if len(data) > 0:
                # Save to JSON file
                output_file = os.path.join('output', f'page_{p}.json')
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                logging.info(f"Page {p} scraped successfully, data saved to {output_file}")
            else:
                logging.warning(f"Page {p}: No results found.")
        else:
            logging.error(f"Page {p}: Failed to scrape page.")

if __name__ == "__main__":
    main()