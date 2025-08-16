import re

def parse_metadata_from_comments(code: str) -> dict:
    metadata = {}
    pattern = re.compile(r'__([a-zA-Z0-9_]+)__\s*=\s*["\']?(.*?)["\']?$')

    for line in code.splitlines():
        line = line.strip()
        if line.startswith(('#', '//', '<!--')) or line.startswith('__'):
            match = pattern.search(line)
            if match:
                key, value = match.groups()
                metadata[key] = value

        if line == "" or not line.startswith(('#', '//', '<!--')):  # kończymy po nagłówku
            break

    return metadata