import os
import subprocess
import re
import shutil
from bs4 import BeautifulSoup

def generate_website():
    print("Starting website generation process...")
    md_folder = 'md'
    build_folder = 'build'
    posts_md_folder = os.path.join(md_folder, 'posts')
    posts_build_folder = os.path.join(build_folder, 'posts')
    index_md_path = os.path.join(md_folder, '_', 'index.md')
    index_html_path = os.path.join(build_folder, 'index.html')
    
    # Source CSS path and destination path
    css_source_path = 'css/github.css'
    css_build_path = os.path.join(build_folder, 'css', 'style.css')
    
    # Ensure build folders exist
    if not os.path.exists(build_folder):
        print(f"Creating output directory: {build_folder}")
        os.makedirs(build_folder)
    
    if not os.path.exists(posts_build_folder):
        print(f"Creating posts output directory: {posts_build_folder}")
        os.makedirs(posts_build_folder)
    
    # Copy CSS file to build directory
    print(f"Copying CSS file: {css_source_path} -> {css_build_path}")
    os.makedirs(os.path.dirname(css_build_path), exist_ok=True)
    shutil.copy(css_source_path, css_build_path)
    
    # Create index.html first using pandoc
    if os.path.exists(index_md_path):
        print(f"Processing index file: {index_md_path} -> {index_html_path}")
        # For index.html, CSS is in the same directory
        subprocess.run(['pandoc', '-s', index_md_path, '-o', index_html_path, '--css', 'css/style.css'])
        print("Index file created successfully")
        
        # Read the generated index.html
        print("Reading generated index.html...")
        with open(index_html_path, 'r', encoding='utf-8') as index_html:
            html_content = index_html.read()
        
        # Create dark mode toggle HTML and JavaScript
        dark_mode_toggle = """
<div class="theme-switch-wrapper">
    <label class="theme-switch" for="checkbox">
        <input type="checkbox" id="checkbox" />
        <div class="slider round"></div>
    </label>
    <em>Toggle Dark Mode</em>
</div>

<style>
.theme-switch-wrapper {
  display: flex;
  align-items: center;
  margin: 20px 0;
}
.theme-switch {
  display: inline-block;
  height: 34px;
  position: relative;
  width: 60px;
}
.theme-switch input {
  display: none;
}
.slider {
  background-color: #ccc;
  bottom: 0;
  cursor: pointer;
  left: 0;
  position: absolute;
  right: 0;
  top: 0;
  transition: .4s;
}
.slider:before {
  background-color: #fff;
  bottom: 4px;
  content: "";
  height: 26px;
  left: 4px;
  position: absolute;
  transition: .4s;
  width: 26px;
}
input:checked + .slider {
  background-color: #66bb6a;
}
input:checked + .slider:before {
  transform: translateX(26px);
}
.slider.round {
  border-radius: 34px;
}
.slider.round:before {
  border-radius: 50%;
}
em {
  margin-left: 10px;
  font-size: 1rem;
}

/* Dark mode styles */
body.dark-mode {
  background-color: #1a1a1a;
  color: #e6e6e6;
}
body.dark-mode a {
  color: #3391ff;
}
body.dark-mode .markdown-body {
  color: #e6e6e6;
  background-color: #1a1a1a;
}
body.dark-mode .markdown-body blockquote {
  color: #bebebe;
  border-left-color: #444;
}
body.dark-mode .markdown-body h1,
body.dark-mode .markdown-body h2,
body.dark-mode .markdown-body h3,
body.dark-mode .markdown-body h4,
body.dark-mode .markdown-body h5,
body.dark-mode .markdown-body h6 {
  color: #e6e6e6;
  border-bottom-color: #444;
}
body.dark-mode .markdown-body hr {
  background-color: #444;
}
body.dark-mode .markdown-body table tr {
  background-color: #1a1a1a;
  border-top-color: #444;
}
body.dark-mode .markdown-body table tr:nth-child(2n) {
  background-color: #222;
}
body.dark-mode .markdown-body table td,
body.dark-mode .markdown-body table th {
  border-color: #444;
}
body.dark-mode .markdown-body code {
  background-color: #222;
  color: #e6e6e6;
}
body.dark-mode .markdown-body pre {
  background-color: #222;
  border-color: #444;
}
</style>

<script>
const toggleSwitch = document.querySelector('.theme-switch input[type="checkbox"]');

function switchTheme(e) {
    if (e.target.checked) {
        document.documentElement.setAttribute('data-theme', 'dark');
        document.body.classList.add('dark-mode');
        localStorage.setItem('theme', 'dark');
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
        document.body.classList.remove('dark-mode');
        localStorage.setItem('theme', 'light');
    }    
}

toggleSwitch.addEventListener('change', switchTheme, false);

// Check for saved user preference, if any, on load
const currentTheme = localStorage.getItem('theme') ? localStorage.getItem('theme') : null;
if (currentTheme) {
    document.documentElement.setAttribute('data-theme', currentTheme);

    if (currentTheme === 'dark') {
        toggleSwitch.checked = true;
        document.body.classList.add('dark-mode');
    }
}
</script>
"""
        
        # Check if the {dark_mode} marker exists in the HTML
        if '{dark_mode}' in html_content:
            print("Found {dark_mode} marker in the HTML")
            # Replace the marker with the dark mode toggle
            html_content = html_content.replace('{dark_mode}', dark_mode_toggle)
        
        # Check if the {latest_posts} marker exists in the HTML
        if '{latest_posts}' in html_content:
            print("Found {latest_posts} marker in the HTML")
            
            # Check if posts directory exists
            if os.path.exists(posts_md_folder):
                print(f"Reading posts from: {posts_md_folder}")
                # Generate a list of posts with their modification times
                posts_info = []
                posts_html = ""
                # Create posts_ul with a fallback method
                posts_ul = soup.new_tag('ul') if 'soup' in locals() else BeautifulSoup('', 'html.parser').new_tag('ul')
                
                for md_file in os.listdir(posts_md_folder):
                    if md_file.endswith('.md'):
                        full_path = os.path.join(posts_md_folder, md_file)
                        # Get last modified time
                        mod_time = os.path.getmtime(full_path)
                        
                        post_title = md_file.replace('.md', '').replace('_', ' ').title()
                        post_html_path = f"posts/{md_file.replace('.md', '.html')}"
                        
                        posts_info.append({
                            'title': post_title,
                            'path': post_html_path,
                            'mod_time': mod_time
                        })
                
                # Sort posts by modification time in descending order (most recent first)
                posts_info.sort(key=lambda x: x['mod_time'], reverse=True)
                
                # Generate sorted post links
                for post in posts_info:
                    # Generate HTML string for posts_html
                    posts_html += f'  <li><a href="{post["path"]}" target="_blank">{post["title"]}</a></li>\n'
                    
                    # Use html.parser to create elements if soup is not defined
                    li_tag = soup.new_tag('li') if 'soup' in locals() else BeautifulSoup('', 'html.parser').new_tag('li')
                    a_tag = soup.new_tag('a', href=post['path']) if 'soup' in locals() else BeautifulSoup('', 'html.parser').new_tag('a', href=post['path'])
                    a_tag.string = post['title']
                    # Add target="_blank" to open in new window
                    a_tag['target'] = '_blank'
                    li_tag.append(a_tag)
                    posts_ul.append(li_tag)
                    
                    print(f"Added link to post: {post['title']}")
                
                # Wrap posts_html in <ul> tags
                posts_html = f"<ul>\n{posts_html}</ul>"
            else:
                print(f"Warning: Posts directory not found at {posts_md_folder}")
                posts_html = "<p>No posts found.</p>"
                # Create an empty ul for consistency
                posts_ul = soup.new_tag('ul') if 'soup' in locals() else BeautifulSoup('', 'html.parser').new_tag('ul')
            
            # Create posts list div
            posts_list = soup.new_tag('div') if 'soup' in locals() else BeautifulSoup('', 'html.parser').new_tag('div')
            posts_list['class'] = 'posts-list'
            
            # Add heading
            posts_heading = soup.new_tag('h2') if 'soup' in locals() else BeautifulSoup('', 'html.parser').new_tag('h2')
            posts_heading.string = 'Latest Posts'
            posts_list.append(posts_heading)
            
            # Append the posts list
            posts_list.append(posts_ul)
            
            # Replace the marker with the generated posts list
            html_content = html_content.replace('{latest_posts}', posts_html)
            
            # Write the modified HTML back to index.html
            with open(index_html_path, 'w', encoding='utf-8') as index_file:
                index_file.write(html_content)
            print("Index file updated with post list and dark mode toggle")
        else:
            # If no markers found, use BeautifulSoup to modify the HTML
            print("Warning: Markers not found in the HTML. Using BeautifulSoup to modify the content.")
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Add dark mode toggle
            dark_mode_div = BeautifulSoup(dark_mode_toggle, 'html.parser')
            
            # Create posts list HTML
            posts_list = soup.new_tag('div')
            posts_list['class'] = 'posts-list'
            
            posts_heading = soup.new_tag('h2')
            posts_heading.string = 'Latest Posts'
            posts_list.append(posts_heading)
            
            # Create posts_ul with a fallback method
            posts_ul = soup.new_tag('ul') if 'soup' in locals() else BeautifulSoup('', 'html.parser').new_tag('ul')
            
            # Check if posts directory exists
            if os.path.exists(posts_md_folder):
                print(f"Reading posts from: {posts_md_folder}")
                # Generate a list of posts with their modification times
                posts_info = []
                for md_file in os.listdir(posts_md_folder):
                    if md_file.endswith('.md'):
                        full_path = os.path.join(posts_md_folder, md_file)
                        # Get last modified time
                        mod_time = os.path.getmtime(full_path)
                        
                        post_title = md_file.replace('.md', '').replace('_', ' ').title()
                        post_html_path = f"posts/{md_file.replace('.md', '.html')}"
                        
                        posts_info.append({
                            'title': post_title,
                            'path': post_html_path,
                            'mod_time': mod_time
                        })
                
                # Sort posts by modification time in descending order (most recent first)
                posts_info.sort(key=lambda x: x['mod_time'], reverse=True)
                
                # Generate sorted post links
                for post in posts_info:
                    # Use html.parser to create elements if soup is not defined
                    li_tag = soup.new_tag('li') if 'soup' in locals() else BeautifulSoup('', 'html.parser').new_tag('li')
                    a_tag = soup.new_tag('a', href=post['path']) if 'soup' in locals() else BeautifulSoup('', 'html.parser').new_tag('a', href=post['path'])
                    a_tag.string = post['title']
                    # Add target="_blank" to open in new window
                    a_tag['target'] = '_blank'
                    li_tag.append(a_tag)
                    posts_ul.append(li_tag)
                    
                    print(f"Added link to post: {post['title']}")
            else:
                print(f"Warning: Posts directory not found at {posts_md_folder}")
            
            posts_list.append(posts_ul)
            
            # Find the main content area (usually body or main tag)
            main_content = soup.body
            if main_content:
                # Insert dark mode toggle at the beginning of the body
                for element in reversed(list(dark_mode_div.children)):
                    main_content.insert(0, element)
                
                main_content.append(posts_list)
            
            # Write the modified HTML back to index.html
            with open(index_html_path, 'w', encoding='utf-8') as index_file:
                index_file.write(str(soup))
            print("Index file updated with post list and dark mode toggle (appended to body)")
    else:
        print(f"Warning: Index file not found at {index_md_path}")

    # Create HTML from each Markdown file in posts directory
    if os.path.exists(posts_md_folder):
        print("\nProcessing individual markdown files...")
        for md_file in os.listdir(posts_md_folder):
            if md_file.endswith('.md'):
                md_path = os.path.join(posts_md_folder, md_file)
                html_path = os.path.join(posts_build_folder, md_file.replace('.md', '.html'))
                print(f"Converting: {md_path} -> {html_path}")
                # For post HTML files, CSS is one directory up
                subprocess.run(['pandoc', '-s', md_path, '-o', html_path, '--css', '../css/style.css'])
                
                # Add dark mode toggle and styles to each post
                print(f"Adding dark mode toggle to {html_path}")
                with open(html_path, 'r', encoding='utf-8') as html_file:
                    post_html = html_file.read()
                
                # Parse the HTML
                soup = BeautifulSoup(post_html, 'html.parser')
                
                # Dark mode toggle HTML (same as in index generation)
                dark_mode_toggle = """
<div class="theme-switch-wrapper">
    <label class="theme-switch" for="checkbox">
        <input type="checkbox" id="checkbox" />
        <div class="slider round"></div>
    </label>
    <em>Toggle Dark Mode</em>
</div>

<style>
.theme-switch-wrapper {
  display: flex;
  align-items: center;
  margin: 20px 0;
}
.theme-switch {
  display: inline-block;
  height: 34px;
  position: relative;
  width: 60px;
}
.theme-switch input {
  display: none;
}
.slider {
  background-color: #ccc;
  bottom: 0;
  cursor: pointer;
  left: 0;
  position: absolute;
  right: 0;
  top: 0;
  transition: .4s;
}
.slider:before {
  background-color: #fff;
  bottom: 4px;
  content: "";
  height: 26px;
  left: 4px;
  position: absolute;
  transition: .4s;
  width: 26px;
}
input:checked + .slider {
  background-color: #66bb6a;
}
input:checked + .slider:before {
  transform: translateX(26px);
}
.slider.round {
  border-radius: 34px;
}
.slider.round:before {
  border-radius: 50%;
}
em {
  margin-left: 10px;
  font-size: 1rem;
}

/* Dark mode styles */
body.dark-mode {
  background-color: #1a1a1a;
  color: #e6e6e6;
}
body.dark-mode a {
  color: #3391ff;
}
body.dark-mode .markdown-body {
  color: #e6e6e6;
  background-color: #1a1a1a;
}
body.dark-mode .markdown-body blockquote {
  color: #bebebe;
  border-left-color: #444;
}
body.dark-mode .markdown-body h1,
body.dark-mode .markdown-body h2,
body.dark-mode .markdown-body h3,
body.dark-mode .markdown-body h4,
body.dark-mode .markdown-body h5,
body.dark-mode .markdown-body h6 {
  color: #e6e6e6;
  border-bottom-color: #444;
}
body.dark-mode .markdown-body hr {
  background-color: #444;
}
body.dark-mode .markdown-body table tr {
  background-color: #1a1a1a;
  border-top-color: #444;
}
body.dark-mode .markdown-body table tr:nth-child(2n) {
  background-color: #222;
}
body.dark-mode .markdown-body table td,
body.dark-mode .markdown-body table th {
  border-color: #444;
}
body.dark-mode .markdown-body code {
  background-color: #222;
  color: #e6e6e6;
}
body.dark-mode .markdown-body pre {
  background-color: #222;
  border-color: #444;
}
</style>

<script>
const toggleSwitch = document.querySelector('.theme-switch input[type="checkbox"]');

function switchTheme(e) {
    if (e.target.checked) {
        document.documentElement.setAttribute('data-theme', 'dark');
        document.body.classList.add('dark-mode');
        localStorage.setItem('theme', 'dark');
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
        document.body.classList.remove('dark-mode');
        localStorage.setItem('theme', 'light');
    }    
}

toggleSwitch.addEventListener('change', switchTheme, false);

// Check for saved user preference, if any, on load
const currentTheme = localStorage.getItem('theme') ? localStorage.getItem('theme') : null;
if (currentTheme) {
    document.documentElement.setAttribute('data-theme', currentTheme);

    if (currentTheme === 'dark') {
        toggleSwitch.checked = true;
        document.body.classList.add('dark-mode');
    }
}
</script>
"""
                
                # Create the "Go back" link using direct link to index
                back_link_div = soup.new_tag('div')
                back_link_div['class'] = 'back-link'
                back_link_div['style'] = 'margin: 20px 0; font-size: 16px;'
                
                back_link = soup.new_tag('a')
                back_link['href'] = '../index.html'  # Always go to index.html
                back_link.string = '← Back to Home'
                
                # Ensure it doesn't open in a new window
                if 'target' in back_link.attrs:
                    del back_link['target']
                
                back_link_div.append(back_link)
                
                # Find the body tag and insert the back link and dark mode toggle at the beginning
                body_tag = soup.body
                if body_tag:
                    # Parse dark mode toggle HTML
                    dark_mode_soup = BeautifulSoup(dark_mode_toggle, 'html.parser')
                    
                    # Insert dark mode toggle elements at the beginning of the body
                    for element in reversed(list(dark_mode_soup.children)):
                        body_tag.insert(0, element)
                    
                    # Insert back link
                    body_tag.insert(0, back_link_div)
                    
                    # Add target="_blank" to all links
                    for link in soup.find_all('a'):
                        # Skip internal links and already modified links
                        if 'target' not in link.attrs:
                            # Only add target="_blank" if it's not the back link
                            if link.get('href') != '../index.html':
                                link['target'] = '_blank'
                    
                    # Write the modified HTML back to the file
                    with open(html_path, 'w', encoding='utf-8') as html_file:
                        html_file.write(str(soup))
                    print(f"Added dark mode toggle, 'Back' link, and new window links to {html_path}")
                else:
                    print(f"Warning: Could not find body tag in {html_path}")
    else:
        print(f"Warning: Posts directory not found at {posts_md_folder}")
    
    print("\nWebsite generation completed successfully!")

generate_website()
