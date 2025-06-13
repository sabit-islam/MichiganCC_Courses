"""
Glen Oaks CC Course Scraper

Developed by: Sabit Islam 
Date: 06-09-2025

Developed for LSA Transfer Student Center and to be used for educational purposes only.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

department_paths = [
    "/course-descriptions/acct/",
    "/course-descriptions/agt/",
    "/course-descriptions/alh/",
    "/course-descriptions/anth/",
    "/course-descriptions/art/",
    "/course-descriptions/auto/",
    "/course-descriptions/bio/",
    "/course-descriptions/bus/",
    "/course-descriptions/chem/",
    "/course-descriptions/com/",
    "/course-descriptions/cis/",
    "/course-descriptions/crju/",
    "/course-descriptions/cadd/",
    "/course-descriptions/econ/",
    "/course-descriptions/edu/",
    "/course-descriptions/elec/",
    "/course-descriptions/eng/",
    "/course-descriptions/geog/",
    "/course-descriptions/geol/",
    "/course-descriptions/hist/",
    "/course-descriptions/hum/",
    "/course-descriptions/inds/",
    "/course-descriptions/lng/",
    "/course-descriptions/mach/",
    "/course-descriptions/math/",
    "/course-descriptions/mus/",
    "/course-descriptions/nur/",
    "/course-descriptions/phil/",
    "/course-descriptions/phed/",
    "/course-descriptions/phys/",
    "/course-descriptions/psi/",
    "/course-descriptions/psy/",
    "/course-descriptions/rel/",
    "/course-descriptions/swk/",
    "/course-descriptions/soc/",
    "/course-descriptions/tech/",
    "/course-descriptions/weld/"
]


all_courses = []

for dept_path in department_paths:
    dept_url = "https://catalog.glenoaks.edu" + dept_path
    response = requests.get(dept_url)
    soup = BeautifulSoup(response.text, "html.parser")

    course_blocks = soup.select(".sc_sccoursedescs .courseblock")

    for block in course_blocks:
        code_tag = block.select_one(".detail-code strong")
        name_tag = block.select_one(".detail-title strong")
        code = code_tag.get_text(strip=True) if code_tag else ""
        name = name_tag.get_text(strip=True).title() if name_tag else ""
        print("Fetching course:", code, name)
        credit_tag = block.select_one(".detail-hours_html strong")
        credit_match = re.search(r"(\d+)", credit_tag.get_text(strip=True)) if credit_tag else None
        credit = credit_match.group(1) if credit_match else ""
        credit_contact = f"{credit}" if credit else ""
        desc_tag = block.select_one(".courseblockextra")
        description = desc_tag.get_text(strip=True) if desc_tag else ""

        all_courses.append({
            "course_code": code,
            "course_name": name,
            "credit_hours": credit_contact,
            "description": description
        })

df = pd.DataFrame(all_courses)
df.to_csv("data/glen_oaks_courses.csv", index=False)
print("It worked!")
