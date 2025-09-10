import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

def get_date():
    return datetime.today().strftime("%Y-%m-%d")

def get_tempo_links():
    url = f'https://cekfakta.tempo.co/{datetime.now().strftime("%Y/%m")}'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    links_data = []
    
    for article in soup.find_all('article', class_='text-card'):
        date_text = article.find('h4', class_='date')
        if date_text and 'jam' in date_text.get_text():
            a_tag = article.find('a', href=True)
            if a_tag:
                link = "https:" + a_tag['href'] if a_tag['href'].startswith("//") else a_tag['href']
                links_data.append((a_tag.get_text().strip(), link))
    
    return list(set(links_data))

def extract_content(text):
    match = re.search(r"(jakarta -|jakarta-)(.*)", text.lower(), re.DOTALL)
    return match.group(2).strip() if match else text

def scrape_tempo_articles(tempo_links):
    data = []
    date = get_date()
    source = "Tempo"
    
    for title, link in tempo_links:
        category, title_news = title.split(':', 1) if ':' in title else (title, title)
        
        response = requests.get(link)
        soup = BeautifulSoup(response.text, 'html.parser')
        detail_in = soup.find('div', 'detail-in')
        
        if detail_in:
            p = detail_in.find_all('p')
            content = ' '.join(p.get_text() for p in p)
            
            # Process content directly instead of writing to raw file first
            processed_content = extract_content(content)
            
            # Extract image URL
            image = ""
            # Find the first image with "statik.tempo.co" in the URL
            img_tags = detail_in.find_all('img')
            for img in img_tags:
                src = img.get('src', '')
                if "statik.tempo.co" in src:
                    image = src
                    break
            
            data.append({
                'title': title_news,
                'source': source,
                'url': link,
                'image': image,
                'date': date,
                'content': processed_content
            })
    
    return data

def crawl_tempo():
    tempo_links = get_tempo_links()
    return scrape_tempo_articles(tempo_links)

def main(**kwargs):
    return crawl_tempo()

if __name__ == "__main__":
    main()
