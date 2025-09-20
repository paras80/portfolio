import time
import re
import json
import requests
from bs4 import BeautifulSoup

def get_initial_session():
    """
    Creates a persistent session and loads the initial search page
    to obtain cookies and any dynamic tokens.
    """
    session = requests.Session()
    default_headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    initial_url = "https://www.hmtwatches.in/search?keys=%25"
    response = session.get(initial_url, headers=default_headers)
    if response.status_code != 200:
        print("Failed to load the initial page.")
    # Update session headers (and optionally extract dynamic tokens from response.text)
    session.headers.update(default_headers)
    return session

def load_more_products(session, page):
    """
    Simulates clicking the "Load More" button by sending a POST request
    to the load_more endpoint. This function returns the HTML snippet
    containing additional product links.
    """
    endpoint = "https://www.hmtwatches.in/api/search/loadmore"  # Adjust if needed
    payload = {
        "keys": "%25",   # Wildcard search key (adjust as needed)
        "page": page,    # Current page number (simulate successive clicks)
        "limit": 20      # Number of products per page; adjust if needed
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Content-Type': 'application/json'
    }
    print(f"Sending POST request for load_more, page {page} ...")
    response = session.post(endpoint, json=payload, headers=headers)
    print("Raw response text:", response.text[:200])  # Print first 200 chars for debug
    if response.status_code != 200:
        print(f"Failed to fetch load_more data for page {page}: Status code {response.status_code}")
        return None
    if not response.text.strip():
        print("Empty response received for page", page)
        return None
    try:
        data = response.json()
        html_snippet = data.get("html", "")
        if not html_snippet.strip():
            print("HTML snippet is empty on page", page)
            return None
        return html_snippet
    except Exception as e:
        print("Error parsing JSON from load_more response:", e)
        return None

def extract_product_ids(html):
    """
    Parses the provided HTML snippet using BeautifulSoup to extract product IDs.
    Looks for <a> tags with href attributes containing "product_details?id=".
    """
    soup = BeautifulSoup(html, "html.parser")
    product_ids = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        match = re.search(r'product_details\?id=([^&]+)', href)
        if match:
            product_ids.append(match.group(1))
    return list(set(product_ids))  # Remove duplicates

def fetch_product_details(session, product_id):
    """
    Fetches product details from the product_view endpoint.
    Returns a dictionary with product details parsed from the HTML.
    """
    url = f"https://www.hmtwatches.in/product_view?id={product_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
    response = session.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to retrieve product_view for id {product_id}: Status code {response.status_code}")
        return None
    soup = BeautifulSoup(response.text, "html.parser")
    # For demonstration, confirm the product id by locating an anchor with product_details?id=
    a_tag = soup.find("a", href=re.compile(r'product_details\?id='))
    if a_tag:
        href = a_tag["href"]
        match = re.search(r'product_details\?id=([^&]+)', href)
        found_id = match.group(1) if match else product_id
    else:
        found_id = product_id
    # Optionally, extract additional details (e.g., product title)
    title_tag = soup.find("h1", class_="product-title")
    title = title_tag.get_text(strip=True) if title_tag else ""
    return {"id": found_id, "title": title}

def main():
    session = get_initial_session()
    all_product_ids = []
    current_page = 1
    while True:
        html_snippet = load_more_products(session, current_page)
        if not html_snippet:
            print("No more HTML snippet returned; stopping load_more.")
            break
        product_ids = extract_product_ids(html_snippet)
        if not product_ids:
            print(f"No product IDs found on page {current_page}; ending load_more.")
            break
        print(f"Page {current_page} returned {len(product_ids)} product IDs: {product_ids}")
        all_product_ids.extend(product_ids)
        current_page += 1
        time.sleep(1)
    all_product_ids = list(set(all_product_ids))
    print(f"\nTotal unique product IDs found: {len(all_product_ids)}")
    all_product_details = {}
    for pid in all_product_ids:
        details = fetch_product_details(session, pid)
        if details:
            all_product_details[pid] = details
        time.sleep(0.5)
    print("\nProduct Details:")
    print(json.dumps(all_product_details, indent=4))

if __name__ == "__main__":
    main()
