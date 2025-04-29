import requests
import os
from datetime import datetime
from zipfile import ZipFile

BASE_URL = "https://disclosures-clerk.house.gov"
DATA_DIR = "data"

def search_report_pdfs():
    import requests
from bs4 import BeautifulSoup

# Correct URL that actually has the form
form_url = "https://disclosures-clerk.house.gov/FinancialDisclosure/ViewSearch"
post_url = "https://disclosures-clerk.house.gov/FinancialDisclosure/ViewMemberSearchResult"

# Start session
session = requests.Session()

# Step 1: GET the correct form page
resp = session.get(form_url)
soup = BeautifulSoup(resp.text, "lxml")  # now using lxml

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

print(response.status_code)
print(response.text[:1000])  # Just printing the first part


def download_report_pdf_file(year, doc_id, filing_type, check_next_year=True):

    if filing_type == 'O':
        doc_type = "financial_pdf"
    else:
        doc_type = "ptr_pdf"

    pdf_url = f"{BASE_URL}/public_disc/{doc_type}s/{year}/{doc_id}.pdf"

    print(f"🔗 Checking {pdf_url}")

    output_dir = os.path.join(DATA_DIR, "3.report_pdf_files", str(year))
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{doc_type}.{doc_id}.pdf")

    try:
        response = requests.head(pdf_url)
        response.raise_for_status()
        remote_size = int(response.headers.get("Content-Length", 0))
    except Exception as e:
        print(f"❌ Error checking (year={year}, doc_id={doc_id}): {e}")
        if check_next_year:
            return download_report_pdf_file(year+1, doc_id, filing_type, check_next_year=False)
        return False

    if os.path.exists(output_path):
        local_size = os.path.getsize(output_path)
        if local_size == remote_size:
            print(f"✅ (year={year}, doc_id={doc_id}) file exists and matches size ({local_size} bytes). Skipping.")
            return False
        else:
            print(f"⚠️ Size mismatch for (year={year}, doc_id={doc_id}). Re-downloading...")

    response = requests.get(pdf_url)
    response.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(response.content)

    print(f"✅ Downloaded {output_path}")
    return True

def download_report_pdf_files():
    import db
    filings = db.get_all_filings()
    for filing in filings:
        
        print(filing)

        year =  filing['year']
        doc_id =  filing['doc_id']
        filing_type = filing['filing_type']
        download_report_pdf_file(year, doc_id, filing_type)


if __name__ == '__main__':
    download_report_pdf_files()
    
    
   


