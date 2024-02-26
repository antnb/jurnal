import os
import requests
from bs4 import BeautifulSoup
import re
import random
import string
import html
import time
import threading
import shutil
from datetime import datetime

# Create folders if they don't exist
folders = ['posts', 'full_articles', 'pdfs']
for folder in folders:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Function to clean up HTML and extract text content
def clean_html(html_content):
    cleaned_content = re.sub(r'<.*?>', '', html_content)
    cleaned_content = re.sub(r'\s+', ' ', cleaned_content)
    return cleaned_content.strip()

# Function to encode special characters in title
def encode_special_characters(title):
    # Replace special characters with their HTML entities
    encoded_title = html.escape(title)
    return encoded_title

# Function to strip special characters from description
def strip_special_characters(description):
    stripped_description = re.sub(r'[^a-zA-Z0-9\s]', '', description)
    return stripped_description

# Function to download and rename PDF document
def download_and_rename_pdf(url, numeric_part):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise HTTPError for bad responses

        # Define file name for PDF (using numeric part)
        file_name = f"pdfs/{numeric_part}.pdf"

        # Download PDF and save it with the defined file name
        with open(file_name, 'wb') as pdf_file:
            shutil.copyfileobj(response.raw, pdf_file)

        print(f"PDF downloaded and saved as '{file_name}'")

    except Exception as e:
        print(f"Failed to download PDF. Reason: {str(e)}")

# Read URLs from the text file
with open("urls.txt", "r", encoding="utf-8") as file:
    urls = file.readlines()

# Process each URL sequentially
for url in urls:
    try:
        url = url.strip()  # Remove leading/trailing whitespace and newline characters
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses

        # Parse HTML content
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract relevant information from the HTML
        title_raw = soup.find("h1", class_="page-header").get_text(strip=True)
        title = encode_special_characters(title_raw)

        # Sanitize title for use as a filename
        sanitized_title = re.sub(r'[^\w\s-]', '', title).strip()
        sanitized_title = re.sub(r'[-\s]+', '-', sanitized_title)

        # Extract authors
        authors_list = []
        authors_html = soup.find("div", class_="authors")
        if authors_html:
            author_names = authors_html.find_all("strong")
            for author in author_names:
                author_name = author.get_text().strip()
                authors_list.append(author_name)
        else:
            raise ValueError("Failed to locate authors information. Element with class 'authors' not found.")

        # Join author names separated by comma
        authors = ', '.join(authors_list)


        abstract_div = soup.find("div", class_="article-abstract")
        abstract = clean_html(abstract_div.get_text(strip=True)) if abstract_div else ""

        # Extract keywords if present
        keywords_match = re.search(r'(?i)(keywords|kata kunci):?\s*(.*)', abstract)
        keywords = [kw.strip() for kw in keywords_match.group(2).split(',')] if keywords_match else []

        # Extract publication date
        publication_date_element = soup.find("div", class_="list-group-item date-published")
        publication_date_text = publication_date_element.find("strong").next_sibling.strip() if publication_date_element else ""
        try:
            # Attempt to parse the date
            publication_date = datetime.strptime(publication_date_text, "%b %d, %Y").strftime("%Y-%m-%d")
        except ValueError:
            publication_date = "2021-11-09"  # Fallback date if publication date is not found

        # Extract citation information
        citation_output_element = soup.find("div", id="citationOutput")
        citation_output_text = citation_output_element.get_text(strip=True).strip().replace("\n", " ").replace("\t", "") if citation_output_element else ""

        # Replace "Date accessed: random tanggal,hari dan tahun" with "Date accessed: {{ site.time | date: "%d %b. %Y" }}"
        citation_output_text = re.sub(r'Date accessed: \d{1,2} \w{3}\. \d{4}', 'Date accessed: {{ site.time | date: "%d %b. %Y" }}', citation_output_text)
        # Replace the undesired URL pattern with the desired one
        citation_output_text = re.sub(r'https://ojs\.unud\.ac\.id/index\.php/spektrum/article/view/(\d+)', r'https://jurnal.harianregional.com/spektrum/id-\1', citation_output_text)
        # Extract the numeric part from the URL
        numeric_part = re.search(r'\d+$', url).group()

        # Construct canonical URL
        canonical_url = f"https://jurnal.harianregional.com/spektrum/id-{numeric_part}"
        # Extract issue information
        issue_element = soup.find("div", class_="panel panel-default issue")
        issue_text = issue_element.find("a", class_="title").get_text(strip=True) if issue_element else ""

        # Scrape Downloads link
        downloads_link_element = soup.find("a", class_="galley-link btn btn-default pdf")
        downloads_link = downloads_link_element["href"] if downloads_link_element else ""

        # Extract references information
        references_element = soup.find("div", class_="item references")
        references_text = references_element.find("div", class_="value").get_text(strip=True) if references_element else ""
        references_formatted = '\n'.join(f"- {ref.strip()}" for ref in references_text.split("\n")) if references_text else "References Not Available"

        # Extract DOI
        doi_element = soup.find("div", class_="list-group-item doi")
        if doi_element:
            doi_link = doi_element.find("a")
            doi = doi_link.get("href") if doi_link else "DOI Not Available"
        else:
            doi = "DOI Not Available"
    
        # Generate Markdown content
        markdown_content = f'''---
layout: post
title: "{title}"
author: "{authors}"
description: "{strip_special_characters(abstract[:170])}"
categories: spektrum
comments: true
canonical_url: {canonical_url}
tags:
{'  - "' + '"\n  - "'.join(keywords) + '"' if keywords else ''}
---
##  PDF
{downloads_link}

### Published
{publication_date}

### DOI
{doi}
## Main Article Content

## Authors:
{', '.join(authors_list)}

## Abstract:
{abstract}

### Keywords
{'*Keyword Not Available*' if not keywords else ', '.join(['*' + keyword + '*' for keyword in keywords])}

### Downloads:
{downloads_link}

## References
{references_formatted}

## Article Details

### How To Cite
{citation_output_text}

### Issue
{issue_text}

### Copyright 
<a href="http://creativecommons.org/licenses/by/4.0/" rel="license"><img src="https://i.creativecommons.org/l/by/4.0/88x31.png" alt="Creative Commons License" /></a>
This work is licensed under a <a href="http://creativecommons.org/licenses/by/4.0/" rel="nofollow">Creative Commons Attribution 4.0 International License</a>

'''

        # Modify the file name to include DC.Date.created and the numeric part
        numeric_part = re.search(r'\d+$', url).group()
        post_file_name = f"posts/{publication_date}-id-{numeric_part}.md" if publication_date else f"posts/unknown-id-{numeric_part}.md"

        # Save the Markdown content to a file with the modified name
        with open(post_file_name, "w", encoding="utf-8") as file:
            file.write(markdown_content)

        print(f"Scraped information saved to '{post_file_name}'")

        # Download and rename PDF document
        pdf_url = soup.find("meta", {"name": "citation_pdf_url"})['content']
        download_and_rename_pdf(pdf_url, numeric_part)

    except Exception as e:
        print(f"Failed to process {url}. Reason: {str(e)}")

# Notify completion
print("Scraping and Markdown conversion completed!")
