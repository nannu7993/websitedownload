import streamlit as st
import requests
from bs4 import BeautifulSoup
import urllib.parse
from io import BytesIO
import zipfile
import os

# Define headers to mimic a regular browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

def download_assets(url):
    zip_buffer = BytesIO()
    
    try:
        # Download main page with headers
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        base_url = urllib.parse.urljoin(url, '/')
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Save HTML
            zip_file.writestr('html/index.html', response.text)
            
            # Download images
            for img in soup.find_all('img'):
                src = img.get('src')
                if src:
                    try:
                        img_url = urllib.parse.urljoin(base_url, src)
                        img_name = os.path.basename(urllib.parse.urlparse(img_url).path)
                        if not img_name:
                            continue
                        img_response = requests.get(img_url, headers=HEADERS)  # Added headers
                        zip_file.writestr(f'images/{img_name}', img_response.content)
                    except Exception as e:
                        st.warning(f"Failed to download image: {img_url}")
                        continue

            # Download CSS
            for css in soup.find_all('link', rel='stylesheet'):
                href = css.get('href')
                if href:
                    try:
                        css_url = urllib.parse.urljoin(base_url, href)
                        css_name = os.path.basename(urllib.parse.urlparse(css_url).path)
                        if not css_name:
                            continue
                        css_response = requests.get(css_url, headers=HEADERS)  # Added headers
                        zip_file.writestr(f'css/{css_name}', css_response.content)
                    except Exception as e:
                        st.warning(f"Failed to download CSS: {css_url}")
                        continue

            # Download JavaScript
            for js in soup.find_all('script', src=True):
                src = js.get('src')
                if src:
                    try:
                        js_url = urllib.parse.urljoin(base_url, src)
                        js_name = os.path.basename(urllib.parse.urlparse(js_url).path)
                        if not js_name:
                            continue
                        js_response = requests.get(js_url, headers=HEADERS)  # Added headers
                        zip_file.writestr(f'js/{js_name}', js_response.content)
                    except Exception as e:
                        st.warning(f"Failed to download JavaScript: {js_url}")
                        continue

        return zip_buffer.getvalue()
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# Streamlit UI
st.title('Website Asset Downloader')

url = st.text_input('Enter website URL (e.g., https://example.com)')

if st.button('Download Assets'):
    if url:
        with st.spinner('Downloading assets...'):
            zip_data = download_assets(url)
            if zip_data:
                st.success('Download ready!')
                st.download_button(
                    label="Download ZIP file",
                    data=zip_data,
                    file_name="website_assets.zip",
                    mime="application/zip"
                )
    else:
        st.warning('Please enter a URL')

# Add some helpful information
st.markdown("""
---
### Notes:
- Some websites may block automated downloads
- If you get a 403 error, the website might be protecting against automated access
- Make sure you have permission to download content from the website
""")
