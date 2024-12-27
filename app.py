import streamlit as st
import requests
from bs4 import BeautifulSoup
import urllib.parse
from io import BytesIO
import zipfile
import os
import base64
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

def is_same_domain(url1, url2):
    """Check if two URLs belong to the same domain"""
    domain1 = urllib.parse.urlparse(url1).netloc
    domain2 = urllib.parse.urlparse(url2).netloc
    return domain1 == domain2

def save_data_url(data_url, zip_file, count, folder='images'):
    """Handle data URL images"""
    try:
        header, encoded = data_url.split(',', 1)
        file_type = header.split(';')[0].split('/')[1]
        
        if 'svg+xml' in header:
            file_type = 'svg'
            if '%3Csvg' in encoded:
                encoded = urllib.parse.unquote(encoded)
                zip_file.writestr(f'{folder}/embedded_image_{count}.{file_type}', encoded)
                return True
        
        if 'base64' in header:
            data = base64.b64decode(encoded)
            zip_file.writestr(f'{folder}/embedded_image_{count}.{file_type}', data)
            return True
            
        return False
    except Exception as e:
        return False

def process_page(url, base_url, zip_file, visited_urls, max_pages=10):
    """Process a single page and its assets"""
    if url in visited_urls or len(visited_urls) >= max_pages:
        return
    
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        visited_urls.add(url)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Modify paths in HTML to be relative
        page_path = url[len(base_url):] if url.startswith(base_url) else 'index.html'
        page_path = page_path.lstrip('/') or 'index.html'
        
        # Process images
        image_count = 0
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                if src.startswith('data:'):
                    # Handle data URLs
                    if save_data_url(src, zip_file, image_count):
                        new_src = f'images/embedded_image_{image_count}'
                        img['src'] = new_src
                        image_count += 1
                else:
                    # Keep external links as they are
                    full_url = urllib.parse.urljoin(url, src)
                    if not is_same_domain(base_url, full_url):
                        img['src'] = full_url
        
        # Save the modified HTML
        zip_file.writestr(f'html/{page_path}', str(soup))
        
        # Download CSS files from same domain
        for css in soup.find_all('link', rel='stylesheet'):
            href = css.get('href')
            if href:
                css_url = urllib.parse.urljoin(url, href)
                if is_same_domain(base_url, css_url):
                    try:
                        css_response = requests.get(css_url, headers=HEADERS)
                        css_path = css_url[len(base_url):].lstrip('/')
                        zip_file.writestr(f'css/{css_path}', css_response.content)
                    except Exception as e:
                        continue
        
        # Download JavaScript files from same domain
        for js in soup.find_all('script', src=True):
            src = js.get('src')
            if src:
                js_url = urllib.parse.urljoin(url, src)
                if is_same_domain(base_url, js_url):
                    try:
                        js_response = requests.get(js_url, headers=HEADERS)
                        js_path = js_url[len(base_url):].lstrip('/')
                        zip_file.writestr(f'js/{js_path}', js_response.content)
                    except Exception as e:
                        continue
        
        # Find and process internal links
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            full_url = urllib.parse.urljoin(url, href)
            if is_same_domain(base_url, full_url) and full_url not in visited_urls:
                process_page(full_url, base_url, zip_file, visited_urls, max_pages)
                
    except Exception as e:
        st.warning(f"Error processing {url}: {str(e)}")

def download_website(url, max_pages=10):
    """Download entire website with related pages"""
    zip_buffer = BytesIO()
    visited_urls = set()
    
    try:
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            process_page(url, url, zip_file, visited_urls, max_pages)
            
        return zip_buffer.getvalue()
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# Streamlit UI
st.title('Website Downloader')

url = st.text_input('Enter website URL (e.g., https://example.com)')
max_pages = st.slider('Maximum number of pages to download', 1, 50, 10)

if st.button('Download Website'):
    if url:
        with st.spinner('Downloading website...'):
            zip_data = download_website(url, max_pages)
            if zip_data:
                st.success('Download ready!')
                st.download_button(
                    label="Download ZIP file",
                    data=zip_data,
                    file_name="website_content.zip",
                    mime="application/zip"
                )
    else:
        st.warning('Please enter a URL')

st.markdown("""
---
### Features:
- Downloads full website structure up to specified number of pages
- Maintains external links as-is
- Downloads internal CSS, JavaScript, and embedded images
- Preserves website structure in the ZIP file
- Handles data URLs and embedded content

### Notes:
- Some websites may block automated downloads
- Make sure you have permission to download content
- Large websites may take longer to process
""")
