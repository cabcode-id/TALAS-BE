import csv
import requests
import re
import time
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

# Tanggal yang dimasukkan ke csv. 
def get_raw_date():
    return datetime.today().strftime("%Y-%m-%d")

# Membuat dictionary berisi judul dan link yang dibuat beberapa jam lalu atau kemarin. 
def find_links(url):
    print(f"Crawling URL: {url}")
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    divs = soup.find_all('div', class_='col-md-8')

    span_elements = []

    # G pake range waktu dulu
    # # Mengambil waktu saat ini dalam zona waktu Jakarta (GMT+7)
    # current_hour = datetime.now(timezone(timedelta(hours=7))).hour
    # # Menghitung jam yang sudah berlalu dari jam saat ini untuk crawl dari awal hari ini.
    # hour_patterns = [f"\\b{i} jam lalu\\b" for i in range(1, current_hour + 1)]
    # minute_pattern = "\\b\\d+ menit lalu\\b"
    # time_pattern = f"{minute_pattern}|{('|'.join(hour_patterns))}"

    for div in divs:
        # spans = div.find_all('span', string=re.compile(time_pattern, re.IGNORECASE))
        spans = div.find_all('span')
        span_elements.extend(spans)

    links_dict = {}
    for span in span_elements:
        parent = span.find_parent()
        
        # Check if this span is related to content we want to filter out
        should_skip = False
        checking_element = span
        for _ in range(5):  # Check up to 5 levels up to find slugs
            if not checking_element:
                break
                
            # Check if there's a slug element 
            slug_element = checking_element.find_previous('h4', class_='slug')
            if slug_element:
                slug_link = slug_element.find('a')
                if slug_link and 'video' in slug_link.text.lower():
                    should_skip = True
                    break
            
            checking_element = checking_element.parent
        
        if should_skip:
            continue
            
        while parent:
            link = parent.find('a', href=True)
            if link:
                # Skip link yang ada slug.
                if link.find_parent('h4', class_='slug'):
                    break
                    
                title = link.get('title', '')
                if title:  # Only add non-empty titles
                    links_dict[title] = link['href']
                break
            parent = parent.find_parent()
    return links_dict

# Mengumpulkan artikel dari link yang ditemukan.
def collect_articles(links_dict):
    data = []
    raw_date = get_raw_date()
    source = "Antara Sanur"
    for title, link in links_dict.items():
        try:
            get_content = requests.get(link, timeout=10)
            get_content.raise_for_status()
            date = raw_date
            content, image_url = find_content(link)
            # Process content directly
            processed_content = extract_content(content)
            data.append([title, source, link, image_url, date, processed_content])
        except requests.exceptions.RequestException as e:
            print(f"Error fetching content for {link}: {e}")
        time.sleep(2)
    return data

# Mencari konten dari link berita.
def find_content(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find the image with the largest area instead of by class
    image_url = ""
    max_area = 0
    for img in soup.find_all('img'):
        # Skip small icons, emoticons etc
        if not img.has_attr('src') or img['src'].startswith('data:'):
            continue
            
        # Get width and height attributes
        width_str = img.get('width', '0')
        height_str = img.get('height', '0')
        
        # Remove 'px' suffix if present
        width_str = width_str.replace('px', '') if isinstance(width_str, str) else width_str
        height_str = height_str.replace('px', '') if isinstance(height_str, str) else height_str
        
        try:
            width = int(width_str) or int(re.search(r'width:\s*(\d+)px', img.get('style', '') or '') or [0, 0])[1]
            height = int(height_str) or int(re.search(r'height:\s*(\d+)px', img.get('style', '') or '') or [0, 0])[1]
        except (ValueError, TypeError):
            width, height = 0, 0
        
        # Calculate area
        area = width * height
        
        # Update max area and image URL if this image is larger
        if area > max_area:
            max_area = area
            image_url = img['src']
    
    # If no area detected images, fallback to traditional method
    if not image_url:
        image_div = soup.find('div', class_='wrap__article-detail-image mt-4')
        if image_div:
            img_tag = image_div.find('img', class_='img-fluid')
            if img_tag and img_tag.has_attr('src'):
                image_url = img_tag['src']
    
    parent_p_count = {}
    # Mencari semua parent yang memiliki p. Jumlah p yang tertinggi = main content yang ingin diambil.
    for p in soup.find_all('p'):
        # Skip paragraphs that have any class attribute
        if p.has_attr('class'):
            continue
        # Skip paragraphs that contain a span with class 'baca-juga'
        if p.find('span', class_='baca-juga'):
            continue

        parent = p.find_parent()
        if parent:
            parent_p_count[parent] = parent_p_count.get(parent, 0) + 1

    content_text = ""
    if parent_p_count:
        max_parent = max(parent_p_count, key=parent_p_count.get)
        paragraphs = []
        for p in max_parent.find_all('p'):
            if p.has_attr('class'):
                continue
            if p.find('span', class_='baca-juga'):
                continue
            text = p.get_text(" ", strip=True)
            paragraphs.append(text)
        content_text = " ".join(paragraphs)
    
    return content_text, image_url

def extract_content(text):
    text = text.lower()
    start_phrases = ["jakarta (antara) - "]
    start_pattern = "|".join(map(re.escape, start_phrases))
    pattern = f"({start_pattern})(.*)"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(2).strip() if match else text

def crawl_antara():
    all_links = {}
    page = 1
    max_pages = 10  # Set a reasonable maximum to avoid infinite crawling
    consecutive_empty_pages = 0
    
    while page <= max_pages:
        url = f'https://www.antaranews.com/tag/pantai-sanur-bali/{page}'
        try:
            links_dict = find_links(url)
            
            # If no articles found or we got an empty dictionary
            if not links_dict:
                consecutive_empty_pages += 1
                print(f"No articles found on page {page}")
                
                # Stop after 2 consecutive empty pages
                if consecutive_empty_pages >= 2:
                    print("Reached end of articles, stopping crawler")
                    break
            else:
                consecutive_empty_pages = 0  # Reset counter when we find articles
                all_links.update(links_dict)
                print(f"Found {len(links_dict)} articles on page {page}")
                
                # Print each article title and link
                for title, link in links_dict.items():
                    print(f"  - {title}: {link}")
            
            page += 1
        except requests.exceptions.RequestException as e:
            print(f"Error accessing page {page}: {e}")
            break
    
    # Process all collected links
    data = collect_articles(all_links)
    
    # Format data for return
    formatted_data = []
    for row in data:
        formatted_data.append({
            'title': row[0],
            'source': row[1],
            'url': row[2],
            'image': row[3],
            'date': row[4],
            'content': row[5]
        })
    
    return formatted_data

def main(**kwargs):
    return crawl_antara()

if __name__ == "__main__":
    articles = main()
    titles = [article['title'] for article in articles]
    print(titles)


