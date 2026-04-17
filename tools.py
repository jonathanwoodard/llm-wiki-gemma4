import os
import re
import yaml
import requests
import datetime
from bs4 import BeautifulSoup
from docling.document_converter import DocumentConverter

# --- SECURITY LAYER ---

def is_safe_path(target_path: str) -> bool:
    base_dir = os.path.realpath(os.getcwd())
    target_dir = os.path.realpath(target_path)
    try:
        return os.path.commonpath([base_dir, target_dir]) == base_dir
    except ValueError:
        return False

# --- NEW & UPDATED TOOLS ---

def read_file(path: str) -> str:
    if not is_safe_path(path):
        return f"Error: Security Violation. Access to '{path}' is denied."
    try:
        with open(path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        return f"Error: {str(e)}"

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
        return f"Success: File {path} written."
    except Exception as e:
        return f"Error: {str(e)}"

def append_to_file(path: str, content: str) -> str:
    """Safely appends content to a file (useful for log.md and index.md)."""
    if not is_safe_path(path):
        return "Error: Security Violation."
    try:
        with open(path, 'a', encoding='utf-8') as file:
            file.write(f"\n{content}")
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
        content = read_file(path)
        match = re.search(r'^---\s*(.*?)\s*---', content, re.DOTALL)
        if match:
            # We return it as a string for the LLM to parse or view
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

def read_pdf(path: str) -> str:
    if not is_safe_path(path):
        return "Error: Security Violation."
    try:
        converter = DocumentConverter()
        return converter.convert(path).document.export_to_markdown()
    except Exception as e:
        return f"Error: {str(e)}"

def web_scrape(url: str) -> str:
    """Scrapes a URL and returns a simplified Markdown version of the text content."""
    if not is_safe_path(url): # Note: In a real scenario, you'd use a URL validator, not is_safe_path
        return "Error: Invalid URL."
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Basic conversion: extract text and wrap in simple MD structure
        title = soup.title.string if soup.title else "No Title"
        paragraphs = [p.get_text() for p in soup.find_all('p')]
        content = f"# {title}\n\nSource: {url}\n\n" + "\n\n".join(paragraphs)
        return content
    except Exception as e:
        return f"Error scraping URL: {str(e)}"

def check_broken_links(root_dir: str = "wiki") -> str:
    """Scans all markdown files in the wiki for broken internal [[links]] or [links](path)."""
    if not is_cap_safe_path(root_dir): # Assuming a helper for directory validation
        return "Error: Security Violation."
    
    broken_links = []
    # Regex to find [[Link]] or [Text](path.md)
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
                            # match is a tuple (group1, group2) from the regex
                            link_target = match[0] if match[0] else match[1]
                            if not link_target: continue
                            
                            # Check if the target file exists (handling relative paths)
                            # This is a simplified check; real implementation needs path resolution
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
    """Automatically regenerates the index.md based on the current wiki structure."""
    if not is_safe_path(index_path):
        return "Error: Security Violation."
    
    try:
        new_index = "# Wiki Index\n\nGenerated on: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n"
        categories = {}

        for root, _, files in os.walk(root_dir):
            for file in files:
                if file.endswith(".md") and file != os.path.basename(index_path):
                    rel_path = os.path.relpath(os.path.join(root, file), root_dir)
                    cat = os.path.dirname(rel_path).split(os.sep)[0] or "General"
                    if cat not in categories: categories[cat] = []
                    categories[cat].append(rel_path)

        for cat, paths in categories.items():
            new_index += f"## {cat.capitalize()}\n"
            for p in paths:
                new_index += f"- [[{p}]]\n"
            new_index += "\n"

        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(new_index)
        return f"Success: {index_path} rebuilt."
    except Exception as e:
        return f"Error rebuilding index: {str(e)}"


# --- TEST SUITE ---
if __name__ == "__main__":
    # Create a dummy file for testing
    test_file = "test_agent_file.txt"
    with open(test_file, "w") as f:
        f.write("Hello, this is a secure test.")

    print("--- Testing Security (Path Traversal Attempt) ---")
    print(f"Attempting to read /etc/passwd: {read_file('/etc/passwd')}")

    print("\n--- Testing list_directory (CWD) ---")
    print(list_directory("."))

    print("\n--- Testing write_file ---")
    print(write_file("subfolder/new_test.txt", "Secure content."))

    print("\n--- Testing read_file ---")
    print(f"Content: {read_file(test_file)}")

    # Cleanup
    if os.path.exists(test_file):
        os.remove(test_file)










