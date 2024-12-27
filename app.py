from flask import Flask, render_template, request, send_file
import requests
from bs4 import BeautifulSoup
import os
import zipfile
import urllib.parse
import re

app = Flask(__name__)

def download_assets(url):
    # Create directories for assets
    base_dir = 'downloaded_assets'
    asset_dirs = {
        'images': os.path.join(base_dir, 'images'),
        'css': os.path.join(base_dir, 'css'),
        'js': os.path.join(base_dir, 'js'),
        'html': os.path.join(base_dir, 'html')
    }
    
    # Create directories if they don't exist
    for directory in asset_dirs.values():
        os.makedirs(directory, exist_ok=True)

    # Download main page
    try:
        response = requests.get(url)
        response.raise_for_status()
    except:
        return False

    # Parse HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    base_url = urllib.parse.urljoin(url, '/')

    # Download images
    for img in soup.find_all('img'):
        src = img.get('src')
        if src:
            try:
                img_url = urllib.parse.urljoin(base_url, src)
                img_name = os.path.basename(urllib.parse.urlparse(img_url).path)
                if not img_name:
                    continue
                img_response = requests.get(img_url)
                with open(os.path.join(asset_dirs['images'], img_name), 'wb') as f:
                    f.write(img_response.content)
            except:
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
                css_response = requests.get(css_url)
                with open(os.path.join(asset_dirs['css'], css_name), 'wb') as f:
                    f.write(css_response.content)
            except:
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
                js_response = requests.get(js_url)
                with open(os.path.join(asset_dirs['js'], js_name), 'wb') as f:
                    f.write(js_response.content)
            except:
                continue

    # Save HTML
    with open(os.path.join(asset_dirs['html'], 'index.html'), 'w', encoding='utf-8') as f:
        f.write(response.text)

    # Create ZIP file
    zip_path = 'website_assets.zip'
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, base_dir)
                zipf.write(file_path, arcname)

    return True

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        if download_assets(url):
            return send_file('website_assets.zip', as_attachment=True)
        return "Error downloading assets. Please check the URL and try again."
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
