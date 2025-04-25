import requests
import os
from datetime import datetime
from zipfile import ZipFile

BASE_URL = "https://disclosures-clerk.house.gov"
DATA_DIR = "data"

def download_fd_zip_for_year(year: int):
    pdf_url = f"{BASE_URL}/public_disc/financial-pdfs/{year}FD.zip"
    print(f"🔗 Checking {pdf_url}")

    output_dir = os.path.join(DATA_DIR, "1.fd_zip_files")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{year}FD.zip")

    try:
        response = requests.head(pdf_url)
        response.raise_for_status()
        remote_size = int(response.headers.get("Content-Length", 0))
    except Exception as e:
        print(f"❌ Error checking {year}: {e}")
        return False

    if os.path.exists(output_path):
        local_size = os.path.getsize(output_path)
        if local_size == remote_size:
            print(f"✅ {year} file exists and matches size ({local_size} bytes). Skipping.")
            return False
        else:
            print(f"⚠️ Size mismatch for {year}. Re-downloading...")

    response = requests.get(pdf_url)
    response.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(response.content)

    print(f"✅ Downloaded {output_path}")
    return True

def unzip_fd_zip(year: int):
    zip_path = os.path.join(DATA_DIR, "1.fd_zip_files", f"{year}FD.zip")
    extract_dir = os.path.join(DATA_DIR, "2.fd_unzipped", str(year))
    os.makedirs(extract_dir, exist_ok=True)

    try:
        with ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)
        print(f"📂 Unzipped to {extract_dir}")
    except Exception as e:
        print(f"❌ Failed to unzip {zip_path}: {e}")

def year_list():
    current_year = datetime.now().year
    return list(range(2008, current_year + 1))

if __name__ == '__main__':
    for year in year_list():
        print(f"\n📅 Processing year {year}")
        if download_fd_zip_for_year(year):
            unzip_fd_zip(year)
