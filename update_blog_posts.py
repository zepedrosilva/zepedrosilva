#!/usr/bin/env python3

import os
import re
from datetime import datetime
import feedparser

# Set user agent to avoid Medium blocking - must be set before parsing
feedparser.USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def convert_medium_url_to_canonical(original_url, canonical_domain="https://blog.zepedro.com"):
    """convert Medium URL to use canonical domain by extracting article ID"""
    medium_article_pattern = r'-([a-f0-9]{12})(?:\?|$)'
    match = re.search(medium_article_pattern, original_url)
    if match:
        article_id = match.group(1)
        return f"{canonical_domain}/{article_id}"
    return re.sub(r'\?source=.*', '', original_url)

def fetch_medium_posts():
    """fetch posts from Medium RSS feed"""
    feed_url = "https://medium.com/@zepedrosilva/feed"
    feed = feedparser.parse(feed_url)
    posts = []

    for entry in feed.entries:
        published_date = 'Unknown'
        if hasattr(entry, 'published'):
            for fmt in ('%a, %d %b %Y %H:%M:%S %z', '%a, %d %b %Y %H:%M:%S %Z'):
                try:
                    published_date = datetime.strptime(entry.published, fmt).strftime('%Y-%m-%d')
                    break
                except ValueError:
                    pass

        canonical_link = convert_medium_url_to_canonical(entry.link)
        posts.append({
            'title': entry.title,
            'link': canonical_link,
            'published': published_date
        })

    return posts

def load_curated_config(config_path="curated.yaml"):
    """load curated tracks config if present"""
    if not os.path.exists(config_path):
        return None
    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Warning: Could not parse {config_path}: {e}")
        return None

def generate_curated_markdown(curated_data, base_url="https://blog.zepedro.com"):
    """generate markdown for curated tracks from config"""
    tracks = curated_data.get('tracks', [])
    md = ""
    for track in tracks:
        icon = f"{track['icon']} " if track.get('icon') else ""
        md += f"#### {icon}{track['name']}\n"
        for art in track.get('articles', []):
            art_id = art['id']
            url = f"{base_url}/{art_id}" if not art_id.startswith('http') else art_id
            meta_suffix = f" — *{art['meta']}*" if art.get('meta') else ""
            md += f"* [{art['title']}]({url}){meta_suffix}\n"
        md += "\n"
    return md.rstrip()

def update_readme(posts):
    """update README.md with curated tracks and latest blog posts"""
    with open('README.md', 'r', encoding='utf-8') as file:
        content = file.read()
    
    new_content = content

    # update curated tracks if curated.yaml exists
    curated_data = load_curated_config()
    if curated_data:
        curated_start = "<!-- CURATED_THEMES_PLACEHOLDER - Do not remove this comment -->"
        curated_end = "<!-- /CURATED_THEMES_PLACEHOLDER -->"
        if curated_start in new_content and curated_end in new_content:
            curated_md = generate_curated_markdown(curated_data)
            new_content = re.sub(
                re.escape(curated_start) + r'.*?' + re.escape(curated_end),
                f"{curated_start}\n\n{curated_md}\n\n{curated_end}",
                new_content,
                flags=re.DOTALL
            )

    # generate markdown list for latest posts
    blog_section = ""
    for post in posts:
        blog_section += f"* [{post['title']}]({post['link']})\n"
    
    placeholder = "<!-- BLOG_POSTS_PLACEHOLDER - Do not remove this comment -->"
    start_idx = new_content.find(placeholder)
    
    if start_idx != -1:
        end_pattern = r'\n## '
        end_match = re.search(end_pattern, new_content[start_idx:])
        end_idx = start_idx + end_match.start() if end_match else len(new_content)
        
        before_placeholder = new_content[:start_idx + len(placeholder)]
        after_section = new_content[end_idx:]
        new_content = f"{before_placeholder}\n\n{blog_section}\n{after_section}"
    
    if new_content != content:
        with open('README.md', 'w', encoding='utf-8') as file:
            file.write(new_content)
        print("Updated README.md with curated tracks and latest blog posts")
        return True
    else:
        print("No changes needed in README.md")
        return False

def main():
    try:
        posts = fetch_medium_posts()
        print(f"Fetched {len(posts)} posts from Medium")
        
        if posts:
            update_readme(posts)
        else:
            print("No posts found")
            
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    main()