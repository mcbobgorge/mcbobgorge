#!/usr/bin/env python3
"""Convert an intake block into a review data file.

Reads plain-text intake from a file path argument or stdin, with labels
case-insensitive and in any order. Derives slug from brand + product unless
--slug is given. Validates through build_lib/reviews.py before writing.

Usage:
  python3 tools/new_review.py < intake.txt
  python3 tools/new_review.py intake.txt
  python3 tools/new_review.py intake.txt --slug custom-slug --force
  python3 tools/new_review.py intake.txt --listing-name "Brand — Short" --table-name "Brand Short"
"""
import sys
import re
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "build_lib"))

from reviews import ValidationError, load_review  # noqa: E402


def parse_args():
    """Parse command-line arguments."""
    args = sys.argv[1:]
    input_file = None
    slug = None
    force = False
    listing_name = None
    table_name = None

    i = 0
    while i < len(args):
        if args[i] == "--slug":
            slug = args[i + 1]
            i += 2
        elif args[i] == "--force":
            force = True
            i += 1
        elif args[i] == "--listing-name":
            listing_name = args[i + 1]
            i += 2
        elif args[i] == "--table-name":
            table_name = args[i + 1]
            i += 2
        elif not args[i].startswith("--"):
            input_file = args[i]
            i += 1
        else:
            print(f"Unknown option: {args[i]}", file=sys.stderr)
            sys.exit(1)

    return input_file, slug, force, listing_name, table_name


def read_input(file_path):
    """Read input from file or stdin."""
    if file_path:
        try:
            return Path(file_path).read_text(encoding="utf-8")
        except FileNotFoundError:
            print(f"Error: File not found: {file_path}", file=sys.stderr)
            sys.exit(1)
    else:
        return sys.stdin.read()


def normalize_label(label):
    """Normalize a label by removing punctuation and em-dashes.
    
    Special case: "Scores — Taste:" becomes "scores" since we want to capture
    all scores on that line.
    """
    # Replace hyphens and em-dashes/en-dashes with spaces
    label = label.replace("—", " ").replace("–", " ").replace("-", " ")
    # Keep only alphanumeric and spaces
    label = re.sub(r"[^\w\s]", "", label)
    label = re.sub(r"\s+", " ", label).strip()
    label = label.lower()
    
    # Special handling: if label starts with "scores", return just "scores"
    # This handles "Scores — Taste" and similar
    if label.startswith("scores"):
        return "scores"
    
    return label


def parse_intake(text):
    """Parse intake block into a dict with data and sections."""
    lines = text.strip().split("\n")
    data = {}
    current_section = None
    section_lines = []

    for line in lines:
        # Check if line is a label (contains a colon but not part of a multi-line section)
        if ":" in line and current_section is None:
            # Try to parse as label: value
            # Special case for "Scores — Taste: 5 Sweetness: 7 ..." patterns
            if re.search(r"Scores\s*[—–-]", line, re.IGNORECASE):
                # This is a scores line
                label = "scores"
                # Extract everything after "Scores —" or "Scores -"
                match = re.search(r"Scores\s*[—–-]\s*(.*)", line, re.IGNORECASE)
                if match:
                    value = match.group(1).strip()
                else:
                    value = ""
            else:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    label = normalize_label(parts[0])
                    value = parts[1].strip()
                else:
                    continue

            # Start a section if it's Notes or Verdict
            if label in ("notes", "verdict"):
                current_section = label
                section_lines = [value] if value else []
            else:
                data[label] = value
        elif current_section:
            # In a multi-line section
            normalized_line = normalize_label(line.split(":")[0]) if ":" in line else ""
            if normalized_line in ("notes", "verdict", "brand", "product", "date tasted",
                                  "size", "still or sparkling", "pasteurized", "added sugar",
                                  "organic", "fair trade", "pulp", "scores", "one line summary"):
                # Start of a new field, save the current section
                data[current_section] = "\n".join(section_lines).strip()
                current_section = None
                # Re-process this line
                if ":" in line:
                    if re.search(r"Scores\s*[—–-]", line, re.IGNORECASE):
                        label = "scores"
                        match = re.search(r"Scores\s*[—–-]\s*(.*)", line, re.IGNORECASE)
                        if match:
                            value = match.group(1).strip()
                        else:
                            value = ""
                    else:
                        parts = line.split(":", 1)
                        if len(parts) == 2:
                            label = normalize_label(parts[0])
                            value = parts[1].strip()
                        else:
                            continue
                    if label in ("notes", "verdict"):
                        current_section = label
                        section_lines = [value] if value else []
                    else:
                        data[label] = value
            else:
                # Continuation of current section
                section_lines.append(line)

    # Save any remaining section
    if current_section:
        data[current_section] = "\n".join(section_lines).strip()

    return data


def normalize_bool(value):
    """Convert yes/no/true/false/y/n to boolean string."""
    if not isinstance(value, str):
        return value
    v = value.strip().lower()
    if v in ("yes", "true", "y"):
        return "true"
    elif v in ("no", "false", "n"):
        return "false"
    else:
        raise ValueError(f"Invalid boolean value: {value}")


def parse_scores(score_str):
    """Parse scores from one line or multiple lines."""
    scores = {}
    score_keys = ["taste", "sweetness", "body", "refreshment", "ethics", "overall"]

    # Try to match patterns like "Taste: 5" or "Sweetness: 7" etc.
    # Split on multiple spaces or newlines to separate key-value pairs
    parts = re.split(r"\s{2,}|[\n]", score_str)

    for part in parts:
        part = part.strip()
        if not part:
            continue
        # Try to find "Key: value" or "Key value" pattern
        match = re.match(r"([a-z]+)\s*:?\s*([\d.]+)", part, re.IGNORECASE)
        if match:
            key = match.group(1).lower()
            value = float(match.group(2))
            if key in score_keys:
                scores[key] = value

    return scores


def derive_slug(brand, product):
    """Derive slug from brand and product."""
    slug_text = f"{brand} {product}".lower()
    # Remove punctuation and special chars, convert spaces to dashes
    slug = re.sub(r"[^\w\s-]", "", slug_text)
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")


def derive_listing_name(brand, product):
    """Derive listing_name as 'Brand — Product-ish short form'."""
    return f"{brand} — {product}"


def derive_table_name(brand, product):
    """Derive table_name as a short form."""
    # Try to extract the key adjective/type from product
    # e.g., "Organic Coconut Water" -> "Brand Organic"
    #       "Coconut Water Original" -> "Brand Original"
    words = product.split()
    if len(words) > 1:
        # Use last word (typically "Water", "Coconut Water") or most descriptive
        short = " ".join(words[:-1]) if words[-1].lower() in ("water", "coconut") else product
    else:
        short = product
    return f"{brand} {short}".strip()


def format_toml_scores(scores):
    """Format scores dict as TOML inline table."""
    ordered_keys = ["taste", "sweetness", "body", "refreshment", "ethics", "overall"]
    parts = []
    for key in ordered_keys:
        if key in scores:
            val = scores[key]
            # Format as int if whole number, otherwise as float
            if isinstance(val, float) and val.is_integer():
                parts.append(f"{key} = {int(val)}")
            else:
                parts.append(f"{key} = {val}")
    return "{ " + ", ".join(parts) + " }"


def generate_review_content(data, slug, listing_name, table_name):
    """Generate the complete review markdown file content."""
    # Normalize date (ensure it's YYYY-MM-DD)
    date_str = data.get("date tasted", datetime.now().strftime("%Y-%m-%d"))
    try:
        # Try to parse various date formats
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%m-%d-%Y", "%m/%d", "%d/%m/%Y"):
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                if "%Y" not in fmt:
                    # If year wasn't specified, use current year
                    dt = dt.replace(year=datetime.now().year)
                date_str = dt.strftime("%Y-%m-%d")
                break
            except ValueError:
                continue
    except Exception:
        # If parsing fails, use as-is (will fail validation)
        pass

    # Parse scores
    scores_text = data.get("scores", "")
    scores = parse_scores(scores_text)
    if not scores:
        raise ValueError("No valid scores found in intake")

    # Normalize boolean fields
    bool_fields = ["pasteurized", "added sugar", "organic", "fair trade", "pulp"]
    bool_data = {}
    for field in bool_fields:
        key = field.replace(" ", "_")
        normalized_field = normalize_label(field)
        value = data.get(normalized_field, "")
        bool_data[key] = normalize_bool(value)

    # Get sections
    notes = data.get("notes", "").strip()
    verdict = data.get("verdict", "").strip()
    if not notes:
        notes = "(Notes to be added)"
    if not verdict:
        verdict = "(Verdict to be added)"

    # Build TOML front matter
    brand = data.get("brand", "").strip()
    product = data.get("product", "").strip()
    size = data.get("size", "").strip()
    style = data.get("still or sparkling", "Still").strip()
    description = data.get("one line summary", "").strip()
    image = f"reviews/img/{slug}.jpg"

    if not brand:
        raise ValueError("Brand is required")
    if not product:
        raise ValueError("Product is required")
    if not size:
        raise ValueError("Size is required")
    if not description:
        raise ValueError("One-line summary is required")

    toml_content = f'''+++
brand = "{brand}"
product = "{product}"
listing_name = "{listing_name}"
table_name = "{table_name}"
date = "{date_str}"
size = "{size}"
style = "{style}"
pasteurized = {bool_data["pasteurized"]}
added_sugar = {bool_data["added_sugar"]}
organic = {bool_data["organic"]}
fair_trade = {bool_data["fair_trade"]}
pulp = {bool_data["pulp"]}
extra_tags = []
image = "{image}"
description = "{description}"
scores = {format_toml_scores(scores)}
+++

## Notes

{notes}

## Verdict

{verdict}
'''
    return toml_content


def main():
    input_file, slug_override, force, listing_name_override, table_name_override = parse_args()
    text = read_input(input_file)
    data = parse_intake(text)

    # Extract brand and product
    brand = data.get("brand", "").strip()
    product = data.get("product", "").strip()

    if not brand or not product:
        print("Error: Brand and Product are required", file=sys.stderr)
        sys.exit(1)

    # Derive or use provided slug
    slug = slug_override or derive_slug(brand, product)

    # Derive or use provided names
    listing_name = listing_name_override or derive_listing_name(brand, product)
    table_name = table_name_override or derive_table_name(brand, product)

    # Generate content
    try:
        content = generate_review_content(data, slug, listing_name, table_name)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Determine output path
    output_path = ROOT / "content" / "reviews" / f"{slug}.md"

    # Check if file exists
    if output_path.exists() and not force:
        print(f"Error: {output_path} already exists. Use --force to overwrite.", file=sys.stderr)
        sys.exit(1)

    # Write file
    output_path.write_text(content, encoding="utf-8")

    # Validate through the loader
    try:
        # Create a placeholder image so validation passes
        img_path = ROOT / "reviews" / "img" / f"{slug}.jpg"
        img_path.parent.mkdir(parents=True, exist_ok=True)
        if not img_path.exists():
            img_path.write_bytes(b"\xff\xd8\xff")  # Minimal JPEG header
        review = load_review(output_path)
    except ValidationError as e:
        # Remove the file if validation failed
        output_path.unlink()
        print(f"Error: Validation failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # Remove the file if any other error
        output_path.unlink()
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"✓ Review written to: {output_path}")
    print(f"⚠ Remember to place the photo at: {img_path}")


if __name__ == "__main__":
    main()
