import requests
from bs4 import BeautifulSoup
import json
import os

BASE_URL = "https://disclosures-clerk.house.gov"
DATA_DIR = "data"

def search_disclosures():
    # Correct URLs
    form_url = f"{BASE_URL}/FinancialDisclosure/ViewSearch"
    post_url = f"{BASE_URL}/FinancialDisclosure/ViewMemberSearchResult"

    # Start session
    session = requests.Session()

    # Step 1: GET the form page
    resp = session.get(form_url)
    soup = BeautifulSoup(resp.text, "lxml")  # you can use 'lxml' or 'html.parser'

    # Step 2: Find the __RequestVerificationToken
    token_input = soup.find("input", {"name": "__RequestVerificationToken"})

    if token_input is None:
        print("❌ Could not find the __RequestVerificationToken input field.")
        with open("debug_page.html", "w", encoding="utf-8") as f:
            f.write(resp.text)
        raise Exception("Token not found, check debug_page.html")

    token = token_input["value"]
    print(f"✅ Extracted Token: {token}")

    # Step 3: POST the form with the token
    payload = {
        "LastName": "",
        "FilingYear": "",
        "State": "",
        "District": "",
        "__RequestVerificationToken": token,
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0",
    }

    response = session.post(post_url, data=payload, headers=headers)

    return response

def parse_disclosures_html_to_dict_list(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    results = []
    table = soup.find('table', {'class': 'library-table'})

    if table:
        tbody = table.find('tbody')
        rows = tbody.find_all('tr')
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) == 4:
                name_tag = cols[0].find('a')
                name = name_tag.text.strip() if name_tag else ''
                link = name_tag['href'] if name_tag and 'href' in name_tag.attrs else ''
                office = cols[1].text.strip()
                filing_year = cols[2].text.strip()
                filing_type = cols[3].text.strip()

                result = {
                    'name': name,
                    'link': link,
                    'office': office,
                    'filing_year': filing_year,
                    'filing_type': filing_type
                }
                results.append(result)

    return results


import re
from urllib.parse import urljoin

def sanitize_for_filename(name):
    name = re.sub(r'\.+', '.', name)
    name = re.sub(r'["\u201c\u201d\u2018\u2019]', '', name)
    sanitized = re.sub(r'[<>:"/\\|?*\n\r\t]', '_', name)
    sanitized = re.sub(r'_+', '_', sanitized)
    sanitized = sanitized.strip(' ._')
    return sanitized

def download_disclosures_pdfs(disclosures, output_base_dir):
    os.makedirs(output_base_dir, exist_ok=True)
    session = requests.Session()

    for disclosure in disclosures:
        name = disclosure['name']
        office = disclosure['office']
        filing_year = disclosure['filing_year']
        filing_type = disclosure['filing_type']
        link = disclosure['link']

        # Prepare folder
        clean_name = sanitize_for_filename(name)
        clean_office = sanitize_for_filename(office)
        folder_name = f"{clean_name}_{clean_office}"
        folder_path = os.path.join(output_base_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        # Determine pdf type
        pdf_type = "ptr" if "ptr-pdfs" in link else "financial"

        # Extract pdf number
        pdf_number_match = re.search(r'/([0-9]+)\.pdf$', link)
        pdf_number = pdf_number_match.group(1) if pdf_number_match else "unknown"

        # Prepare file name
        clean_filing_type = sanitize_for_filename(filing_type)
        pdf_filename = f"{filing_year}_{pdf_type}_{clean_filing_type}_{pdf_number}.pdf"
        pdf_path = os.path.join(folder_path, pdf_filename)

        # Download if not already exists
        if os.path.exists(pdf_path):
            print(f"✅ Already exists: {pdf_path}")
            continue

        pdf_url = urljoin(BASE_URL, link)
        print(f"⬇️  Downloading {pdf_url} -> {pdf_path}")

        try:
            r = session.get(pdf_url, timeout=30)
            r.raise_for_status()
            with open(pdf_path, 'wb') as f:
                f.write(r.content)
            print(f"✅ Saved: {pdf_path}")
        except Exception as e:
            print(f"❌ Failed to download {pdf_url}: {e}")


if __name__ == '__main__':

    response = search_disclosures()
    if response.status_code != 200:
        print(f"❌ Failed POST, status code: {response.status_code}")
        exit(-1)
    
    output_dir = os.path.join(DATA_DIR, "3.search_pdf_reports")
    os.makedirs(output_dir, exist_ok=True)

    html_file = os.path.join(output_dir, 'disclosures.html')
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(response.text)
    
    disclosures = parse_disclosures_html_to_dict_list(response.text)
     # Save to a JSON file
    json_file = os.path.join(output_dir, 'disclosures.json')
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(disclosures, f, ensure_ascii=False, indent=2)

    # download pdf files
    pdf_output_dir = os.path.join(output_dir, "pdfs")
    os.makedirs(pdf_output_dir, exist_ok=True)
    download_disclosures_pdfs(disclosures, pdf_output_dir)

    print('done')