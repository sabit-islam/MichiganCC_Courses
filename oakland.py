"""
Northwestern Michigan College Course Scraper

Developed by: Sabit Islam 
Date: 08-14-2025

Developed for LSA Transfer Student Center and to be used for educational purposes only.
"""
import os
import re
import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE = "https://catalog.oaklandcc.edu"
INDEX = f"{BASE}/course-descriptions/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "close",
}

from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

session = requests.Session()
retry = Retry(
    total=5,
    connect=5,
    read=5,
    backoff_factor=0.8,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=frozenset(["GET", "HEAD"]),
    raise_on_status=False,
)
session.mount("https://", HTTPAdapter(max_retries=retry))
session.mount("http://", HTTPAdapter(max_retries=retry))

def clean(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").replace("\xa0", " ")).strip()

resp = session.get(INDEX, headers=HEADERS, timeout=30)
resp.raise_for_status()
soup = BeautifulSoup(resp.text, "html.parser")

dept_paths = []
for a in soup.select('a[href^="/course-descriptions/"]'):
    href = a.get("href", "")
    if re.fullmatch(r"/course-descriptions/[a-z0-9-]+/", href):
        dept_paths.append(href)

seen = set()
dept_paths = [p for p in dept_paths if not (p in seen or seen.add(p))]
print("Found departments:", len(dept_paths))

all_courses = []

for dept_path in dept_paths:
        url = urljoin(BASE, dept_path)
        time.sleep(0.5)  
        response = session.get(url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            continue
        print(f"Scraping {url}")
        soup = BeautifulSoup(response.text, "html.parser")

        for block in soup.select("div.courseblock"):
            title_p = block.select_one("p.courseblocktitle strong")
            if not title_p:
                continue
            print("fetching:" + title_p.get_text(strip=True))
            credit_span = title_p.select_one("span.coursecredithours")
            credit_hours = ""
            if credit_span:
                m = re.search(r"(\d+(?:\.\d+)?)", credit_span.get_text(" ", strip=True))
                if m:
                    credit_hours = m.group(1)
                credit_span.extract()

            title_txt = clean(title_p.get_text(" ", strip=True))

            m = re.match(r"^([A-Z&]+[A-Z]*\s*\d+[A-Z]?)\s+(.+)$", title_txt)
            if m:
                course_code = clean(m.group(1))
                course_name = clean(m.group(2))
            else:
                parts = re.split(r"\s{2,}", title_txt, maxsplit=1)
                course_code = clean(parts[0]) if parts else ""
                course_name = clean(parts[1]) if len(parts) > 1 else ""

            desc_chunks = []
            for p in block.select("p.courseblockdesc"):
                txt = clean(p.get_text(" ", strip=True))
                if not txt:
                    continue
                low = txt.lower()
                if low.startswith("equivalent:") or low.startswith("esl placement level:"):
                    continue
                desc_chunks.append(txt)

            description = " ".join(desc_chunks).strip()

            all_courses.append({
                "course_code": course_code,
                "course_name": course_name,
                "credit_hours": credit_hours,
                "description": description
            })


pd.DataFrame(all_courses).to_csv("data/oaklandcc.csv", index=False)
print("It worked!")
