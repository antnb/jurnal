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

# Function to generate full article Markdown content
def generate_full_article_markdown(title, authors, abstract, canonical_url, keywords, numeric_part):
    markdown_content = f'''---
layout: full_article
title: "Full Article Of {encode_special_characters(title)}"
author: "{authors}"
description: "Full Article {strip_special_characters(abstract[:170])}"
categories: tropika
canonical_url: {canonical_url}
comments: true
tags:
{'  - "' + '"\n  - "'.join(keywords) + '"' if keywords else ''}
---


{strip_special_characters(abstract[:570])}"


        <object id="pdfObject" data="http://localhost:4000/pdf/107739.pdf" type="application/pdf" width="100%" height="600">
            <p style="font-size: 16px;">It appears you don't have a PDF plugin for this browser.
                You can <a href="http://localhost:4000/pdf/107739.pdf" target="_blank">download the PDF file</a>.</p>
        </object>


'''

    return markdown_content

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

# Function to process a single URL
def process_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses

        # Parse HTML content
        soup = BeautifulSoup(response.content, "html.parser")

        # Extract relevant information from the HTML
        title_raw = soup.find("h1", class_="page-header").get_text(strip=True)
        title = encode_special_characters(title_raw)

        authors_list = [author.get_text(strip=True) for author in soup.find_all("div", class_="authors") if author]
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
		
		

        # Generate a random string of 6 alphanumeric characters
        random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

        # Construct canonical URL
        canonical_url = f"https://jurnal.harianregional.com/tropika/id-{numeric_part}"

        # Generate full article Markdown content
        full_article_markdown = generate_full_article_markdown(title, authors, abstract, canonical_url, keywords, numeric_part)

        # Modify the file name to include 'full'
        full_article_file_name = f"full_articles/{publication_date}-full-{numeric_part}.md" if publication_date else f"full_articles/unknown-full-{numeric_part}.md"

        # Save the full article Markdown content to a file with the modified name
        with open(full_article_file_name, "w", encoding="utf-8") as file:
            file.write(full_article_markdown)

        print(f"Full article Markdown saved to '{full_article_file_name}'")

        # Download and rename PDF document
        pdf_url = soup.find("meta", {"name": "citation_pdf_url"})['content']
        download_and_rename_pdf(pdf_url, numeric_part)

    except Exception as e:
        print(f"Failed to process {url}. Reason: {str(e)}")
		
 # Generate Markdown content
        markdown_content = f'''---
layout: post
title: "{title}"
author: "{authors}"
description: "{strip_special_characters(abstract[:170])}"
categories: tropika
comments: true
tags:
{'  - "' + '"\n  - "'.join(keywords) + '"' if keywords else ''}
---

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

### Published
{publication_date}

### Citation Format
{citation_output_text}

### Issue
{issue_text}

'''

# Process URLs in parallel using threading
def process_urls_threaded(urls):
    # Create and start threads
    threads = [threading.Thread(target=lambda: process_url(url)) for url in urls]
    for thread in threads:
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

# Split URLs into chunks for threading
chunk_size = 20
url_chunks = [urls[i:i+chunk_size] for i in range(0, len(urls), chunk_size)]

# Process URLs in parallel using threading
for chunk in url_chunks:
    process_urls_threaded(chunk)

print("Scraping and Markdown conversion completed!")
