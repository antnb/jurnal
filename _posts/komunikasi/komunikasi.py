import requests
from bs4 import BeautifulSoup
import re
import os
import random
import string
import html

# Function to clean up HTML and extract text content
def clean_html(html_content):
    cleaned_content = re.sub(r'<.*?>', '', html_content)
    cleaned_content = re.sub(r'\s+', ' ', cleaned_content)
    return cleaned_content.strip()

# Function to remove double colons, semicolons, or commas after tags:
def remove_double_colons(text):
    return re.sub(r'(?<=tags: )[:;,]+\s*', '', text)

# Function to remove semicolons, colons, or commas at the beginning of the Keywords section
def remove_colons(text):
    return re.sub(r'(?<=### Keywords\n)[:;,]+\s*', '', text)

# Read URLs from the text file
with open("urls.txt", "r", encoding="utf-8") as file:
    urls = file.readlines()

# Initialize lists to store debugging information
urls_processed = []
urls_failed = []
reasons_failed = []

# Loop through each URL
for url in urls:
    url = url.strip()  # Remove any leading/trailing whitespaces or newlines
    if not url:
        continue  # Skip processing empty URLs
    urls_processed.append(url)

    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract relevant information from the HTML and HTML escape special characters
        title_raw = soup.find("h1", class_="page_title").get_text().strip()
        title = f'"{html.escape(title_raw, quote=True)}"'

        # Sanitize title for use as a filename
        sanitized_title = re.sub(r'[^\w\s-]', '', title).strip()
        sanitized_title = re.sub(r'[-\s]+', '-', sanitized_title)

        # Extract authors and affiliations
        authors_list = []
        authors_html = soup.find("ul", class_="item authors")
        if authors_html:
            authors_items = authors_html.find_all("li")
            for author_item in authors_items:
                author_name = html.escape(author_item.find("span", class_="name").get_text().strip())
                author_affiliation = author_item.find("span", class_="affiliation")
                if author_affiliation:
                    author_affiliation = f" ({html.escape(author_affiliation.get_text().strip())})"
                else:
                    author_affiliation = ""
                authors_list.append(f"{author_name}{author_affiliation}")

        # Extract abstract
        abstract_div = soup.find("div", class_="item abstract")
        if abstract_div:
            abstract_content = clean_html(str(abstract_div))
            abstract_match = re.search(r'(?i)(abstract|abstrak):?(.*)', abstract_content)
            if abstract_match:
                abstract_raw = abstract_match.group(2).strip()
                abstract = f'"{html.escape(abstract_raw, quote=True)}"'
            else:
                abstract = "Abstract Not Available"

            # Extract keywords
            keywords_match = re.search(r'(?i)(keywords|kata kunci):?\s*(.*)', abstract_content)
            if keywords_match:
                keywords = [html.escape(kw.strip()) for kw in keywords_match.group(2).split(',')]
            else:
                keywords = []
        else:
            abstract = "Abstract Not Available"
            keywords = []

        # Extract publication date
        publication_date = html.escape(soup.find("div", class_="item published").find("div", class_="value").get_text().strip())

        # Extract citation information and format it properly
        citation_output = html.escape(soup.find("div", id="citationOutput").get_text().strip())

        # Extract issue information
        issue_element = soup.find("div", class_="item issue")
        issue_text = html.escape(issue_element.find("div", class_="value").get_text(strip=True))

        # Scrape Downloads link
        downloads_link_element = soup.find("a", class_="obj_galley_link pdf")
        if downloads_link_element:
            downloads_link = downloads_link_element["href"]
        else:
            downloads_link = "Download Not Available Yet"

        # Generate a random string of 6 alphanumeric characters
        random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        
        # Function to generate front matter section with encoded special characters
        def generate_front_matter(title, authors_list, abstract, keywords):
            encoded_title = html.escape(title, quote=True)
            encoded_authors = [html.escape(author, quote=True) for author in authors_list]
            encoded_abstract = html.escape(abstract, quote=True)
            encoded_keywords = [html.escape(keyword, quote=True) for keyword in keywords]

        # Construct Markdown content
        markdown_content = f'''---
layout: post
title: "{title}"
author: "{', '.join([author.split('(')[0].strip() for author in authors_list])}"
description: {abstract[:150]}
categories: komunikasi
{'tags: ' + ', '.join(keywords) if keywords else ''}
---

## Authors:
{', '.join(authors_list)}

## Abstract:
{abstract}

### Keywords
{'Keyword Not Available' if not keywords else ', '.join(keywords)}

## Downloads:
{downloads_link}

## Published
{publication_date}

## How To Cite
{citation_output}

## Citation Format Options:
ABNT, APA, BibTeX, CBE, EndNote - EndNote format (Macintosh & Windows), MLA, ProCite - RIS format (Macintosh & Windows), RefWorks, Reference Manager - RIS format (Windows only), Turabian

## Issue
{issue_text}
'''

        # Apply search and replace functions
        markdown_content = remove_double_colons(markdown_content)
        markdown_content = remove_colons(markdown_content)

        # Extract the numeric part from the URL
        numeric_part = re.search(r'\d+$', url).group()

        # Modify the file name to include DC.Date.created and the numeric part
        file_name = f"{publication_date}-id-{numeric_part}.md" if publication_date else f"unknown-id-{numeric_part}.md"

        # Save the Markdown content to a file with the modified name
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(markdown_content)

        print(f"Scraped information saved to '{file_name}'")
    else:
        urls_failed.append(url)
        reasons_failed.append(f"Failed to retrieve content from {url}")

# Save debugging information to a text file
with open("debug_info.txt", "w", encoding="utf-8") as debug_file:
    debug_file.write("URLs Processed:\n")
    debug_file.write("\n".join(urls_processed))
    debug_file.write("\n\nURLs Failed:\n")
    debug_file.write("\n".join(urls_failed))
    debug_file.write("\n\nReasons for Failure:\n")
    debug_file.write("\n".join(reasons_failed))

print("Scraping and Markdown conversion completed!")