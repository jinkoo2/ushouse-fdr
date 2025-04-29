import sqlite3
import os

DATA_DIR = "data"
db_path = os.path.join(DATA_DIR, "fdr.db")

def init_db():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS filings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id TEXT,
            year INTEGER,
            prefix TEXT,
            last_name TEXT,
            first_name TEXT,
            suffix TEXT,
            filing_type TEXT,
            state_district TEXT,
            filing_date TEXT,
            UNIQUE (doc_id, filing_date, year, filing_type)
        )
    ''')


    # Lookup table for filing types
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS filing_types (
            code TEXT PRIMARY KEY,
            description TEXT,
            meaning TEXT
        )
    ''')

    # Pre-populate the filing_types table
    filing_type_entries = [
        ('A', 'Annual Report', 'Regular yearly disclosure of financial information.'),
        ('P', 'Periodic Transaction Report (PTR)', 'Report of stock trades and asset transactions under the STOCK Act.'),
        ('O', 'Original Filing', 'First-time filing, often by new members or nominees.'),
        ('T', 'Termination Report', 'Final report filed when leaving office.'),
        ('X', 'Amendment', 'Correction or update to a previously filed report.'),
        ('C', 'Candidacy Report', 'Financial disclosure submitted while running for office.'),
        ('E', 'Extension Request', 'Request for an extension to file the disclosure.'),
        ('D', 'Delinquent Notice', 'Filed after missing a required filing deadline.'),
        ('G', 'Gift Report', 'Report focused on gifts received.'),
        ('B', 'Blind Trust Report', 'Disclosure involving the establishment of a blind trust.'),
        ('W', 'Waiver Request', 'Request to waive certain reporting requirements.')
    ]

    cursor.executemany('''
        INSERT OR IGNORE INTO filing_types (code, description, meaning)
        VALUES (?, ?, ?)
    ''', filing_type_entries)
    

    conn.commit()
    conn.close()


def get_all_filing_types():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM filing_types')
    rows = cursor.fetchall()

    # Fetch column names
    headers = [description[0] for description in cursor.description]

    result = [dict(zip(headers, row)) for row in rows]

    conn.close()
    return result

def get_all_filings():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM filings')
    rows = cursor.fetchall()
    
    # Fetch column names
    headers = [description[0] for description in cursor.description]

    result = [dict(zip(headers, row)) for row in rows]

    conn.close()
    return result

   
if __name__ == '__main__':  
    filing_types = get_all_filing_types()
    print(filing_types)

    filings = get_all_filings()
    for filing in filings[:5]:
        print(filing)

