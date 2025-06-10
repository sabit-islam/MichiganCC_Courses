"""
Mott Community College Course Scraper

Developed by: Sabit Islam 
Date: 05-23-2025

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
    text = re.sub(r'[●•▪‣‣]+', '', text)
    text = re.sub(r'\s*\d+\.\s*', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    text = text.strip()

    return text

def extract_components(full_text):
    credits_match = re.search(r'Credits\s+(\d+\s*)', full_text, re.IGNORECASE)
    
    contact_hours = credits_match.group(0) if credits_match else ""
    contact_hours = contact_hours.replace("Credits", "").strip() if contact_hours else ""
    print(f"Contact Hours: {contact_hours}")

    description_start = credits_match.end() + 4 if credits_match else 4
    # description_end = outcomes_match.start() if outcomes_match else len(full_text)
    main_description = full_text[description_start:len(full_text)].strip()

    return {
        "credits": contact_hours,
        "description": main_description,
    }


all_courses = []

for page in range(1, 11):
    url = f"https://catalog.mcc.edu/content.php?catoid=12&navoid=360&filter[item_type]=3&filter[only_active]=1&filter[3]=1&filter[cpage]={page}"
    print(f"Page {page}")
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    course_links = soup.find_all("a", onclick=lambda x: x and x.startswith("showCourse("))

    for link in course_links:
        course_name = link.get_text(strip=True)
        print(f"fethcing course: {course_name}")
        onclick = link["onclick"]

        parts = onclick.split("'")
        catoid = parts[1]
        coid = parts[3]

        ajax_url = (
            f"https://catalog.mcc.edu/ajax/preview_course.php"
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
                if h3 and course_name.split()[0] in h3.text:
                    target_div = div
                    break

            if target_div:
                description_raw = target_div.get_text(separator=' ')
                description = clean_description(description_raw)
            else:
                description = "No description found"

        except Exception as e:
            description = f"Error: {e}"

        components = extract_components(description)
        c_id, c_name = course_name.split(" ", 1)

        all_courses.append({
            "course_code": c_id,
            "course_name": c_name,
            "credits": components["credits"],
            "description": components["description"],
        })


driver.quit()

df = pd.DataFrame(all_courses)
df.to_csv("mott_courses.csv", index=False)
print("It worked and you are not a total loser!")
