"""
Kellogg College Course Scraper

Developed by: Sabit Islam 
Date: 06-13-2025

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

    # Match course code and name (like: ACCO 101 - General Accounting)
    header_match = re.match(
    r'^([A-Z]{2,5}\s*\d{2,6}[A-Z0-9]*)\s*[-–]\s*(.*?)\s+(\d+(?:\.\d+)?)\s*CR\b',
    clean_text
    )
    if header_match:
        course_code = header_match.group(1).strip()
        course_name = header_match.group(2).strip()
        credits = header_match.group(3).strip()
    else:
        course_code = course_name = credits = ""

    # Strip header portion to isolate description section
    description_start = re.search(r'\d+\s*CR\b', clean_text)
    if description_start:
        desc_text = clean_text[description_start.end():].strip()
    else:
        desc_text = clean_text

    # Trim at Requisites or Course Learning Outcomes
    cutoff = re.search(r'\b(Requisites|Course Learning Outcomes):', desc_text, re.IGNORECASE)
    if cutoff:
        description = desc_text[:cutoff.start()].strip()
    else:
        description = desc_text

    return course_code, course_name, credits, description





all_courses = []
total_skipped = 0
courses_skipped = []

for page in range(1,12):  
    url = f"http://catalog.kellogg.edu/content.php?catoid=27&catoid=27&navoid=2181&filter[item_type]=3&filter[only_active]=1&filter[3]=1&filter[cpage]={page}"
    print(f"Page {page} at {url}")
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    course_links = soup.find_all("a", href=True, onclick=lambda x: x and "showCourse" in x)

    print(f"Found {len(course_links)} courses on this page.")

    for link in course_links:
        full_course_text = link.get_text(strip=True)

        onclick = link.get("onclick", "")
        match = re.search(r"showCourse\('(\d+)',\s*'(\d+)'", onclick)
        if not match:
            continue
        catoid, coid = match.groups()

        ajax_url = (
            f"http://catalog.kellogg.edu/ajax/preview_course.php"
            f"?catoid={catoid}&coid={coid}&show"
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

                if re.search(r'\d{3}-\d{3}', course_code):
                    print(f"Skipping special topics course: {course_code}")
                    courses_skipped.append(full_course_text)
                    total_skipped += 1
                    continue

                if not course_code or not course_name:
                    print(f"Invalid course format, skipped: {full_course_text}")
                    total_skipped += 1
                    courses_skipped.append(full_course_text)
                    continue
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
        print(f"Processed course: {course_code} - {course_name}")
        

driver.quit()
df = pd.DataFrame(all_courses)
df1 = pd.DataFrame(courses_skipped, columns=["skipped_courses"])
df1.to_csv("data/debug/kellogg_debug.csv", index=False)
df.to_csv("data/kellogg_courses.csv", index=False)
print("It worked!")
print(f"Total courses skipped: {total_skipped}")
