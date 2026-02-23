#!/usr/bin/env python3
"""Generate _index.json and _index.md for the HGSI unified knowledge base."""

import json
import os
import re
from datetime import datetime, timezone

HGSI_DIR = "/Users/howardwang/Desktop/playground/avicenna/knowledge/HGSI"
SECTIONS_DIR = os.path.join(HGSI_DIR, "sections")

SECTION_TITLES = {
    "01-learning-theory": "Learning Theory",
    "02-lesson-planning": "Lesson Planning & Progressions",
    "03-communication": "Communication & Presentation",
    "04-rider-analysis": "Rider Analysis",
    "05-children-teaching": "Children's Teaching",
    "06-stance-and-movement": "Stance, Movement & Turn Mechanics",
    "07-beginner-technique": "Beginner Technique",
    "08-intermediate-technique": "Intermediate Technique",
    "09-advanced-technique": "Advanced Technique",
    "10-carving": "Carving",
    "11-freeriding": "Freeriding",
    "12-freestyle": "Freestyle & Park",
    "13-competitive": "Competitive Snowboarding",
    "14-safety": "Safety & Risk Management",
    "15-biomechanics": "Biomechanics & Anatomy",
    "16-terrain-environment": "Terrain & Environment",
    "17-equipment": "Equipment",
    "18-certification": "Certification & Course Outlines",
    "19-reference": "Reference & Glossary",
}

SECTION_CATEGORIES = {
    "01-learning-theory": "Teaching & Learning",
    "02-lesson-planning": "Teaching & Learning",
    "03-communication": "Teaching & Learning",
    "04-rider-analysis": "Teaching & Learning",
    "05-children-teaching": "Teaching & Learning",
    "06-stance-and-movement": "Technique",
    "07-beginner-technique": "Technique",
    "08-intermediate-technique": "Technique",
    "09-advanced-technique": "Technique",
    "10-carving": "Technique",
    "11-freeriding": "Technique",
    "12-freestyle": "Technique",
    "13-competitive": "Technique",
    "14-safety": "Knowledge",
    "15-biomechanics": "Knowledge",
    "16-terrain-environment": "Knowledge",
    "17-equipment": "Knowledge",
    "18-certification": "Reference",
    "19-reference": "Reference",
}


def parse_frontmatter(filepath):
    """Extract YAML frontmatter from a markdown file."""
    with open(filepath, 'r') as f:
        content = f.read()

    fm_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if not fm_match:
        return {}

    fm = {}
    for line in fm_match.group(1).split('\n'):
        m = re.match(r'^(\w[\w_]*)\s*:\s*(.+)$', line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val.startswith('[') and val.endswith(']'):
                # Parse tags list
                tags = [t.strip().strip('"').strip("'") for t in val[1:-1].split(',')]
                fm[key] = [t.strip() for t in tags if t.strip()]
            elif val.startswith('"') and val.endswith('"'):
                fm[key] = val[1:-1]
            else:
                fm[key] = val
    return fm


def extract_title(filepath):
    """Extract the first H1 title from a markdown file."""
    with open(filepath, 'r') as f:
        in_fm = False
        for line in f:
            if line.strip() == '---':
                in_fm = not in_fm
                continue
            if in_fm:
                continue
            m = re.match(r'^# (.+)$', line.strip())
            if m:
                return m.group(1)
    return os.path.splitext(os.path.basename(filepath))[0].replace('-', ' ').title()


def generate():
    """Generate index files."""
    sections = {}
    total_topics = 0

    for section_slug in sorted(os.listdir(SECTIONS_DIR)):
        section_path = os.path.join(SECTIONS_DIR, section_slug)
        if not os.path.isdir(section_path):
            continue

        topics = []
        for fname in sorted(os.listdir(section_path)):
            if not fname.endswith('.md'):
                continue

            filepath = os.path.join(section_path, fname)
            fm = parse_frontmatter(filepath)
            title = extract_title(filepath)
            slug = os.path.splitext(fname)[0]

            topic_entry = {
                "slug": slug,
                "title": title,
                "language": fm.get("language", "en"),
                "source_organization": fm.get("source_organization", "unknown"),
                "tags": fm.get("tags", []),
            }
            topics.append(topic_entry)

        section_title = SECTION_TITLES.get(section_slug, section_slug)
        sections[section_slug] = {
            "title": section_title,
            "category": SECTION_CATEGORIES.get(section_slug, "General"),
            "path": f"sections/{section_slug}/",
            "topic_count": len(topics),
            "topics": topics,
        }
        total_topics += len(topics)

    # Generate _index.json
    index_data = {
        "title": "HGSI Unified Snowboard Instruction Knowledge Base",
        "source": "SBINZ / NZSBI / CASI",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_topics": total_topics,
        "total_sections": len(sections),
        "sections": sections,
    }

    json_path = os.path.join(HGSI_DIR, "_index.json")
    with open(json_path, 'w') as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)
    print(f"Generated {json_path} ({total_topics} topics in {len(sections)} sections)")

    # Generate _index.md
    md_lines = [
        "# HGSI Unified Snowboard Instruction Knowledge Base",
        "",
        "**Sources:** SBINZ (Snowboard Instruction New Zealand), NZSBI (NZ Snowboard Instructors), CASI (Canadian Association of Snowboard Instructors)",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}",
        f"**Total Topics:** {total_topics}",
        f"**Total Sections:** {len(sections)}",
        "",
        "## How to Use",
        "",
        '**To search:** `Grep "keyword" knowledge/HGSI/`',
        "**To browse:** Check section indexes below",
        "",
        "---",
        "",
    ]

    # Group by category
    current_category = None
    for section_slug in sorted(sections.keys()):
        s = sections[section_slug]
        category = s["category"]
        if category != current_category:
            current_category = category
            md_lines.append(f"## {category}")
            md_lines.append("")

        # Count by source organization
        source_counts = {}
        lang_counts = {"en": 0, "zh": 0}
        for t in s["topics"]:
            org = t.get("source_organization", "unknown")
            source_counts[org] = source_counts.get(org, 0) + 1
            lang = t.get("language", "en")
            lang_counts[lang] = lang_counts.get(lang, 0) + 1

        source_str = ", ".join(f"{org}: {count}" for org, count in sorted(source_counts.items()))
        lang_str = f"EN: {lang_counts['en']}" + (f", ZH: {lang_counts['zh']}" if lang_counts['zh'] > 0 else "")

        md_lines.append(f"### {s['title']}")
        md_lines.append(f"**Path:** `sections/{section_slug}/` | **Topics:** {s['topic_count']} | **Sources:** {source_str} | **Languages:** {lang_str}")
        md_lines.append("")

        for t in s["topics"]:
            lang_badge = " `[zh]`" if t.get("language") == "zh" else ""
            org_badge = f" *({t.get('source_organization', '')})*"
            md_lines.append(f"- [{t['title']}](sections/{section_slug}/{t['slug']}.md){lang_badge}{org_badge}")

        md_lines.append("")

    md_path = os.path.join(HGSI_DIR, "_index.md")
    with open(md_path, 'w') as f:
        f.write('\n'.join(md_lines))
    print(f"Generated {md_path}")


if __name__ == "__main__":
    generate()
