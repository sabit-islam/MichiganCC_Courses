"""
Delta College Course Scraper

Developed by: Sabit Islam 
Date: 06-10-2025

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


def parse_course_components(text: str):
    text = text.strip()

    # Match course code and name
    # Pattern: 2–6 uppercase letters, optional space, 2–4 digits + optional letter
    match = re.match(r'^([A-Z]{2,6}\s*\d{2,4}[A-Z]?)\s*[-–]\s*(.+)', text)
    if not match:
        return "", "", "", text

    course_code = match.group(1).strip()
    
    # Split remaining string (course name + description + credits)
    rest = match.group(2).strip()

    # Match credit hours near end (captures 3, 3.0, .75, etc.)
    credit_match = re.search(r'(\d+(?:\.\d+)?|\.\d+)\s*credits?', rest, re.IGNORECASE)
    credit_hours = credit_match.group(1) if credit_match else ""

    # Assume course name ends before description starts (first sentence word boundary)
    # We'll take first 2–6 capitalized words as a naive course name
    name_parts = rest.split()
    name_tokens = []
    for token in name_parts:
        if token[0].isupper() and not re.match(r'\d', token):
            name_tokens.append(token)
        else:
            break
    course_name = " ".join(name_tokens)

    # Description is the rest of the string after course name
    desc_start = rest.find(course_name) + len(course_name)
    description = rest[desc_start:].strip()

    return course_code, course_name, credit_hours, description




all_courses = []
total_skipped = 0
courses_skipped = []

for page in range(1,16):  
    url = f"https://catalog.delta.edu/content.php?catoid=14&catoid=14&navoid=2131&filter[item_type]=3&filter[only_active]=1&filter[3]=1&filter[cpage]={page}"
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
            f"https://catalog.delta.edu/ajax/preview_course.php"
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

                if re.search(r'\d{3}-\d{3}', course_code):
                    print(f"Skipping special topics course: {course_code}")
                    courses_skipped.append(full_course_text)
                    total_skipped += 1
                    continue

                if not course_code or not course_name:
                    print("Invalid course format, skipped")
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
       # print(f"Course Code: {course_code}, Course Name: {course_name}, Credit: {credit_contact}, Description: {description[:50]}")

driver.quit()
df = pd.DataFrame(all_courses)
df1 = pd.DataFrame(courses_skipped, columns=["skipped_courses"])
df1.to_csv("data/debug.csv", index=False)
df.to_csv("data/delta_courses.csv", index=False)
print("It worked!")
print(f"Total courses skipped: {total_skipped}")
