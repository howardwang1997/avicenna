#!/usr/bin/env python3
"""Migrate SBINZ knowledge base files to HGSI unified knowledge base."""

import os
import re
import shutil

SBINZ_DIR = "/Users/howardwang/Desktop/playground/avicenna/knowledge/SBINZ"
HGSI_DIR = "/Users/howardwang/Desktop/playground/avicenna/knowledge/HGSI/sections"

# Mapping: old SBINZ section → new HGSI section
SECTION_MAPPING = {
    # 01-learning-theory
    "how-people-learn": "01-learning-theory",
    "getting-stoked-on-snowboarding": "01-learning-theory",
    # 02-lesson-planning
    "structuring-lessons-and-sessions": "02-lesson-planning",
    "using-adapting-creating-progressions": "02-lesson-planning",
    # 03-communication
    "effective-presentation": "03-communication",
    "delivering-feedback": "03-communication",
    # 04-rider-analysis
    "effective-rider-analysis": "04-rider-analysis",
    # 05-children-teaching
    "teaching-children": "05-children-teaching",
    # 06-stance-and-movement
    "movements-of-snowboarding": "06-stance-and-movement",
    "the-snowboard-turn": "06-stance-and-movement",
    "how-the-snowboard-performs": "06-stance-and-movement",
    # 07-beginner-technique
    "first-time-snowboarders": "07-beginner-technique",
    "learning-beginner-turns": "07-beginner-technique",
    # 08-intermediate-technique
    "exploring-intermediate-turns": "08-intermediate-technique",
    # 09-advanced-technique
    "mastering-advanced-turns": "09-advanced-technique",
    # 10-carving
    "exploring-carving": "10-carving",
    "advanced-carving": "10-carving",
    # 11-freeriding
    "exploring-freeriding": "11-freeriding",
    "advanced-freeriding": "11-freeriding",
    # 12-freestyle
    "exploring-freestyle": "12-freestyle",
    "advanced-freestyle": "12-freestyle",
    # 13-competitive
    "competitive-snowboarding": "13-competitive",
    # 15-biomechanics
    "basic-biomechanics": "15-biomechanics",
    # 17-equipment
    "snowboard-equipment": "17-equipment",
    # 19-reference
    "glossary": "19-reference",
    "maori-translations": "19-reference",
}

# Special per-file overrides for terrain-and-environment section
TERRAIN_FILE_MAPPING = {
    "scope.md": "14-safety",
    "terrain-park-riding.md": "14-safety",
    "terrain-selection-and-weather.md": "14-safety",
    "reading-advanced-terrain.md": "16-terrain-environment",
    "snow-conditions.md": "16-terrain-environment",
}


def update_frontmatter(content: str, new_section: str) -> str:
    """Update frontmatter fields for HGSI migration."""
    # Match YAML frontmatter
    fm_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if not fm_match:
        return content

    fm_text = fm_match.group(1)
    rest = content[fm_match.end():]

    # Update name: sbinz-{old-section}-{topic} → hgsi-{new-section}-{topic}
    def replace_name(m):
        old_name = m.group(1)
        # Extract topic slug: remove sbinz-{old-section}- prefix
        # Pattern: sbinz-{section}-{topic}
        parts = old_name.split('-')
        # Find where the old section ends and topic begins
        # We need to match against known old sections
        for old_sec in SECTION_MAPPING:
            prefix = f"sbinz-{old_sec}-"
            if old_name.startswith(prefix):
                topic_slug = old_name[len(prefix):]
                return f"name: hgsi-{new_section}-{topic_slug}"
        # For terrain-and-environment special cases
        prefix = "sbinz-terrain-and-environment-"
        if old_name.startswith(prefix):
            topic_slug = old_name[len(prefix):]
            return f"name: hgsi-{new_section}-{topic_slug}"
        # Fallback: just replace sbinz with hgsi
        return f"name: {old_name.replace('sbinz-', 'hgsi-', 1)}"

    fm_text = re.sub(r'name: (.+)', replace_name, fm_text)

    # Update tags: replace old section slug with new section slug
    def replace_tags(m):
        tags_str = m.group(1)
        # Parse tags list
        tags = [t.strip().strip('"').strip("'") for t in tags_str.strip('[]').split(',')]
        new_tags = []
        for tag in tags:
            tag = tag.strip()
            if tag == 'sbinz':
                new_tags.append('hgsi')
            elif tag in SECTION_MAPPING:
                new_tags.append(new_section)
            elif tag == 'terrain-and-environment':
                new_tags.append(new_section)
            else:
                new_tags.append(tag)
        # Deduplicate while preserving order
        seen = set()
        deduped = []
        for t in new_tags:
            if t not in seen:
                seen.add(t)
                deduped.append(t)
        return f"tags: [{', '.join(deduped)}]"

    fm_text = re.sub(r'tags: (\[.+?\])', replace_tags, fm_text)

    return f"---\n{fm_text}\n---\n{rest}"


def migrate():
    """Run the migration."""
    migrated = 0
    errors = []

    # Process section directories
    for entry in sorted(os.listdir(SBINZ_DIR)):
        entry_path = os.path.join(SBINZ_DIR, entry)

        # Handle standalone files (document-overview.md)
        if os.path.isfile(entry_path) and entry.endswith('.md'):
            if entry == 'document-overview.md':
                dest_section = "19-reference"
                dest_path = os.path.join(HGSI_DIR, dest_section, entry)
                content = open(entry_path, 'r').read()
                content = update_frontmatter(content, dest_section)
                # Fix name for standalone file
                content = content.replace(
                    'name: hgsi-document-overview',
                    'name: hgsi-19-reference-document-overview'
                )
                with open(dest_path, 'w') as f:
                    f.write(content)
                migrated += 1
                print(f"  {entry} → {dest_section}/")
            continue

        if not os.path.isdir(entry_path):
            continue

        # Skip non-section entries
        if entry.startswith('_') or entry.startswith('.'):
            continue

        section_name = entry

        # Handle terrain-and-environment specially (per-file mapping)
        if section_name == "terrain-and-environment":
            for fname in sorted(os.listdir(entry_path)):
                if not fname.endswith('.md'):
                    continue
                src = os.path.join(entry_path, fname)
                dest_section = TERRAIN_FILE_MAPPING.get(fname)
                if not dest_section:
                    errors.append(f"No mapping for terrain-and-environment/{fname}")
                    continue
                content = open(src, 'r').read()
                content = update_frontmatter(content, dest_section)
                dest = os.path.join(HGSI_DIR, dest_section, fname)
                with open(dest, 'w') as f:
                    f.write(content)
                migrated += 1
                print(f"  terrain-and-environment/{fname} → {dest_section}/")
            continue

        # Normal section mapping
        dest_section = SECTION_MAPPING.get(section_name)
        if not dest_section:
            errors.append(f"No mapping for section: {section_name}")
            continue

        for fname in sorted(os.listdir(entry_path)):
            if not fname.endswith('.md'):
                continue
            src = os.path.join(entry_path, fname)
            content = open(src, 'r').read()
            content = update_frontmatter(content, dest_section)
            dest = os.path.join(HGSI_DIR, dest_section, fname)
            with open(dest, 'w') as f:
                f.write(content)
            migrated += 1
            print(f"  {section_name}/{fname} → {dest_section}/")

    print(f"\nMigrated {migrated} files")
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")

    # Print per-section counts
    print("\nPer-section file counts:")
    for section in sorted(os.listdir(HGSI_DIR)):
        section_path = os.path.join(HGSI_DIR, section)
        if os.path.isdir(section_path):
            count = len([f for f in os.listdir(section_path) if f.endswith('.md')])
            print(f"  {section}: {count}")


if __name__ == "__main__":
    migrate()
