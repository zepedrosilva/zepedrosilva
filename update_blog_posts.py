#!/usr/bin/env python3

import feedparser
import re
import urllib.request
from datetime import datetime

def fetch_medium_posts():
    """fetch posts from Medium RSS feed"""
    feed_url = "https://blog.zepedro.com/feed"
    
    # create request with user agent to avoid blocking
    req = urllib.request.Request(
        feed_url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    )
    
    with urllib.request.urlopen(req) as response:
        feed_data = response.read()
    
    feed = feedparser.parse(feed_data)
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
        
        # clean up Medium URL - remove tracking parameters
        clean_link = re.sub(r'\?source=.*', '', entry.link)
        
        posts.append({
            'title': entry.title,
            'link': clean_link,
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