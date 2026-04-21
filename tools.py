import os
import re
import shutil
import requests
import datetime
from bs4 import BeautifulSoup
from docling.document_converter import DocumentConverter

# --- SECURITY LAYER ---

def is_safe_path(target_path: str) -> bool:
    """Ensures the target path is within the current working directory."""
    base_dir = os.path.realpath(os.getcwd())
    try:
        target_dir = os.path.realpath(target_path)
        return os.path.commonpath([base_dir, target_dir]) == base_dir
    except ValueError:
        return False

# --- CORE TOOLS ---

def read_document(path: str) -> str:
    """
    Unified reader. 
    If path is a PDF, uses docling to convert to Markdown.
    Otherwise, reads as standard text.
    """
    if not is_safe_path(path):
        return f"Error: Security Violation. Access to '{path}' is denied."
    
    if not os.path.exists(path):
        return f"Error: File '{path}' not found."

    try:
        ext = os.path.splitext(path)[1].lower()
        
        if ext == ".pdf":
            # Use docling for complex PDF parsing
            converter = DocumentConverter()
            return converter.convert(path).document.export_to_markdown()
        else:
            # Standard text/markdown reading
            with open(path, 'r', encoding='utf-8') as file:
                return file.read()
    except Exception as e:
        return f"Error processing document: {str(e)}"

def write_file(path: str, content: str) -> str:
    if not is_safe_path(path):
        return "Error: Security Violation."
    
    # Consistency Check for wiki folder
    if "wiki/" in path and not content.strip().startswith("---"):
        return "Error: Wiki files must start with YAML frontmatter delimiter (---)."

    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as file:
            file.write(content)
        # Every write triggers a log update and index refresh automatically
        rebuild_wiki_index("wiki/index.md", "wiki")
        return f"Success: {path} saved and Index updated."
    except Exception as e:
        return f"Error: {str(e)}"

def handle_media_ingest(source_path: str, target_dir: str) -> str:
    """New tool to move non-text assets (images/audio) into the wiki structure."""
    if not is_safe_path(source_path) or not is_safe_path(target_dir):
        return "Error: Security Violation."
    
    try:
        os.makedirs(target_dir, exist_ok=True)
        filename = os.path.basename(source_path)
        dest_path = os.path.join(target_dir, filename)
        shutil.copy2(source_path, dest_path)
        return f"Success: Media saved to {dest_path}"
    except Exception as e:
        return f"Error: {str(e)}"

def append_to_file(path: str, content: str) -> str:
    """Safely appends content to a file (useful for log.md and index.md)."""
    if not is_safe_path(path):
        return "Error: Security Violation."
    try:
        with open(path, 'a', encoding='utf-8') as file:
            file.write(f"\n{content}" if os.path.getsize(path) > 0 else content)
        return f"Success: Content appended to {path}."
    except Exception as e:
        return f"Error: {str(e)}"

def search_wiki(query: str, root_dir: str = "wiki") -> str:
    """Searches for a keyword or regex across all markdown files in the wiki."""
    if not is_safe_path(root_dir):
        return "Error: Security Violation."
    
    results = []
    try:
        for root, _, files in os.walk(root_dir):
            for file in files:
                if file.endswith(".md"):
                    path = os.path.join(root, file)
                    with open(path, 'r', encoding='utf-8') as f:
                        if query.lower() in f.read().lower():
                            results.append(path)
        return f"Found '{query}' in: " + ", ".join(results) if results else "No matches found."
    except Exception as e:
        return f"Error during search: {str(e)}"

def get_file_metadata(path: str) -> str:
    """Extracts YAML frontmatter from a wiki page."""
    if not is_safe_path(path):
        return "Error: Security Violation."
    try:
        # Using the unified reader
        content = read_document(path)
        match = re.search(r'^---\s*(.*?)\s*---', content, re.DOTALL)
        if match:
            return match.group(1)
        return "No metadata found."
    except Exception as e:
        return f"Error reading metadata: {str(e)}"

def list_directory(path: str) -> str:
    if not is_safe_path(path):
        return "Error: Security Violation."
    try:
        entries = os.listdir(path)
        return "\n".join([f"{'[DIR]' if os.path.isdir(os.path.join(path, e)) else '[FILE]'} {e}" for e in sorted(entries)])
    except Exception as e:
        return f"Error: {str(e)}"

def web_scrape(url: str) -> str:
    """Scrapes a URL and returns a simplified Markdown version of the text content."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for script in soup(["script", "style"]):
            script.decompose()

        title = soup.title.string if soup.title else "No Title"
        paragraphs = [p.get_text() for p in soup.find_all('p')]
        content = f"# {title}\n\nSource: {url}\n\n" + "\n\n".join(paragraphs)
        return content
    except Exception as e:
        return f"Error scraping URL: {str(e)}"

def check_broken_links(root_dir: str = "wiki") -> str:
    """Scans all markdown files in the wiki for broken internal [[links]] or [links](path)."""
    if not is_safe_path(root_dir):
        return "Error: Security Violation."
    
    broken_links = []
    link_pattern = re.compile(r'\[\[(.*?)\]\]|\[.*?\]\((.*?\.md)\)')

    try:
        for root, _, files in os.walk(root_dir):
            for file in files:
                if file.endswith(".md"):
                    path = os.path.join(root, file)
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        matches = link_pattern.findall(content)
                        for match in matches:
                            link_target = match[0] if match[0] else match[1]
                            if not link_target: continue
                            
                            target_path = os.path.join(root, link_target)
                            if not os.path.exists(target_path):
                               broken_links.append(f"Broken link in {path}: '{link_target}'")
        
        return "\n".join(broken_links) if broken_links else "No broken links found."
    except Exception as e:
        return f"Error during linting: {str(e)}"

def find_orphan_pages(root_dir: str = "wiki") -> str:
    """Identifies markdown files that are not referenced by any other file in the wiki."""
    try:
        all_files = []
        all_links = set()
        link_pattern = re.compile(r'\[\[(.*?)\]\]|\[.*?\]\((.*?\.md)\)')

        for root, _, files in os.walk(root_dir):
            for file in files:
                if file.endswith(".md"):
                    full_path = os.path.join(root, file)
                    all_files.append(full_path)
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        matches = link_pattern.findall(content)
                        for m in matches:
                            target = m[0] if m[0] else m[1]
                            if target: all_links.add(target)

        orphans = [f for f in all_files if os.path.basename(f) not in all_links]
        return "Orphaned pages: " + ", ".join(orphans) if orphans else "No orphans found."
    except Exception as e:
        return f"Error finding orphans: {str(e)}"

def rebuild_wiki_index(index_path: str, root_dir: str = "wiki") -> str:
    """Regenerates index.md with Obsidian-compatible Wikilinks."""
    if not is_safe_path(index_path):
        return "Error: Security Violation."
    
    try:
        new_index = f"--- \ntitle: Wiki Index\nupdated: {datetime.now().strftime('%Y-%m-%d')}\n---\n\n# Wiki Index\n\n"
        
        for root, dirs, files in os.walk(root_dir):
            # Filter for specific subdirectories to create sections
            folder_name = os.path.basename(root)
            if folder_name in ["sources", "concepts", "features", "products", "personas"]:
                new_index += f"## {folder_name.capitalize()}\n"
                for file in sorted(files):
                    if file.endswith(".md"):
                        name_no_ext = os.path.splitext(file)[0]
                        new_index += f"- [[{name_no_ext}]]\n"
                new_index += "\n"
        
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(new_index)
        return f"Success: {index_path} rebuilt for Obsidian."
    except Exception as e:
        return f"Error rebuilding index: {str(e)}"

# --- TEST SUITE ---
if __name__ == "__main__":
    # Create a dummy text file for testing
    test_text_file = "test_text.txt"
    with open(test_text_file, "w") as f:
        f.write("This is a plain text test.")

    print("--- Testing Unified Reader (Text) ---")
    print(f"Content: {read_document(test_text_file)}")

    print("\n--- Testing Security (Path Traversal Attempt) ---")
    print(f"Attempting to read /etc/passwd: {read_document('/etc/passwd')}")

    print("\n--- Testing list_directory (CWD) ---")
    print(list_directory("."))

    # Cleanup
    if os.path.exists(test_text_file):
        os.remove(test_text_file)
