import re
import os
import requests
from bs4 import BeautifulSoup
import shutil

# Function to ensure folder existence
def ensure_folders_exist():
    folders = ['jte_pdfs', 'full_jte', 'article_bodies', 'media']
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)

# Function to extract page title and authors from HTML
def extract_data(html):
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.find('h1', class_='page_title').text.strip()
    authors = [author.text.strip() for author in soup.find_all('span', class_='name')]
    authors = ', '.join(authors)
    return title, authors

# Function to extract PDF download URL
def extract_pdf_url(html):
    soup = BeautifulSoup(html, 'html.parser')
    pdf_url = soup.find('meta', attrs={'name': 'citation_pdf_url'})
    if pdf_url:
        return pdf_url['content']
    return None

# Function to download and rename PDF document
def download_and_rename_pdf(url, numeric_part):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise HTTPError for bad responses
        
        # Define file name for PDF (using numeric part)
        file_name = f"jte_pdfs/{numeric_part}.pdf"
        
        # Download PDF and save it with the defined file name
        with open(file_name, 'wb') as pdf_file:
            for chunk in response.iter_content(chunk_size=128):
                pdf_file.write(chunk)
        
        print(f"PDF downloaded and saved as '{file_name}'")
        
    except Exception as e:
        print(f"Failed to download PDF. Reason: {str(e)}")

# Function to download assets and update asset references in HTML body
def download_assets_and_update_references(body_html, numeric_part):
    asset_folder = f"article_bodies/{numeric_part}_files"
    if os.path.exists(asset_folder):
        media_folder = "media"
        if not os.path.exists(media_folder):
            os.makedirs(media_folder)
        
        asset_files = os.listdir(asset_folder)
        for asset_file in asset_files:
            asset_path = os.path.join(asset_folder, asset_file)
            new_asset_path = f"{media_folder}/{asset_file}"
            shutil.copy(asset_path, new_asset_path)
            # Update asset references in the HTML body
            body_html = body_html.replace(asset_path, new_asset_path)

    # Update asset references in the HTML body to point to the media folder
    body_html = body_html.replace(f"{numeric_part}_files/", "https://jurnal.harianregional.com/media/")

    return body_html

# Main function to process URLs
def process_urls(file_path):
    ensure_folders_exist()
    with open(file_path, 'r') as file:
        urls = file.readlines()
        
    for url in urls:
        try:
            url = url.strip()
            numeric_part = re.search(r'\d+$', url).group()
            
            response = requests.get(url)
            response.raise_for_status()
            html = response.text
            
            title, authors = extract_data(html)
            pdf_url = extract_pdf_url(html)
            
            if pdf_url:
                download_and_rename_pdf(pdf_url, numeric_part)
            
            # Extract publication date
            soup = BeautifulSoup(html, 'html.parser')
            publication_date = soup.find("div", class_="item published")
            if publication_date:
                publication_date = publication_date.find("div", class_="value").get_text().strip()
            else:
                publication_date = "2021-11-09" # You can customize this date as needed
            
            # Extract article body from local file
            with open(f"article_bodies/{numeric_part}.htm", 'r', encoding='utf-8') as body_file:
                body_html = body_file.read()

            # Download assets and update asset references in the HTML body
            body_html = download_assets_and_update_references(body_html, numeric_part)

            # Find the position of <body> and </body> tags
            start_index = body_html.find('<body>')
            end_index = body_html.find('</body>')

            # Extract the body content between <body> and </body>
            article_body = body_html[start_index + len('<body>'):end_index].strip()

            # Clean up HTML using BeautifulSoup
            soup = BeautifulSoup(article_body, 'html.parser')
            clean_article_body = soup.prettify()

            # Update the canonical URL format
            canonical_url = f"https://jurnal.harianregional.com/jte/full-{numeric_part}"

            # Update the citation abstract HTML URL dynamically based on numeric_part
            citation_abstract_html_url = f"https://jurnal.harianregional.com/jte/id-{numeric_part}"

            # Include citation_abstract_html_url in YAML front matter
            markdown_content = f'''---
layout: full_article
title: "{title}"
author: "{authors}"
categories: jte
canonical_url: {canonical_url} 
citation_abstract_html_url: "{citation_abstract_html_url}"
citation_pdf_url: "{canonical_url}"  
comments: true
---

{article_body}'''

            # Modify the file name to include 'full'
            full_article_file_name = f"full_jte/{publication_date}-full-{numeric_part}.md" if publication_date else f"full_articles/unknown-full-{numeric_part}.md"
            
            # Write markdown template to file with modified name
            with open(full_article_file_name, 'w', encoding='utf-8') as markdown_file:
                markdown_file.write(markdown_content)
        except Exception as e:
            print(f"Error processing URL: {url}. Reason: {str(e)}")
            continue

if __name__ == "__main__":
    process_urls("urls.txt")
