from PIL import ImageGrab
import pytesseract
import os
import sqlite3
import datetime
import concurrent.futures
import json
from dotenv import load_dotenv; load_dotenv()

from time import sleep
def save_pdf(path, file):
    with open(path, "wb") as f:
        f.write(file.getbuffer())

def check_data_initialized(db_file, screenshots_folder):
    if not os.path.exists(db_file):
        print(f'[{now()}] Initializing empty DB')
        con = sqlite3.connect(db_file)
        cur = con.cursor()
        cur.execute("""
            create table entries(
                created_timestamp text,
                file text,
                ocr_data text,
                ocr_text text
            )
        """)
        con.commit()

    if not os.path.exists(screenshots_folder):
        print(f'[{now()}] Initializing screenshots folder')
        os.mkdir(screenshots_folder)

def insert_row(con, screenshot_dt, filename, ocr_data, ocr_text):
    con.cursor().execute('insert into entries values(?, ?, ?, ?)', (screenshot_dt, filename, json.dumps(ocr_data), ocr_text))
    con.commit()

def now():
    return datetime.datetime.now().isoformat()

def process_frame(db_file, screenshot_folder):
    con = sqlite3.connect(db_file)

    screenshot_dt = now()
        
    print(f'[{screenshot_dt}] Taking screenshot')
    img = ImageGrab.grab(all_screens=True)
    
    print(f'[{now()}] Running OCR Text')
    ocr_text = pytesseract.image_to_string(img, lang='eng')

    print(f'[{now()}] Running OCR Data')
    ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

    print(f'[{now()}] Saving Image')
    filename = f'{screenshot_folder}/screenshot_{screenshot_dt}.jpg'
    img.convert('RGB').save(filename, dpi=(100, 100), optimize=True)

    print(f'[{now()}] Inserting row to db')
    insert_row(con, screenshot_dt, filename, ocr_data, ocr_text)

def main():
    check_data_initialized(os.environ["DB_FILE"], os.environ["SCREENSHOTS_FOLDER"])

    with concurrent.futures.ThreadPoolExecutor(max_workers=int(os.environ["MAX_WORKERS"])) as executor:
        while True:
            print(f'[{now()}] Starting thread')
            executor.submit(process_frame, os.environ["DB_FILE"], os.environ["SCREENSHOTS_FOLDER"])
            print(f'[{now()}] Sleeping {int(os.environ["SLEEP_DURATION"])}s')
            sleep(int(os.environ["SLEEP_DURATION"]))

if __name__ == '__main__':
    main()