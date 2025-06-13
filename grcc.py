"""
Grand Rapids CC Course Scraper

Developed by: Sabit Islam 
Date: 06-09-2025

Developed for LSA Transfer Student Center and to be used for educational purposes only.
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import regex as re
import time
import requests

options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def clean_description(raw_html: str) -> str:
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text(separator=' ')
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'(Facebook|Tweet|Add to Catalog|Print Course)[^)]*\)', '', text)
    return text

def extract_components(full_text):
    credits_match = re.search(r'Credit Hours:\s*(\d+)', full_text, re.IGNORECASE)
    credits = credits_match.group(1) if credits_match else ""
    description_match = re.search(r'Description:\s*(.*?)General Education Distribution Category Met:', full_text, re.IGNORECASE | re.DOTALL)
    description = description_match.group(1).strip() if description_match else full_text
    return {
        "credits": credits,
        "description": description,
    }

all_courses = []
base_url = "https://catalog.grcc.edu/content.php?catoid=59&navoid=5709&filter[item_type]=3&filter[only_active]=1&filter[3]=1&filter[cpage]={}"

for page in range(1,11): 
    url = base_url.format(page)
    print(f"Page {page} → {url}")
    driver.get(url)
    time.sleep(2)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    links = soup.find_all("a", onclick=re.compile(r"showCourse\('59', '\d+'"))

    if not links:
        print("No courses found — likely end of pages.")
        break

    for link in links:
        course_name = link.text.strip().replace('\xa0', ' ')
        onclick = link['onclick']
        match = re.search(r"showCourse\('(\d+)', '(\d+)'", onclick)
        if not match:
            continue
        catoid, coid = match.groups()
        ajax_url = f"https://catalog.grcc.edu/ajax/preview_course.php?catoid={catoid}&coid={coid}&display_options=a%3A2%3A%7Bs%3A8%3A~location~%3Bs%3A8%3A~template~%3Bs%3A28%3A~course_program_display_field~%3Bs%3A0%3A~~%3B%7D&show"

        try:
            r = requests.get(ajax_url, timeout=10)
            raw_desc = clean_description(r.text)
            components = extract_components(raw_desc)
        except Exception as e:
            components = {"credits": "", "description": f"Error: {e}"}

        code_split = course_name.split("-", 1)
        if len(code_split) < 2:
            print("Invalid course format, skipping...")
            continue  #

        course_code = code_split[0].strip()
        course_title = code_split[1].strip()
        if not re.match(r'[A-Z]{2,4}[\s]\d{2,4}', course_name[:10]):
            print(f"Skipping invalid course code: {course_code}")
            continue

        print(f"Fetching course: {course_code} - {course_title}")
        all_courses.append({
            "course_code": course_code,
            "course_name": course_title,
            "credits": components["credits"],
            "description": components["description"]
        })

driver.quit()

df = pd.DataFrame(all_courses)
df.to_csv("data/grcc_courses.csv", index=False)
"Saved to grcc_courses.csv."
