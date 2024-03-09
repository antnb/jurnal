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

# Create folders if they don't exist
folders = ['posts', 'full_ujossh', 'ujossh_pdfs']
for folder in folders:
    if not os.path.exists(folder):
        os.makedirs(folder)

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

def encode_special_characters(title):
    # Replace single quotation marks
    title = title.replace('‘', '&lsquo;').replace('’', '&rsquo;')
    
    # Replace double quotation marks
    title = title.replace('“', '&ldquo;').replace('”', '&rdquo;').replace('"', '&quot;')
    
    # Replace other special characters as needed
    title = title.replace('—', '&mdash;').replace('–', '&ndash;')
    title = title.replace('©', '&copy;').replace('®', '&reg;')

    # Add more replacements as necessary

    return title

# Function to strip special characters from description
def strip_special_characters(description):
    return re.sub(r'[^a-zA-Z0-9\s]', '', description)

def generate_full_article_markdown(title, authors, abstract, canonical_url, keywords, numeric_part):
    # Update the canonical URL format
    canonical_url = f"https://jurnal.harianregional.com/ujossh/full-{numeric_part}"

    # Update the citation abstract HTML URL dynamically based on numeric_part
    citation_abstract_html_url = f"https://jurnal.harianregional.com/ujossh/id-{numeric_part}"

    # Include citation_abstract_html_url in YAML front matter
    markdown_content = f'''---
layout: full_article
title: "Full Article Of {encode_special_characters(title)}"
author: "{authors}"
description: "Full Article {strip_special_characters(abstract[:170])}"
categories: ujossh
canonical_url: {canonical_url} 
citation_abstract_html_url: "{citation_abstract_html_url}"  
citation_pdf_url: "{canonical_url}"  
comments: true
tags:
{'  - "' + '"\n  - "'.join(keywords) + '"' if keywords else ''}
---

{{% include adsense2.html %}}
{strip_special_characters(abstract[:470])}

{{% include adsense1.html %}}

<div style="position: relative; width: 100%; max-width: 1000px;">
    <!-- PDF viewer container -->
    <div style="position: relative; padding-bottom: 100%; overflow: hidden;">
        <!-- PDF viewer -->
        {{% include inarticle.html %}}
        <object data="https://jurnal.harianregional.com/pdf/ujossh/{numeric_part}.pdf" type="application/pdf" width="100%" height="100%" style="position: absolute; top: 0; left: 0;">
            <!-- Fallback content for browsers that cannot display ujossh_pdfs -->
            <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; background-color: #f8f9fa; display: flex; justify-content: center; align-items: center;">
                        <div style="position: absolute; top: 10px; right: 10px; z-index: 9999;">
                {{% include adsense2.html %}}
            </div>
                <p>Sorry, your browser does not support embedded ujossh_pdfs. <a href="https://jurnal.harianregional.com/pdf/ujossh/{numeric_part}.pdf" target="_blank">Click here to view it.</a></p>
            </div>
            <!-- AdSense ad code -->
            <div style="position: absolute; top: 10px; right: 10px; z-index: 9999;">
                {{% include adsense3.html %}}
            </div>
        </object>
    </div>

'''

    return markdown_content




# Function to download and rename PDF document
def download_and_rename_pdf(url, numeric_part):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise HTTPError for bad responses
        
        # Define file name for PDF (using numeric part)
        file_name = f"ujossh_pdfs/{numeric_part}.pdf"
        
        # Download PDF and save it with the defined file name
        with open(file_name, 'wb') as pdf_file:
            shutil.copyfileobj(response.raw, pdf_file)
        
        print(f"PDF downloaded and saved as '{file_name}'")
        
    except Exception as e:
        print(f"Failed to download PDF. Reason: {str(e)}")

# Read URLs from the text file
with open("urls.txt", "r", encoding="utf-8") as file:
    urls = file.readlines()

# Initialize lists to store debugging information
urls_processed = []
urls_failed = []
reasons_failed = []

# Function to process a single URL
def process_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses

        encoding = response.encoding if response.encoding else 'utf-8'
        soup = BeautifulSoup(response.content.decode(encoding), "html.parser")

        # Extract relevant information from the HTML
        title_raw = soup.find("h1", class_="page_title")
        if title_raw:
            title_raw = title_raw.get_text().strip()
            title = encode_special_characters(title_raw)
            
            # Sanitize title for use as a filename
            sanitized_title = re.sub(r'[^\w\s-]', '', title).strip()
            sanitized_title = re.sub(r'[-\s]+', '-', sanitized_title)
        else:
            raise ValueError("Failed to locate title information. Element with class 'page_title' not found.")

        # Extract authors
        authors_list = []
        authors_html = soup.find("ul", class_="item authors")
        if authors_html:
            authors_items = authors_html.find_all("li")
            for author_item in authors_items:
                author_name = author_item.find("span", class_="name").get_text().strip()
                authors_list.append(author_name)
        else:
            raise ValueError("Failed to locate authors information. Element with class 'item authors' not found.")

        # Join author names separated by comma
        authors = ', '.join(authors_list)

        # Extract abstract
        abstract_div = soup.find("div", class_="item abstract")
        if abstract_div:
            abstract_content = clean_html(str(abstract_div))
            abstract_match = re.search(r'(?i)(abstract|abstrak):?(.*)', abstract_content)
            if abstract_match:
                abstract_raw = abstract_match.group(2).strip()
                abstract = f'"{abstract_raw}"'
            else:
                abstract = "Abstract Not Available"

            # Extract keywords
            keywords_match = re.search(r'(?i)(keywords|kata kunci):?\s*(.*)', abstract_content)
            if keywords_match:
                keywords = [kw.strip() for kw in keywords_match.group(2).split(',')]
            else:
                keywords = []
        else:
            abstract = "Abstract Not Available"
            keywords = []

        # Extract publication date
        publication_date = soup.find("div", class_="item published")
        if publication_date:
            publication_date = publication_date.find("div", class_="value").get_text().strip()
        else:
            publication_date = "2021-11-09"  # You can customize this date as needed

        # Extract citation information
        citation_output_element = soup.find("div", id="citationOutput")
        citation_output_text = citation_output_element.get_text(strip=True) if citation_output_element else ""
        citation_output_text = citation_output_text.strip().replace("\n", " ").replace("\t", "")
        
        # Replace "Date accessed: random tanggal,hari dan tahun" with "Date accessed: {{ site.time | date: "%d %b. %Y" }}"
        citation_output_text = re.sub(r'Date accessed: \d{1,2} \w{3}\. \d{4}', 'Date accessed: {{ site.time | date: "%d %b. %Y" }}', citation_output_text)
        # Replace the undesired URL pattern with the desired one
        citation_output_text = re.sub(r'https://ojs\.unud\.ac\.id/index\.php/ujossh/article/view/(\d+)', r'https://jurnal.harianregional.com/ujossh/id-\1', citation_output_text)
        # Extract the numeric part from the URL
        numeric_part = re.search(r'\d+$', url).group()

        # Construct canonical URL
        canonical_url = f"https://jurnal.harianregional.com/ujossh/id-{numeric_part}"
        buat_url = f"https://jurnal.harianregional.com/ujossh/full-{numeric_part}"
        # Update the citation abstract HTML URL
        citation_abstract_html_url = f"https://jurnal.harianregional.com/ujossh/id-{numeric_part}"
        citation_pdf_url = f"https://jurnal.harianregional.com/ujossh/full-{numeric_part}"
        
        # Extract issue information
        issue_text = soup.find("div", class_="item issue").find("div", class_="value").get_text(strip=True)

        # Scrape Downloads link
        downloads_link_element = soup.find("a", class_="obj_galley_link pdf")
        downloads_link = downloads_link_element["href"] if downloads_link_element else "Download Not Available Yet"

        # Extract references information
        references_element = soup.find("div", class_="item references")
        references_formatted = ""

        if references_element:
            references_text = references_element.find("div", class_="value")

            if references_text:
               references_list = [ref.strip() for ref in references_text.stripped_strings]
               references_formatted = '\n'.join(f"- {ref}" for ref in references_list if ref)
            else:
               references_formatted = "References Not Available"
        else:
            references_formatted = "References Not Available"

        # Generate a random string of 6 alphanumeric characters
        random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

        # Construct Markdown content
        markdown_content = f'''---
layout: post
title: "{encode_special_characters(title)}"
author: "{authors}"
description: "{strip_special_characters(abstract[:170])}"
categories: ujossh
canonical_url: {canonical_url}
comments: true
citation_abstract_html_url: "{citation_abstract_html_url}"
citation_pdf_url: "{citation_pdf_url}"
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
Download data is not yet available.

{{% include adsense.html %}}
## References
{references_formatted}

### PDF:

{{% include adsense1.html %}}

<{buat_url}>

{{% include adsense2.html %}}

### Published
{publication_date}

### How To Cite
{citation_output_text}

## Citation Format
ABNT, APA, BibTeX, CBE, EndNote - EndNote format (Macintosh & Windows), MLA, ProCite - RIS format (Macintosh & Windows), RefWorks, Reference Manager - RIS format (Windows only), Turabian

### Issue
{issue_text}

### Section 
**Articles**

### Copyright 
{{% include inarticle.html %}}
<a href="http://creativecommons.org/licenses/by/4.0/" rel="license"><img src="https://i.creativecommons.org/l/by/4.0/88x31.png" alt="Creative Commons License" /></a>
This work is licensed under a <a href="http://creativecommons.org/licenses/by/4.0/" rel="nofollow">Creative Commons Attribution 4.0 International License</a>

{{% include multiplex.html %}}
'''


        
        # Apply search and replace functions
        markdown_content = remove_double_colons(markdown_content)
        markdown_content = remove_colons(markdown_content)

        # Extract the numeric part from the URL
        numeric_part = re.search(r'\d+$', url).group()

        # Modify the file name to include DC.Date.created and the numeric part
        post_file_name = f"posts/{publication_date}-id-{numeric_part}.md" if publication_date else f"posts/unknown-id-{numeric_part}.md"

        # Save the Markdown content to a file with the modified name
        with open(post_file_name, "w", encoding="utf-8") as file:
            file.write(markdown_content)

        print(f"Scraped information saved to '{post_file_name}'")

        # Generate full article Markdown content
        full_article_markdown = generate_full_article_markdown(title, authors, abstract, canonical_url, keywords, numeric_part)

        # Modify the file name to include 'full'
        full_article_file_name = f"full_ujossh/{publication_date}-full-{numeric_part}.md" if publication_date else f"full_articles/unknown-full-{numeric_part}.md"

        # Save the full article Markdown content to a file with the modified name
        with open(full_article_file_name, "w", encoding="utf-8") as file:
            file.write(full_article_markdown)

        print(f"Full article Markdown saved to '{full_article_file_name}'")

        # Add URL to processed list
        urls_processed.append(url)

        # Download and rename PDF document
        pdf_url = soup.find("meta", {"name": "citation_pdf_url"})['content']
        download_and_rename_pdf(pdf_url, numeric_part)

    except Exception as e:
        # Log the error information and add URL to failed list
        urls_failed.append(url)
        reasons_failed.append(f"Failed to process {url}. Reason: {str(e)}")

# Function to process URLs in parallel using threading
def process_urls_threaded(urls):
    # Create and start threads
    threads = []
    for url in urls:
        thread = threading.Thread(target=lambda: process_url(url))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

# Split URLs into chunks for threading
chunk_size = 30
url_chunks = [urls[i:i+chunk_size] for i in range(0, len(urls), chunk_size)]

# Process URLs in parallel using threading
for chunk in url_chunks:
    process_urls_threaded(chunk)

# Save debugging information to a text file after all URLs have been processed
with open("debug_info.txt", "w", encoding="utf-8") as debug_file:
    debug_file.write("URLs Processed:\n")
    debug_file.write("\n".join([f'"{url}"' for url in urls_processed]))
    debug_file.write("\n\nURLs Failed:\n")
    debug_file.write("\n".join([f'"{url}" - {reason}' for url, reason in zip(urls_failed, reasons_failed)]))

print("Scraping, Markdown conversion, and PDF downloading completed!")
