"""
Bay College Course Scraper

Developed by: Sabit Islam 
Date: 06-09-2025

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

    header_match = re.search(r'^(.*?)\s+Credit\(s\):', clean_text)
    if header_match:
        header = header_match.group(1).strip()

        if '-' in header:
            parts = header.split('-', 1)
            course_code = parts[0].strip()
            course_name = parts[1].strip()
        else:
            course_code = ""
            course_name = header
    else:
        course_code = ""
        course_name = ""

    credit_match = re.search(r'Credit\(s\):\s*(\d+)', clean_text)
    credit_contact = f"{credit_match.group(1)}" if credit_match  else ""

    desc_start_match = re.search(r'Contact Hours:\s*\d+\s*', clean_text)
    description = clean_text[desc_start_match.end():].strip() if desc_start_match else clean_text

    return course_code, course_name, credit_contact, description

all_courses = []

for page in range(1, 6):  
    url = f"https://catalog.baycollege.edu/content.php?catoid=1&navoid=14&filter[item_type]=3&filter[only_active]=1&filter[3]=1&filter[cpage]={page}"
    print(f"Page {page}")
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
            f"https://catalog.baycollege.edu/ajax/preview_course.php"
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
                if h3 and h3.text and full_course_text.split()[0] in h3.text:
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
        print(f"Course Code: {course_code}, Course Name: {course_name}, Credit: {credit_contact}, Description: {description[:50]}")

driver.quit()
df = pd.DataFrame(all_courses)
df.to_csv("bay_college.csv", index=False)
print("It worked!")