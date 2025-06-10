"""
Henry Ford College Course Scraper

Developed by: Sabit Islam 
Date: 06-10-2025

Developed for LSA Transfer Student Center and to be used for educational purposes only.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time


COURSE_LIST_URL_TEMPLATE = "https://catalog.hfcc.edu/courses?page={}"

all_courses = []

def get_course_description(relative_url):
    full_url = "https://catalog.hfcc.edu" + relative_url
    try:
        r = requests.get(full_url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        desc_div = soup.find("div", class_="field--name-field-crs-description")
        if desc_div:
            paragraphs = desc_div.find_all("p")
            return " ".join(p.get_text(strip=True) for p in paragraphs)
        return "No description"
    except Exception as e:
        return f"Error: {e}"

for page in range(0,21):
    url = COURSE_LIST_URL_TEMPLATE.format(page)
    print(f"Fetching page {page + 1} → {url}")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    rows = soup.select("tbody tr")
    for row in rows:
        title_cell = row.find("td", class_="views-field-title")
        credit_cell = row.find("td", class_="views-field-field-crs-credit-hours")
        
        if title_cell and credit_cell:
            link_tag = title_cell.find("a")
            if not link_tag:
                continue
            title = link_tag.get_text(strip=True)
            relative_url = link_tag["href"]
            credits = credit_cell.get_text(strip=True)
            description = get_course_description(relative_url)
            print(f"Parsing Course: {title} ({credits})")
            try:
                course_code, course_name = title.split(":", 1)
                course_code = course_code.strip()
                course_name = course_name.strip()
            except ValueError:
                course_code = ""
                course_name = title.strip()

            all_courses.append({
                "course_code": course_code,
                "course_name": course_name,
                "credits": credits,
                "description": description,
            })
            time.sleep(0.5)  

df = pd.DataFrame(all_courses)
df.to_csv("hfcc_courses.csv", index=False)
print("Courses saved into hfcc_courses.csv")
