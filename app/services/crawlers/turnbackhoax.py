import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"
}

def get_soup(url):
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return BeautifulSoup(response.content, 'html.parser')

def process_title(title):
    is_fake = 0
    clean_title = title.strip()
    
    if "[PENIPUAN]" in clean_title:
        is_fake = 1
        clean_title = clean_title.replace("[PENIPUAN]", "").strip()
    elif "[SALAH]" in clean_title:
        is_fake = 1
        clean_title = clean_title.replace("[SALAH]", "").strip()
        
    return clean_title, is_fake

def parse_article(article_url):
    try:
        soup = get_soup(article_url)
        
        # Extract image URL from figure class="entry-thumbnail"
        image_url = ""
        figure = soup.find('figure', class_='entry-thumbnail')
        if figure and figure.find('img'):
            image_url = figure.find('img').get('src', '')
        
        content_div = soup.find(class_="entry-content mh-clearfix")
        if content_div:
            # Ambil semua teks dari paragraf, item daftar, blockquote
            content_elements = content_div.find_all(['p', 'li', 'blockquote'])
            # Gabungkan semua konten dan hapus baris baru
            content = " ".join(element.get_text().strip() for element in content_elements)
            content = re.sub(r'\s+', ' ', content)
        else:
            content = "No content found"
            
        return {
            "content": content,
            "image": image_url
        }
    except Exception as e:
        print(f"Error parsing article {article_url}: {e}")
        return {
            "content": f"Failed to parse: {str(e)}",
            "image": ""
        }

def get_todays_news_links(url):
    today = datetime.today()
    today_string = today.strftime("%Y/%m/%d")
    
    soup = get_soup(url)
    news_links = []
    seen_urls = set() 
    
    main_content = soup.find('div', id='main-content')
    if not main_content:
        print("Warning: Could not find main-content div")
        return news_links
    
    # Temukan semua tag anchor dalam main-content
    for anchor in main_content.find_all('a', href=True):
        link = anchor.get('href')
        
        # Lewati yang mengandung #mh-comments
        if "/#mh-comments" in link:
            continue
            
        # Periksa apakah url tanggal hari ini dalam format yang diharapkan
        if today_string in link and link not in seen_urls:
            title = anchor.get_text().strip()
            if title:  # Hanya tambahkan jika judul tidak kosong
                clean_title, is_fake = process_title(title)
                news_links.append({
                    "title": clean_title,
                    "link": link,
                    "is_fake": is_fake
                })
                seen_urls.add(link)
    
    return news_links

def crawl_turnbackhoax():
    base_url = "https://turnbackhoax.id/"
    source = "TurnBackHoax"
    
    # Tetapkan tanggal hari ini untuk semua entri
    today_date = datetime.today().strftime("%Y-%m-%d")
    
    today_news = get_todays_news_links(base_url)
    
    print(f"Found {len(today_news)} news articles from today. Extracting full content...")
    
    # Ekstrak konten untuk setiap artikel
    articles_data = []
    for i, article in enumerate(today_news):
        print(f"Processing article {i+1}/{len(today_news)}: {article['title']}")
        details = parse_article(article['link'])
        
        articles_data.append({
            "title": article['title'],
            "source": source,
            "url": article['link'],
            "image": details["image"],
            "date": today_date, 
            "content": details["content"]
        })
        time.sleep(1)
    
    return articles_data

def main(**kwargs):
    return crawl_turnbackhoax()

if __name__ == "__main__":
    main()
