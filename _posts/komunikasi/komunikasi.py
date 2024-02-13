import requests
from bs4 import BeautifulSoup
import re
import os
import random
import string
from html import unescape

# Function to clean up HTML and extract text content
def clean_html(html_content):
    cleaned_content = re.sub(r'<.*?>', '', html_content)  # Remove HTML tags
    cleaned_content = re.sub(r'\n+', ' ', cleaned_content)  # Remove new lines
    cleaned_content = cleaned_content.strip()  # Strip leading/trailing whitespace
    return cleaned_content

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
        continue  # Skip empty lines
    urls_processed.append(url)

    # Check if the URL is valid
    if not url.startswith("http"):
        urls_failed.append(url)
        reasons_failed.append(f"Invalid URL: {url}")
        continue

    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Extract relevant information from the HTML
        title = soup.find("h1", class_="page_title").get_text().strip()
        
        # Sanitize title for use as a filename
        sanitized_title = re.sub(r'[^\w\s-]', '', title).strip()
        sanitized_title = re.sub(r'[-\s]+', '-', sanitized_title)

        # Extract authors and affiliations
        authors_list = []
        authors_html = soup.find("ul", class_="item authors")
        if authors_html:
            authors_items = authors_html.find_all("li")
            for author_item in authors_items:
                author_name = author_item.find("span", class_="name").get_text().strip()
                author_affiliation = author_item.find("span", class_="affiliation")
                if author_affiliation:
                    author_affiliation = f" ({author_affiliation.get_text().strip()})"
                else:
                    author_affiliation = ""
                authors_list.append(f"{author_name}{author_affiliation}")

        # Extract abstract and keywords
        abstract_div = soup.find("div", class_="item abstract")
        if abstract_div:
            abstract_content = clean_html(str(abstract_div))
            # Check if the abstract contains "ABSTRAK" or "Abstract" and remove it
            abstract_content = re.sub(r'ABSTRAK|Abstract', '', abstract_content)
            # Extract keywords
            keywords_match = re.search(r'Keywords?:\s*(.+)', abstract_content, re.IGNORECASE)
            if keywords_match:
                keywords = keywords_match.group(1).strip().split(", ")
                # Remove the keywords from the abstract content
                abstract_content = abstract_content.replace(keywords_match.group(0), '').strip()
            else:
                keywords = ["Keywords Not Available"]
        else:
            abstract_content = "Abstract Not Available"
            keywords = ["Keywords Not Available"]

        # Extract publication date
        publication_date = soup.find("div", class_="item published").find("div", class_="value").get_text().strip()

        # Extract citation information and format it properly
        citation_output = soup.find("div", id="citationOutput").get_text().strip()
        citation_output = unescape(citation_output)  # Convert HTML entities to plain text
        citation_output = re.sub(r'\s+', ' ', citation_output)  # Remove unnecessary spaces
        
        # Extract issue information
        issue_element = soup.find("div", class_="item issue")
        issue_text = issue_element.find("div", class_="value").get_text(strip=True)
        
        # Remove hyperlink if present
        issue_text = re.sub(r'<.*?>', '', issue_text)

        # Scrape Downloads link
        downloads_link_element = soup.find("a", class_="obj_galley_link pdf")
        if downloads_link_element:
            downloads_link = downloads_link_element["href"]
        else:
            downloads_link = "Download Not Available Yet"

        # Generate a random string of 6 alphanumeric characters
        random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        
        # Construct Markdown content
        markdown_content = f'''---
layout: post
title: "{title}"
author: "{', '.join([author.split('(')[0].strip() for author in authors_list])}"
description: {abstract_content[:160]}
categories: komunikasi
tags: {', '.join(keywords)}
---

## Authors:
{', '.join(authors_list)}

## Published
{publication_date}

## Abstract:
{abstract_content}

### Keywords
{', '.join(keywords)}

## How To Cite
{citation_output}

## Issue
{issue_text}

## Downloads:
{downloads_link}
'''

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
