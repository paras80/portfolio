import time
import re
import json
import requests
from bs4 import BeautifulSoup

def load_all_product_ids():
    """
    Simulates clicking the "Load More" button by issuing a POST request for each page.
    The adjusted payload and parsing logic assume that the POST endpoint returns an HTML
    snippet containing product links with hrefs like "product_details?id=...".
    """
    # Adjusted endpoint – typically sites use a separate URL for load-more content.
    base_url = "https://www.hmtwatches.in/search/loadMore"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    page = 1
    product_ids = set()
    
    while True:
        # Adjust the payload based on the actual POST request parameters observed.
        payload = {
            'keys': '%25',  # using %25 as a wildcard search key
            'page': str(page),
            'limit': 20     # assuming 20 products are returned per page; adjust if needed
        }
        
        print(f"POST request for page {page} ...")
        response = requests.post(base_url, data=payload, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch page {page}. Status code: {response.status_code}")
            break
        
        # Parse the returned HTML snippet to extract product links
        soup = BeautifulSoup(response.text, 'html.parser')
        new_ids = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if "product_details?id=" in href:
                match = re.search(r'product_details\?id=([^&]+)', href)
                if match:
                    new_ids.append(match.group(1))
        
        if not new_ids:
            print(f"No more products found on page {page}. Ending load.")
            break
        
        print(f"Found {len(new_ids)} products on page {page}.")
        product_ids.update(new_ids)
        page += 1
        time.sleep(1)  # Polite delay between requests
    
    return list(product_ids)

def scrape_product_view_json(product_id):
    """
    Uses a GET request to retrieve the JSON details from the product_view endpoint
    for the given product ID.
    """
    url = f"https://www.hmtwatches.in/product_view?id={product_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': 'application/json'
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to retrieve JSON for product id {product_id}. Status: {response.status_code}")
        return None
    try:
        return response.json()
    except Exception as e:
        print(f"Error parsing JSON for product id {product_id}: {e}")
        return None

def main():
    # Step 1: Load product IDs by simulating clicking "Load More" via successive POST requests.
    product_ids = load_all_product_ids()
    if not product_ids:
        print("No product IDs found.")
        return
    
    print(f"\nTotal product IDs found: {len(product_ids)}\n")
    
    # Step 2: For each product ID, fetch its JSON details from the product_view endpoint.
    all_product_details = {}
    for pid in product_ids:
        print(f"Fetching JSON details for product id: {pid}")
        details = scrape_product_view_json(pid)
        if details:
            all_product_details[pid] = details
        time.sleep(0.5)  # Polite delay between requests
    
    # Print the aggregated JSON details in a formatted output.
    print(json.dumps(all_product_details, indent=4))

if __name__ == "__main__":
    main()
