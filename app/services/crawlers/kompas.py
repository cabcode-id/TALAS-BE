import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

def extract_article_content(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Url gmbr
        image_url = ""
        photo_wrap = soup.select_one('.photo__wrap')
        if photo_wrap:
            img_tag = photo_wrap.find('img')
            if img_tag and 'src' in img_tag.attrs:
                image_url = img_tag['src']
        
        # Cari element dengan tag p terbanyak
        p_tag_counts = {}
        for elem in soup.find_all():
            p_tags = elem.find_all('p')
            if p_tags:
                p_tag_counts[elem] = len(p_tags)
        
        if not p_tag_counts:
            return "", image_url
        
        content_elem = max(p_tag_counts.items(), key=lambda x: x[1])[0]
        
        # Ekstrak teks dari setiap p tag kecuali yang <strong>
        content_parts = []
        for p in content_elem.find_all('p'):
            for strong in p.find_all('strong'):
                strong.unwrap() 
            
            text = p.get_text(strip=True)
            if text:
                content_parts.append(text)
        
        return ' '.join(content_parts), image_url
        
    except Exception as e:
        print(f"Error extracting content from {url}: {e}")
        return "", ""

def crawl_kompas_news():
    today = datetime.now()
    date_for_url = today.strftime("%Y-%m-%d")  # URL format: 2025-03-14
    date_for_comparison = today.strftime("%Y-%m-%d")  # Database format: 2025-03-14
        
    articles_data = []  #  store dictionaries of article data
    all_articles = []  #  store tuples of (link, title)
    
    # Total halaman yang ada
    url = f"https://indeks.kompas.com/?site=news&date={date_for_url}&page=1"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Cari nomor halaman maksimal ada berapa
        pagination_div = soup.select_one('.paging__wrap')
        if pagination_div:
            page_links = pagination_div.select('.paging__link')
        
        last_page_link = soup.select_one('.paging__link--last')
        
        if not last_page_link:
            page_links = soup.select('.paging__link')
            if page_links:
                page_numbers = []
                for link in page_links:
                    try:
                        page_num = int(link.text.strip())
                        page_numbers.append(page_num)
                    except ValueError:
                        continue
                if page_numbers:
                    last_page = max(page_numbers)
                else:
                    last_page = 1
            else:
                last_page = 1
        else:
            if 'page=' in last_page_link.get('href', ''):
                last_page = int(last_page_link.get('href').split('page=')[-1])
            else:
                last_page = 1
                    
        # iterate through all pages
        for page in range(1, last_page + 1):
            url = f"https://indeks.kompas.com/?site=news&date={date_for_url}&page={page}"
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all article cards/containers
            article_containers = soup.select('.articleListItem')
            
            if not article_containers:
                # Try an alternative selector if the first one doesn't work
                article_containers = soup.select('.article__asset')
            
            if not article_containers:
                # Try another possible class
                article_containers = soup.select('.latest--indeks')
            
            if not article_containers:
                article_containers = soup.select('a[href*="kompas.com/read/"]')
            
            page_articles = []
            
            for container in article_containers:
                article_link = None
                article_title = None
                
                # If the container is already a link
                if container.name == 'a' and container.get('href'):
                    article_link = container.get('href')
                    title_elem = container.select_one('h2') or container.select_one('.article__title') or container
                    article_title = title_elem.get_text(strip=True)
                else:
                    # Find the link within the container
                    link_elem = container.select_one('a[href*="kompas.com/read/"]')
                    if link_elem:
                        article_link = link_elem.get('href')
                        title_elem = container.select_one('h2') or container.select_one('.article__title') or link_elem
                        article_title = title_elem.get_text(strip=True)
                
                if article_link and article_title:
                    page_articles.append((article_link, article_title))
            
            all_articles.extend(page_articles)
            
            # Add a delay between page requests
            time.sleep(5)
            
    except Exception as e:
        print(f"Error occurred while scraping: {e}")
        import traceback
        traceback.print_exc()
    
    
    # Extract content from each article
    for i, (link, title) in enumerate(all_articles, 1):
        content, image_url = extract_article_content(link)
        
        articles_data.append({
            'title': title,
            'link': link,
            'date': date_for_comparison,
            'content': content,
            'image': image_url
        })
        
        # Add a small delay to avoid overloading the server
        time.sleep(1)
    
    # Format data for return
    formatted_data = []
    for i, article in enumerate(articles_data, 1):
        formatted_data.append({
            'id': i,
            'title': article['title'],
            'source': 'Kompas',
            'url': article['link'],
            'image': article['image'],
            'date': article['date'],
            'content': article['content']
        })
    
    return formatted_data

def main(**kwargs):
    return crawl_kompas_news()

if __name__ == "__main__":
    main()
