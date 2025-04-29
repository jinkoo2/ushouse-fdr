import os
import sqlite3
import xml.etree.ElementTree as ET
from datetime import datetime

import db

DATA_DIR = "data"

fd_unzipped_dir = os.path.join(DATA_DIR,"2.fd_unzipped")
db_path = os.path.join(DATA_DIR, "fdr.db")

def parse_and_store(year: int):
    xml_file = os.path.join(fd_unzipped_dir, str(year), f"{year}FD.xml")
    if not os.path.exists(xml_file):
        print(f"❌ XML file for {year} not found.")
        return

    tree = ET.parse(xml_file)
    root = tree.getroot()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    inserted_count = 0
    failed_to_insert_count = 0
    duplicate_skippied_count = 0

    for member in root.findall("Member"):
        prefix = member.findtext("Prefix", default="")
        last_name = member.findtext("Last", default="")
        first_name = member.findtext("First", default="")
        suffix = member.findtext("Suffix", default="")
        filing_type = member.findtext("FilingType", default="")
        state_district = member.findtext("StateDst", default="")
        filing_date = member.findtext("FilingDate", default="")
        doc_id = member.findtext("DocID", default="")
        member_year = member.findtext("Year", default=year)  # Prefer the year inside XML if available
        
        # Check if doc_id + filing_date + year + filing_type already exists
        cursor.execute('''
            SELECT 1 FROM filings
            WHERE doc_id = ? AND filing_date = ? AND year = ? AND filing_type = ? AND last_name = ? AND first_name = ? AND state_district = ?
        ''', (doc_id, filing_date, member_year, filing_type, last_name, first_name, state_district))
        exists = cursor.fetchone()
        
        if not exists:
            try:
                cursor.execute('''
                    INSERT INTO filings (doc_id, year, prefix, last_name, first_name, suffix, filing_type, state_district, filing_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (doc_id, member_year, prefix, last_name, first_name, suffix, filing_type, state_district, filing_date))
                inserted_count += 1
            except:
                print('Insert failed for (doc_id={doc_id}, filing_date={filing_date}, member_year={member_year}, filing_type={filing_type}, last_name={last_name}, first_name={first_name})')
                failed_to_insert_count += 1 
        else:
            print(f"⚠️(doc_id={doc_id}, filing_date={filing_date}, member_year={member_year}, filing_type={filing_type}, last_name={last_name}, first_name={first_name}) already exists. Skipping insert.")
            duplicate_skippied_count += 1


    

    conn.commit()
    conn.close()
    return inserted_count, failed_to_insert_count, duplicate_skippied_count

if __name__ == '__main__':
    db.init_db()
    
    inserted_count_total, failed_to_insert_count_total, duplicate_skippied_count_total = 0,0,0

    for year in range(2008, datetime.now().year + 1):
        inserted_count, failed_to_insert_count, duplicate_skippied_count = parse_and_store(year)
        print(f"✅ Inserted records = {inserted_count} for {year}.")
        print(f"✅ Failed to insert = {failed_to_insert_count} for {year}.")
        print(f"✅ Duplicate skipped = {duplicate_skippied_count} for {year}.")
        
        inserted_count_total += inserted_count
        failed_to_insert_count_total += failed_to_insert_count
        duplicate_skippied_count_total += duplicate_skippied_count


    print('------------')
    print(f"✅ Inserted records total = {inserted_count_total}.")
    print(f"✅ Failed to insert total = {failed_to_insert_count_total}.")
    print(f"✅ Duplicate skipped total = {duplicate_skippied_count_total}.")







