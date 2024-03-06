import requests
from bs4 import BeautifulSoup
import re

# Define file paths
urls_file_path = "urls.txt"
statistics_file_path = "scraping_statistics.txt"
failed_urls_file_path = "failed_urls.txt"

# Read URLs from the text file
with open(urls_file_path, "r") as file:
    urls = file.readlines()

# Initialize statistics
total_urls = len(urls)
successful_scrapes = 0
failed_scrapes = 0

# Initialize list to store failed URLs
failed_urls = []
# Read URLs from the text file
with open("urls.txt", "r") as file:
    urls = file.readlines()

# Iterate through each URL in the list
for url in urls:
    # Remove leading/trailing whitespaces and newlines from the URL
    url = url.strip()

    # Send a GET request to the URL
    response = requests.get(url)

    # Parse the HTML content
    soup = BeautifulSoup(response.content, "html.parser")

    # Scrape and save the title
    title = soup.find("h1", class_="page-header").text.strip()

    # Attempt to find the div containing the DOI
    doi_div = soup.find("div", class_="doi")

    if doi_div:
        doi_a = doi_div.find("a")
        if doi_a:
            doi_text = doi_a.text.strip()
            doi = f"https://doi.org/{doi_text}" if not doi_text.startswith("https://doi.org/") else doi_text
        else:
            doi = "DOI Not Available"
    else:
        doi = "DOI Not Available"



    # Extract and clean published date
    published_date = ""
    dc_date_created_meta = soup.find("meta", {"name": "DC.Date.created"})
    if dc_date_created_meta:
        published_date = dc_date_created_meta['content']
    else:
        dc_date_issued_meta = soup.find("meta", {"name": "DC.Date.issued"})
        if dc_date_issued_meta:
            published_date = dc_date_issued_meta['content']

    # Scrape authors list with affiliations
    authors_data = soup.find("div", class_="authors")
    authors_list = []

    for author_data in authors_data.find_all("strong"):
        # Scrape author name
        author_name = author_data.text.strip()
        
        # Check if affiliation element exists
        affiliation_element = author_data.find_next_sibling("div", class_='article-author-affilitation')
        affiliation = affiliation_element.text.strip() if affiliation_element else ""

        authors_list.append(f"{author_name} ({affiliation})")

    # Scrape abstract
    abstract_element = soup.find("div", class_="article-abstract")
    abstract = abstract_element.text.strip() if abstract_element else ""

    # Find keywords within the abstract
    keywords = ""
    if "Keywords" in abstract or "Kata kunci" in abstract:
       keywords_start_index = abstract.find("Keywords") if "Keywords" in abstract else abstract.find("Kata kunci")
       keywords_end_index = abstract.find("\n", keywords_start_index)  # Find the end of the line
       keywords_text = abstract[keywords_start_index:keywords_end_index].split(":")[1].strip()
       keywords_list = [keyword.strip() for keyword in keywords_text.split(",")]
       keywords = ", ".join(keywords_list)
    else:
       keywords = "Keywords Not Available"


    # Scrape Downloads link
    downloads_link_element = soup.find("a", class_="galley-link btn btn-default pdf")

    if downloads_link_element:
        downloads_link = downloads_link_element["href"]
    else:
        downloads_link = "Download Not Available Yet"



    # Scrape How to Cite section
    how_to_cite = soup.find("div", class_="panel-body").find("div", class_="citation_output").text.strip()

    # Scrape anchor text values from citation format options
    citation_format_options = [link.text.strip() for link in soup.find("div", class_="list-group citation_format_options").find_all("a")]

    # Scrape Issue section
    issue_title = soup.find("div", class_="panel panel-default issue").find("a", class_="title").text.strip()

    # Scrape Section
    section = soup.find("div", class_="panel panel-default section").find("div", class_="panel-body").text.strip()

    # Scrape Copyright section
    copyright = soup.find("div", class_="panel panel-default copyright").find("div", class_="panel-body").text.strip()

    # Scrape References section
    references_data = soup.find("div", class_="article-references")

    if references_data:
        references_content = references_data.find("div", class_="article-references-content")
        if references_content:
            references_list = references_content.stripped_strings
            references = "\n".join([f"- {reference}" for reference in references_list])
        else:
            references = "References not available yet."
    else:
        references = "References not available yet."
		
		
    # Scrape authors with and without affiliations
    authors_data = soup.find("div", class_="authors")
    authors_list = []
    authors_without_affiliation = []

    for author_data in authors_data.find_all("strong"):
        # Scrape author name
        author_name = author_data.text.strip()
        
        # Check if affiliation element exists
        affiliation_element = author_data.find_next_sibling("div", class_='article-author-affilitation')
        
        if affiliation_element:
            # If affiliation exists, scrape and add it to the author's name
            affiliation = affiliation_element.text.strip()
            authors_list.append(f"{author_name} ({affiliation})")
        else:
            # If no affiliation exists, add only the author's name without affiliation
            authors_list.append(author_name)
            authors_without_affiliation.append(author_name)
    # Generate Markdown content
    markdown_content = f'''---
layout: post
title: "{title}"
author: "{', '.join(authors_list)}"
tags: {keywords}
categories: jtip

---

## DOI:
{doi}

## Published Date:
{published_date.strip()}

## Authors:
{', '.join(authors_list)}

## Main Article Content

## Abstract:
{abstract}

### Keywords:
{keywords}

### Downloads:
{downloads_link}

## Article Details

## How to Cite:
{how_to_cite}

## Citation Format Options:
{', '.join(citation_format_options)}

## Issue:
{issue_title}

## Section:
{section}

## Copyright:
{copyright}

## References:
{references}
'''

    # Extract the numeric part from the URL
    numeric_part = re.search(r'\d+$', url).group()

    # Modify the file name to include DC.Date.created and the numeric part
    file_name = f"{published_date}-id-{numeric_part}.md" if published_date else f"unknown-id-{numeric_part}.md"

    # Save the Markdown content to a file with the modified name
    with open(file_name, "w", encoding="utf-8") as file:
        file.write(markdown_content)

    print(f"Scraped information saved to '{file_name}'")

# Write statistics to the statistics_file_path
with open(statistics_file_path, "w", encoding="utf-8") as statistics_file:
    statistics_file.write(f"Total URLs: {total_urls}\n")
    statistics_file.write(f"Successful Scrapes: {successful_scrapes}\n")
    statistics_file.write(f"Failed Scrapes: {failed_scrapes}\n")
    statistics_file.write(f"Failed URLs List: {failed_urls_file_path}\n")

# Print summary statistics
print("Scraping summary:")
print(f"Total URLs: {total_urls}")
print(f"Successful Scrapes: {successful_scrapes}")
print(f"Failed Scrapes: {failed_scrapes}")
print(f"Failed URLs List: {failed_urls_file_path}")