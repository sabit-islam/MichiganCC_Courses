"""
St. Clair Community College Course Scraper

Developed by: Sabit Islam 
Date: 07-02-2025

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

def parse_course_components(table):
    h3 = table.find("h3")
    if not h3:
        return "", "", "", ""
    h3_text = h3.get_text(strip=True)
    if "-" in h3_text:
        course_code, course_name = h3_text.split("-", 1)
    else:
        course_code = h3_text.strip()
        course_name = ""

    rest_text = table.get_text(separator="\n", strip=True)

    desc_lines = []
    for line in rest_text.splitlines():
        if line.startswith("Prerequisite(s):") or re.search(r'\d+(\.\d+)?\s*credits?', line):
            break
        if h3_text in line:
            continue 
        desc_lines.append(line)
    description = " ".join(desc_lines).strip()

    credit_match = re.search(r'(\d+(?:\.\d+)?|\.\d+)\s*credits?', rest_text, re.IGNORECASE)
    credit_hours = credit_match.group(1) if credit_match else ""

    return course_code.strip(), course_name.strip(), credit_hours.strip(), description.strip()


all_courses = []

for page in range(1, 6):
    url = f"https://catalog.sc4.edu/content.php?catoid=14&navoid=891&filter[item_type]=3&filter[only_active]=1&filter[3]=1&filter[cpage]={page}"
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
            f"https://catalog.sc4.edu/ajax/preview_course.php"
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
                course_code, course_name, credit_contact, description = parse_course_components(target_div)
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
df.to_csv("data/stclair_courses.csv", index=False)
print("✅ Done! Saved to data/stclair_courses.csv")


