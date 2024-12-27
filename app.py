from flask import Flask, render_template, request, send_file
import requests
from bs4 import BeautifulSoup
import urllib.parse
from io import BytesIO
import zipfile

app = Flask(__name__)

def download_assets(url):
    # Create in-memory zip file
    zip_buffer = BytesIO()
    
    try:
        # Download main page
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse HTML
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
                        img_response = requests.get(img_url)
                        zip_file.writestr(f'images/{img_name}', img_response.content)
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
                        zip_file.writestr(f'css/{css_name}', css_response.content)
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
                        zip_file.writestr(f'js/{js_name}', js_response.content)
                    except:
                        continue

        return zip_buffer.getvalue()
    except Exception as e:
        print(f"Error: {e}")
        return None

app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Website Asset Downloader</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            .container {
                text-align: center;
            }
            input[type="text"] {
                width: 80%;
                padding: 10px;
                margin: 10px 0;
            }
            input[type="submit"] {
                padding: 10px 20px;
                background-color: #4CAF50;
                color: white;
                border: none;
                cursor: pointer;
            }
            input[type="submit"]:hover {
                background-color: #45a049;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Website Asset Downloader</h1>
            <form method="POST">
                <input type="text" name="url" placeholder="Enter website URL (e.g., https://example.com)" required>
                <br>
                <input type="submit" value="Download Assets">
            </form>
        </div>
    </body>
    </html>
    '''

@app.route('/', methods=['POST'])
def download():
    url = request.form['url']
    zip_data = download_assets(url)
    
    if zip_data:
        return send_file(
            BytesIO(zip_data),
            mimetype='application/zip',
            as_attachment=True,
            download_name='website_assets.zip'
        )
    return "Error downloading assets. Please check the URL and try again."

if __name__ == '__main__':
    app.run(debug=True)
