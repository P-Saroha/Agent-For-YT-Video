#!/usr/bin/env python3
"""
Code Optimization Script
Removes emojis, cleans up unnecessary code, and optimizes service files
"""
import re
import os
from pathlib import Path

def remove_emojis(text):
    """Remove all emojis from text"""
    # Comprehensive emoji pattern
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', text)

def optimize_file(file_path):
    """Optimize a single Python file"""
    print(f"Optimizing: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_lines = len(content.splitlines())
    
    # Remove emojis
    content = remove_emojis(content)
    
    # Clean up excessive whitespace
    content = re.sub(r'\n{4,}', '\n\n\n', content)
    
    # Remove trailing whitespace
    lines = [line.rstrip() for line in content.splitlines()]
    content = '\n'.join(lines)
    
    # Ensure file ends with newline
    if not content.endswith('\n'):
        content += '\n'
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    optimized_lines = len(content.splitlines())
    print(f"  - Removed emojis")
    print(f"  - Lines: {original_lines} -> {optimized_lines}")
    print(f"  - Saved!")

def main():
    """Main optimization function"""
    print("=" * 60)
    print("CODE OPTIMIZATION - Removing Emojis & Cleaning Up")
    print("=" * 60)
    print()
    
    # Service files to optimize
    services_dir = Path(__file__).parent / 'app' / 'services'
    service_files = [
        services_dir / 'langchain_service.py',
        services_dir / 'rag_web_service.py',
        services_dir / 'document_service.py',
        services_dir / 'simple_ai_service.py'
    ]
    
    # Also optimize routes
    routes_dir = Path(__file__).parent / 'app' / 'routes'
    route_files = list(routes_dir.glob('*.py'))
    
    all_files = service_files + route_files
    
    for file_path in all_files:
        if file_path.exists():
            optimize_file(file_path)
            print()
    
    print("=" * 60)
    print("OPTIMIZATION COMPLETE!")
    print("=" * 60)

if __name__ == '__main__':
    main()
