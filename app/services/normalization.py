import unicodedata
import re

def normalize_ingredient_name(name: str) -> str:
    """
    - Lowercase
    - Remove accents
    - Remove special chars
    - Apply basic variant map
    """
    if not name:
        return ""

    # 1. Lowercase
    name = name.lower().strip()

    # 2. Remove accents
    name = ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')

    # 3. Remove special chars (keep letters, numbers, spaces, maybe hyphens)
    name = re.sub(r'[^a-z0-9\s\-]', '', name)

    # 4. Collapse multiple spaces
    name = re.sub(r'\s+', ' ', name).strip()

    # 5. Map variants (simple stub)
    variants = {
        "skim milk": "skimmed milk",
        # Add more here
    }
    
    return variants.get(name, name)
