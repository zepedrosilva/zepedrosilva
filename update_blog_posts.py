#!/usr/bin/env python3

import feedparser
import re
from datetime import datetime

# Set user agent to avoid Medium blocking - must be set before parsing
feedparser.USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

def convert_medium_url_to_canonical(original_url, canonical_domain="https://blog.zepedro.com"):
    """convert Medium URL to use canonical domain by extracting article ID"""
    # For Medium URLs, extract the article ID (12-character hex string at the end)
    # Format: https://medium.com/@username/title-slug-ARTICLE_ID?source=...
    # We want to extract just the ARTICLE_ID and create: https://blog.zepedro.com/ARTICLE_ID
    medium_article_pattern = r'-([a-f0-9]{12})(?:\?|$)'
    match = re.search(medium_article_pattern, original_url)
    if match:
        article_id = match.group(1)
        return f"{canonical_domain}/{article_id}"

    # fallback: just remove tracking parameters
    return re.sub(r'\?source=.*', '', original_url)

def fetch_medium_posts():
    """fetch posts from Medium RSS feed"""
    # Use direct Medium feed URL
    feed_url = "https://medium.com/@zepedrosilva/feed"

    feed = feedparser.parse(feed_url)
    posts = []

    for entry in feed.entries:
        # parse date
        published_date = 'Unknown'
        if hasattr(entry, 'published'):
            try:
                published_date = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %z').strftime('%Y-%m-%d')
            except ValueError:
                try:
                    published_date = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %Z').strftime('%Y-%m-%d')
                except ValueError:
                    pass

        # convert Medium URL to canonical blog.zepedro.com URL
        canonical_link = convert_medium_url_to_canonical(entry.link)

        posts.append({
            'title': entry.title,
            'link': canonical_link,
            'published': published_date
        })

    return posts

def update_readme(posts):
    """update README.md with latest blog posts"""
    with open('README.md', 'r', encoding='utf-8') as file:
        content = file.read()
    
    # generate markdown list
    blog_section = ""
    for post in posts:
        blog_section += f"* [{post['title']}]({post['link']})\n"
    
    # find placeholder and replace content
    placeholder = "<!-- BLOG_POSTS_PLACEHOLDER - Do not remove this comment -->"
    start_idx = content.find(placeholder)
    
    # find end of section (next ## heading)
    end_pattern = r'\n## '
    end_match = re.search(end_pattern, content[start_idx:])
    end_idx = start_idx + end_match.start() if end_match else len(content)
    
    # replace content
    before_placeholder = content[:start_idx + len(placeholder)]
    after_section = content[end_idx:]
    new_content = f"{before_placeholder}\n\n{blog_section}\n{after_section}"
    
    # write if changed
    if new_content != content:
        with open('README.md', 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f"Updated README.md with {len(posts)} blog posts")
        return True
    else:
        print("No changes needed")
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