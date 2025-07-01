"""
Kirtland Community College Course Scraper

Developed by: Sabit Islam 
Date: 07-01-2025

Developed for LSA Transfer Student Center and to be used for educational purposes only.
"""

import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import regex as re
import pandas as pd
import time

options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def clean_description(raw_html: str) -> str:
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text(separator=' ')
    text = text.replace('\xa0', ' ')
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'(Facebook|Tweet|Add to Portfolio|Print Course)[^)]*\)', '', text)
    return text

def parse_course_components(clean_text: str):
    clean_text = clean_text.strip()
    match = re.search(
        r'^([A-Z]{2,5}\s*\d{3,5})\s*-\s*(.*?)\s+(\d+(?:\.\d+)?)\s+Credit Hours',
        clean_text
    )

    if match:
        course_code = match.group(1).strip()
        course_name = match.group(2).strip()
        credits = match.group(3).strip()
    else:
        course_code = course_name = credits = ""
    desc_match = re.search(r'(Prerequisites:.*?)Click here for class offerings', clean_text, re.DOTALL)
    if desc_match:
        description = desc_match.group(1).strip()
    else:
        description = re.split(r'Credit Hours', clean_text, maxsplit=1)[-1].strip()

    return course_code, course_name, credits, description
all_courses = []

for page in range(1, 11):
    url = f"https://ecatalog.macomb.edu/content.php?catoid=9&navoid=327&filter[item_type]=3&filter[only_active]=1&filter[3]=1&filter[cpage]={page}"
    print(f"Scraping page {page}")
    driver.get(url)
    time.sleep(1)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    course_links = soup.find_all("a", href=True, onclick=lambda x: x and "showCourse" in x)

    for link in course_links:
        full_course_text = link.get_text(strip=True)
        print(f"Fetching course: {full_course_text}")

        onclick = link.get("onclick", "")
        match = re.search(r"showCourse\('(\d+)',\s*'(\d+)'", onclick)
        if not match:
            continue
        catoid, coid = match.groups()

        ajax_url = (
            f"https://ecatalog.macomb.edu/ajax/preview_course.php"
            f"?catoid={catoid}&coid={coid}"
            f"&display_options=a%3A2%3A%7Bs%3A8%3A~location~%3Bs%3A8%3A~template~%3Bs%3A28%3A~course_program_display_field~%3Bs%3A0%3A~~%3B%7D&show"
        )

        try:
            r = requests.get(ajax_url, timeout=10)
            desc_soup = BeautifulSoup(r.text, "html.parser")

            divs = desc_soup.find_all("div")
            target_div = None
            for div in divs:
                h3 = div.find("h3")
                if h3 and full_course_text.split()[0] in h3.text:
                    target_div = div
                    break

            if target_div:
                raw_text = target_div.get_text(separator=' ')
                clean_text = clean_description(raw_text)
                course_code, course_name, credit_contact, description = parse_course_components(clean_text)
            else:
                course_code = course_name = credit_contact = ""
                description = "No description found"

        except Exception as e:
            course_code = course_name = credit_contact = ""
            description = f"Error: {e}"

        all_courses.append({
            "course_code": course_code,
            "course_name": course_name,
            "credit_hours": credit_contact,
            "description": description
        })

        print(f"{course_code} | {course_name} | {credit_contact}cr | {description[:50]}...")

driver.quit()
df = pd.DataFrame(all_courses)
df.to_csv("data/macomb_courses.csv", index=False)
print("✅ Done!")
