import datetime
import requests
from bs4 import BeautifulSoup
import time 

# Request headers to mimic a browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

# Tanggal yang mau dimasukkan ke csv
def current_date():
    return datetime.date.today().strftime("%Y-%m-%d")

# URL yang mau discrape
def generate_url():
    formatted_date = datetime.date.today().strftime("%m%%2F%d%%2F%Y")  # MM%2FDD%2FYYYY
    return f"https://news.detik.com/berita/indeks?date={formatted_date}"

# Buat list halaman-halaman yang ada pada tanggal tsb (page 1, page 2, page 3, etc.)
def get_numbered_links(url):
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Cari prev dan next
    prev_next_link = soup.find('a', string=lambda text: text and text.strip().lower() in ["prev", "next"])

    if prev_next_link:
        parent = prev_next_link.find_parent()  # Cari parent dari prev/next
        if parent:
            numbered_links = set() 
            for anchor in parent.find_all('a', href=True):
                text = anchor.text.strip()
                if text.isdigit() and 1 <= int(text) <= 9: # Hanya ambil page 1-9
                    if text.lower() not in ["prev", "next"]:  # Exclude prev and next
                        numbered_links.add(anchor['href'])
            return list(numbered_links)
    return []

# Ambil artikel dari halaman tsb
def get_articles(url):
    response = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(response.content, 'html.parser')

    articles = {}  

    # Cari h3 yang berisi judul artikel
    for h3 in soup.find_all('h3', class_='media__title'):
        a_tag = h3.find('a', class_='media__link', href=True)
        if a_tag:
            title = a_tag.get_text(strip=True) 
            link = a_tag['href']

           
            if link not in articles:
                articles[link] = title

    return articles

def extract_content(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Cari div yang berisi konten artikel
        content_div = soup.find('div', class_='detail__body-text')
        
        # Extract image URL
        image_url = ""
        figure = soup.find('figure', class_='detail__media-image')
        if figure:
            img_tag = figure.find('img')
            if img_tag and 'src' in img_tag.attrs:
                image_url = img_tag['src']
        
        # Extract text content
        if content_div:
            paragraphs = content_div.find_all('p')
            paragraph_text = ' '.join(p.get_text(strip=True) for p in paragraphs)  # Join text without newlines
            return paragraph_text, image_url
        return "", image_url 
    except requests.exceptions.RequestException as e:
        print(f"Error fetching content from {url}: {e}")
        return "", ""

def crawl_detik():
    url = generate_url()
    pagination_links = get_numbered_links(url)
    # Add the main URL to pagination links if it doesn't exist
    if url not in pagination_links:
        pagination_links.append(url)
        
    articles = {}

    for page_link in pagination_links:
        page_articles = get_articles(page_link)
        if page_articles:
            articles.update(page_articles)
    
    processed_data = []
    for link, title in articles.items():
        content, image_url = extract_content(link)
        date = current_date()
        processed_data.append({
            'title': title,
            'source': "Detik",
            'url': link,
            'image': image_url,
            'date': date,
            'content': content
        })
        time.sleep(2)
    
    return processed_data

def main(**kwargs):
    return crawl_detik()

if __name__ == "__main__":
    main()


