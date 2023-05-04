import requests
from bs4 import BeautifulSoup
import time
import sqlite3
import copy
import smtplib
from email.mime.text import MIMEText
from smtplib import SMTP

# Establish a connection to the database
conn = sqlite3.connect('jobs.db')
cursor = conn.cursor()

# Create a table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        company TEXT,
        job_url TEXT
    )
''')
conn.commit()

class TestSMTP(SMTP):
    def __init__(self, host='localhost', port=25, local_hostname=None,
                 timeout=60, source_address=None):
        super().__init__(host, port, local_hostname, timeout, source_address)
        self.debuglevel = 1  # Enable debug output

    def send_message(self, msg, from_addr=None, to_addrs=None, mail_options=(),
                     rcpt_options=()):
        # Instead of sending the message, print it to the console
        print(msg)

        
def send_email(recipient, subject, message):
    sender = 'your_email@example.com'
    password = 'your_email_password'
    smtp_server = 'localhost'
    smtp_port = 25

    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient

    with TestSMTP(smtp_server, smtp_port) as server:
        server.login(sender, password)
        server.send_message(msg)


def get(alue:str, hakusana:str):
    hakusana = hakusana
    alue = alue
    nr = 1
    paikka_copies=[]
    while True:
        time.sleep(1) #avoid spam
        url = f'https://duunitori.fi/tyopaikat/{alue}/{hakusana}?sivu={nr}'
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        job_listings = soup.find_all('div', class_='grid grid--middle job-box job-box--lg')

        try:
            sivunr = soup.select_one('.pagination__splitted a:last-child')
            sivunr = int(sivunr.text)
        except:
            sivunr = 1

        print(nr,"/",sivunr)
        
        for job in job_listings:
            paikka = []
            a_element = job.find('a', class_='job-box__hover gtm-search-result')
            if a_element:
                title = a_element.text
                firma = a_element["data-company"]
                href = a_element['href']
                
                paikka.append(title)
                paikka.append(firma)
                paikka.append(href)
                paikka_copies.extend(paikka)
                

            else:
                break

        nr += 1
        if nr > sivunr:
            return paikka_copies
           

def get_database():
    conn = sqlite3.connect('jobs.db')
    cursor = conn.cursor()
    cursor.execute("SELECT title, company, job_url FROM jobs")
    rows = cursor.fetchall()
    result = [tuple(row) for row in rows]  # Convert rows to tuples
    return result


def lahetys():
    data = get_database()  # Retrieve data from the database
    uusdata = get(alue, hakusana)
    new_jobs = []

    conn = sqlite3.connect('jobs.db')
    cursor = conn.cursor()

    for i in range(0, len(uusdata), 3):
        title, firma, href = uusdata[i:i+3]  # Unpack the values from uusdata
        
        if (title, firma, href) not in [tuple(item) for item in data]:  # Convert data to tuples for comparison
            cursor.execute('INSERT INTO jobs (title, company, job_url) VALUES (?, ?, ?)', (title, firma, href))
            conn.commit()
            new_jobs.append((title, firma, href))
    
    conn.close()
    
    if new_jobs:
        recipient = 'recipient_email@example.com'
        subject = 'New Job Listings'
        message = 'The following job listings are not in the database:\n\n'
        for job in new_jobs:
            message += f'Title: {job[0]}\nCompany: {job[1]}\nJob URL: {job[2]}\n\n'
        send_email(recipient, subject, message)
        print("sent")
    else:
        print("no new jobs")

if __name__ == "__main__":
    while True:
        alue = input("Anna alue: ")
        hakusana = input("Anna yksi hakusana: ")
        
        if not alue.isalpha() or not hakusana.isalpha():
            print("Virheellinen syöte. Anna vain merkkijonoja.")
            continue
        
        lahetys()
        break


    
