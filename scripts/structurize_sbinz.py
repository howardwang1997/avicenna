#!/usr/bin/env python3
"""
Structurize SBINZ Manual into knowledge base files.
Splits the 16500+ line manual into section-organized topic files
following the HeygoAgent knowledge format but with full content.
"""

import json
import re
import os
from datetime import datetime
from pathlib import Path

SOURCE_FILE = Path(__file__).parent.parent / "notes" / "SBINZ-manual-FullPDF-30 may 2025" / "content.md"
OUTPUT_DIR = Path(__file__).parent.parent / "knowledge" / "sbinz-full"

# ── Section and topic definitions based on TOC ──────────────────────────────
# Each section has: title, dir_name, subsections
# Each subsection has: title, topics list
# Each topic has: title, slug, start_line, category tag

SECTIONS = {
    "a": {
        "title": "Creating a Learning Environment",
        "dir": "a-learning-environment",
        "topics": [
            # Getting Stoked on Snowboarding
            {"title": "Safety", "slug": "safety", "start": 318, "cat": "safety"},
            {"title": "Fun", "slug": "fun", "start": 445, "cat": "teaching-theory"},
            {"title": "Achievement", "slug": "achievement", "start": 506, "cat": "teaching-theory"},
            {"title": "Recognition", "slug": "recognition", "start": 546, "cat": "teaching-theory"},
            {"title": "Stoke", "slug": "stoke", "start": 605, "cat": "teaching-theory"},
            {"title": "Maslow's Hierarchy of Needs", "slug": "maslows-hierarchy-of-needs", "start": 655, "cat": "teaching-theory"},
            {"title": "Understanding Fear & The Three Cs", "slug": "understanding-fear-and-the-three-cs", "start": 720, "cat": "teaching-theory"},
            # How People Learn
            {"title": "Stages of Skill Acquisition", "slug": "stages-of-skill-acquisition", "start": 824, "cat": "teaching-theory"},
            {"title": "The Eight Multiple Intelligences", "slug": "multiple-intelligences", "start": 909, "cat": "teaching-theory"},
            {"title": "Self Efficacy", "slug": "self-efficacy", "start": 963, "cat": "teaching-theory"},
            # Structuring Lessons & Sessions
            {"title": "Lesson Format", "slug": "lesson-format", "start": 1111, "cat": "teaching-theory"},
            {"title": "Activity-Analyse-Adapt Teaching Cycle", "slug": "activity-analyse-adapt", "start": 1304, "cat": "teaching-theory"},
            {"title": "Distributed Learning & Practice", "slug": "distributed-learning-and-practice", "start": 1412, "cat": "teaching-theory"},
            {"title": "Instructing vs Coaching & Training", "slug": "instructing-vs-coaching", "start": 1528, "cat": "teaching-theory"},
            # Using, Adapting & Creating Progressions
            {"title": "Student Levels & Development Options", "slug": "student-levels-and-development-options", "start": 1578, "cat": "progression"},
            {"title": "Copying Sample Progressions", "slug": "copying-sample-progressions", "start": 1734, "cat": "progression"},
            {"title": "Choosing Developmental & Corrective Progressions", "slug": "choosing-progressions", "start": 1773, "cat": "progression"},
            {"title": "Creating Progressions", "slug": "creating-progressions", "start": 1840, "cat": "progression"},
            # Effective Presentation
            {"title": "Building Relationships & Interacting with Guests", "slug": "building-relationships", "start": 1859, "cat": "teaching-theory"},
            {"title": "What-Why-How Simple Descriptions", "slug": "what-why-how", "start": 1954, "cat": "teaching-theory"},
            {"title": "Talk-Show-Feel Communication Modes", "slug": "talk-show-feel", "start": 2016, "cat": "teaching-theory"},
            {"title": "Pacing of Information", "slug": "pacing-of-information", "start": 2041, "cat": "teaching-theory"},
            {"title": "Utilising Different Teaching Styles", "slug": "teaching-styles", "start": 2122, "cat": "teaching-theory"},
            {"title": "Question Based Learning", "slug": "question-based-learning", "start": 2187, "cat": "teaching-theory"},
            {"title": "Body Language", "slug": "body-language", "start": 2327, "cat": "teaching-theory"},
            {"title": "Tone of Voice", "slug": "tone-of-voice", "start": 2425, "cat": "teaching-theory"},
            {"title": "Judger vs Learner", "slug": "judger-vs-learner", "start": 2527, "cat": "teaching-theory"},
            {"title": "The Matching Principle", "slug": "the-matching-principle", "start": 2570, "cat": "teaching-theory"},
            {"title": "Looping", "slug": "looping", "start": 2632, "cat": "teaching-theory"},
            {"title": "Intention & Adapting Delivery Method", "slug": "intention-and-adapting-delivery", "start": 2641, "cat": "teaching-theory"},
            # Delivering Feedback
            {"title": "Introduction to Feedback", "slug": "introduction-to-feedback", "start": 2727, "cat": "teaching-theory"},
            {"title": "Developing Feedback", "slug": "developing-feedback", "start": 2849, "cat": "teaching-theory"},
            {"title": "Seek-Give-Seek Feedback", "slug": "seek-give-seek-feedback", "start": 2926, "cat": "teaching-theory"},
            # Teaching Children
            {"title": "Basics of Teaching Children", "slug": "basics-of-teaching-children", "start": 3014, "cat": "children"},
            {"title": "Profiling Children", "slug": "profiling-children", "start": 3076, "cat": "children"},
            {"title": "Motivations", "slug": "motivations", "start": 3174, "cat": "children"},
            {"title": "Negative Behaviours", "slug": "negative-behaviours", "start": 3193, "cat": "children"},
            {"title": "The C.A.P Model", "slug": "the-cap-model", "start": 3226, "cat": "children"},
            {"title": "Creative Lesson Building", "slug": "creative-lesson-building", "start": 3343, "cat": "children"},
            {"title": "Rider Analysis for Children", "slug": "rider-analysis-for-children", "start": 3435, "cat": "children"},
            {"title": "Equipment for Children", "slug": "equipment-for-children", "start": 3468, "cat": "children"},
        ],
    },
    "b": {
        "title": "Technical Understanding",
        "dir": "b-technical",
        "topics": [
            # The Snowboard Turn
            {"title": "Turn Size, Shape & Performance", "slug": "turn-size-shape-performance", "start": 3553, "cat": "technique"},
            {"title": "Turn Phases", "slug": "turn-phases", "start": 3599, "cat": "technique"},
            {"title": "Beginner Turns", "slug": "beginner-turns", "start": 3686, "cat": "technique"},
            {"title": "Intermediate Turns", "slug": "intermediate-turns", "start": 3762, "cat": "technique"},
            {"title": "Advanced Turns", "slug": "advanced-turns", "start": 3866, "cat": "technique"},
            {"title": "Turn Forces", "slug": "turn-forces", "start": 4010, "cat": "technique"},
            # The Movements of Snowboarding
            {"title": "Basic Stance", "slug": "basic-stance", "start": 4080, "cat": "technique"},
            {"title": "Four Movement Options", "slug": "four-movement-options", "start": 4218, "cat": "technique"},
            {"title": "Active Stance", "slug": "active-stance", "start": 4486, "cat": "technique"},
            {"title": "Reactive Balance", "slug": "reactive-balance", "start": 4535, "cat": "technique"},
            {"title": "Applying Movements", "slug": "applying-movements", "start": 4613, "cat": "technique"},
            {"title": "High Performance Stance", "slug": "high-performance-stance", "start": 4840, "cat": "technique"},
            {"title": "Proactive Balance", "slug": "proactive-balance", "start": 4887, "cat": "technique"},
            {"title": "Quantifying Movements", "slug": "quantifying-movements", "start": 4903, "cat": "technique"},
            # How the Snowboard Performs
            {"title": "Board Performance", "slug": "board-performance", "start": 5155, "cat": "technique"},
            {"title": "Edge Pressure Steer Sequence", "slug": "edge-pressure-steer-sequence", "start": 5305, "cat": "technique"},
            {"title": "Understanding Steering Angle", "slug": "understanding-steering-angle", "start": 5382, "cat": "technique"},
            {"title": "Creating & Managing Rebound", "slug": "creating-and-managing-rebound", "start": 5415, "cat": "technique"},
            # Terrain & Environment
            {"title": "Terrain Selection & Fall Lines", "slug": "terrain-selection-and-fall-lines", "start": 5468, "cat": "technique"},
            {"title": "Mountain Weather", "slug": "mountain-weather", "start": 5549, "cat": "safety"},
            {"title": "Terrain Park Riding", "slug": "terrain-park-riding", "start": 5570, "cat": "freestyle"},
            {"title": "Park SMART & SCOPE", "slug": "park-smart-and-scope", "start": 5734, "cat": "freestyle"},
            {"title": "Snow Conditions", "slug": "snow-conditions", "start": 5853, "cat": "technique"},
            {"title": "Reading Advanced Terrain", "slug": "reading-advanced-terrain", "start": 6034, "cat": "technique"},
            # Basic Biomechanics
            {"title": "Joints", "slug": "joints", "start": 6211, "cat": "technique"},
            {"title": "Connective Tissue & Muscles", "slug": "connective-tissue-and-muscles", "start": 6305, "cat": "technique"},
            {"title": "Female Biomechanics & Anatomy", "slug": "female-biomechanics-and-anatomy", "start": 6389, "cat": "technique"},
            {"title": "Neuroplasticity & Proprioception", "slug": "neuroplasticity-and-proprioception", "start": 6525, "cat": "technique"},
            {"title": "Injury Prevention", "slug": "injury-prevention", "start": 6541, "cat": "safety"},
            # Effective Rider Analysis
            {"title": "Intro to Rider Analysis", "slug": "intro-to-rider-analysis", "start": 6614, "cat": "assessment"},
            {"title": "Analysing Stance", "slug": "analysing-stance", "start": 6757, "cat": "assessment"},
            {"title": "Analysing Movements", "slug": "analysing-movements", "start": 6776, "cat": "assessment"},
            {"title": "Understanding Cause & Effect", "slug": "understanding-cause-and-effect", "start": 6801, "cat": "assessment"},
            {"title": "Prioritising Inefficiencies", "slug": "prioritising-inefficiencies", "start": 6869, "cat": "assessment"},
            {"title": "The Domino Effect", "slug": "the-domino-effect", "start": 6954, "cat": "assessment"},
        ],
    },
    "c": {
        "title": "Teaching Beginner Snowboarders",
        "dir": "c-beginner",
        "topics": [
            # First-Time Snowboarders
            {"title": "Intro to Equipment & Movements", "slug": "intro-to-equipment-and-movements", "start": 7131, "cat": "progression"},
            {"title": "Skating, Gliding, Climbing", "slug": "skating-gliding-climbing", "start": 7293, "cat": "progression"},
            {"title": "Straight Runs & Direction Changes (J-Turns)", "slug": "straight-runs-and-j-turns", "start": 7445, "cat": "progression"},
            {"title": "Two Footed Orientation", "slug": "two-footed-orientation", "start": 7676, "cat": "progression"},
            {"title": "Heelside Control", "slug": "heelside-control", "start": 7766, "cat": "progression"},
            {"title": "Toeside Control", "slug": "toeside-control", "start": 8031, "cat": "progression"},
            {"title": "Lift Riding", "slug": "lift-riding", "start": 8213, "cat": "progression"},
            # Learning Beginner Turns
            {"title": "Skidded Traverses", "slug": "skidded-traverses", "start": 8332, "cat": "progression"},
            {"title": "Steered Traverses (Garlands)", "slug": "steered-traverses-garlands", "start": 8440, "cat": "progression"},
            {"title": "C-Turns", "slug": "c-turns", "start": 8604, "cat": "progression"},
            {"title": "Linking Beginner Turns", "slug": "linking-beginner-turns", "start": 8720, "cat": "progression"},
            {"title": "Intro to Turn Size & Shape", "slug": "intro-to-turn-size-and-shape", "start": 8898, "cat": "progression"},
        ],
    },
    "d": {
        "title": "Teaching Intermediate Snowboarders",
        "dir": "d-intermediate",
        "topics": [
            # Exploring Intermediate Turns
            {"title": "Active Stance & Blending Movements", "slug": "active-stance-and-blending-movements", "start": 9091, "cat": "technique"},
            {"title": "Exploring New Terrain & Early Edging", "slug": "exploring-new-terrain-and-early-edging", "start": 9169, "cat": "technique"},
            {"title": "Switch Riding", "slug": "switch-riding", "start": 9303, "cat": "technique"},
            # Exploring Freeriding
            {"title": "Intro to Off-Piste with Passive Absorption", "slug": "intro-to-off-piste-passive-absorption", "start": 9432, "cat": "technique"},
            {"title": "Developing Freeriding with Active Absorption", "slug": "developing-freeriding-active-absorption", "start": 9613, "cat": "technique"},
            # Exploring Carving
            {"title": "Intro to Carving with Angulation", "slug": "intro-to-carving-with-angulation", "start": 9748, "cat": "technique"},
            {"title": "Developing Carving with Increased Edge Performance", "slug": "developing-carving-edge-performance", "start": 9957, "cat": "technique"},
            # Exploring Freestyle
            {"title": "Ollies, Nollies & Presses", "slug": "ollies-nollies-and-presses", "start": 10213, "cat": "freestyle"},
            {"title": "Frontside 180s", "slug": "frontside-180s", "start": 10378, "cat": "freestyle"},
            {"title": "Backside 180s", "slug": "backside-180s", "start": 10596, "cat": "freestyle"},
            {"title": "Intro to & Exploring Boxes", "slug": "intro-to-and-exploring-boxes", "start": 10678, "cat": "freestyle"},
            {"title": "Intro to & Exploring Jumps", "slug": "intro-to-and-exploring-jumps", "start": 10836, "cat": "freestyle"},
        ],
    },
    "e": {
        "title": "Teaching Advanced Snowboarders",
        "dir": "e-advanced",
        "topics": [
            # Mastering Advanced Turns
            {"title": "The Stance Scale", "slug": "the-stance-scale", "start": 11035, "cat": "technique"},
            {"title": "Flexed Edge Change Turns", "slug": "flexed-edge-change-turns", "start": 11087, "cat": "technique"},
            {"title": "Retraction Turns", "slug": "retraction-turns", "start": 11248, "cat": "technique"},
            {"title": "Terrain Unweighted Turns", "slug": "terrain-unweighted-turns", "start": 11311, "cat": "technique"},
            # Advanced Freeriding
            {"title": "Riding Steeps & Chutes", "slug": "riding-steeps-and-chutes", "start": 11473, "cat": "technique"},
            {"title": "Riding Bumps", "slug": "riding-bumps", "start": 11566, "cat": "technique"},
            {"title": "Riding Gullies", "slug": "riding-gullies", "start": 11701, "cat": "technique"},
            {"title": "Riding Drops, Spines & Windlips", "slug": "riding-drops-spines-windlips", "start": 11818, "cat": "technique"},
            {"title": "Riding Trees", "slug": "riding-trees", "start": 11936, "cat": "technique"},
            {"title": "Situational Freeriding", "slug": "situational-freeriding", "start": 12019, "cat": "technique"},
            # Advanced Carving
            {"title": "Advanced Angulation", "slug": "advanced-angulation", "start": 12224, "cat": "technique"},
            {"title": "All Terrain & Creative Carving", "slug": "all-terrain-and-creative-carving", "start": 12333, "cat": "technique"},
            {"title": "High Performance Carving", "slug": "high-performance-carving", "start": 12475, "cat": "technique"},
            # Advanced Freestyle
            {"title": "All Mountain Butters", "slug": "all-mountain-butters", "start": 12650, "cat": "freestyle"},
            {"title": "All Mountain Frontside & Backside 360s", "slug": "all-mountain-360s", "start": 12732, "cat": "freestyle"},
            {"title": "All Mountain Hardways Spins", "slug": "all-mountain-hardways-spins", "start": 12852, "cat": "freestyle"},
            {"title": "Park Jumps - Advanced Aerial Awareness", "slug": "park-jumps-advanced-aerial-awareness", "start": 12922, "cat": "freestyle"},
            {"title": "Park Jumps - 180s", "slug": "park-jumps-180s", "start": 13173, "cat": "freestyle"},
            {"title": "Park Jumps - 360s", "slug": "park-jumps-360s", "start": 13325, "cat": "freestyle"},
            {"title": "Boxes & Rails - Boardslides", "slug": "boxes-and-rails-boardslides", "start": 13487, "cat": "freestyle"},
            {"title": "Boxes & Rails - Presses", "slug": "boxes-and-rails-presses", "start": 13649, "cat": "freestyle"},
            {"title": "Boxes & Rails - Side Entries", "slug": "boxes-and-rails-side-entries", "start": 13796, "cat": "freestyle"},
            {"title": "Boxes & Rails - 50-50 with Spins In & Out", "slug": "boxes-and-rails-50-50-with-spins", "start": 13950, "cat": "freestyle"},
            {"title": "Intro to Halfpipe & Transition", "slug": "intro-to-halfpipe-and-transition", "start": 14095, "cat": "freestyle"},
            # Competitive Snowboarding
            {"title": "Slopestyle", "slug": "slopestyle", "start": 14233, "cat": "freestyle"},
            {"title": "Halfpipe & Transition", "slug": "halfpipe-and-transition", "start": 14373, "cat": "freestyle"},
            {"title": "Snowboard Cross & Banked Slalom", "slug": "snowboard-cross-and-banked-slalom", "start": 14570, "cat": "freestyle"},
            {"title": "Freeride Contests", "slug": "freeride-contests", "start": 14710, "cat": "freestyle"},
        ],
    },
    "f": {
        "title": "Equipment & Reference",
        "dir": "f-equipment-and-reference",
        "topics": [
            # Snowboard Equipment
            {"title": "Snowboard Length & Width", "slug": "snowboard-length-and-width", "start": 14863, "cat": "equipment"},
            {"title": "Snowboard Flex & Shape", "slug": "snowboard-flex-and-shape", "start": 14923, "cat": "equipment"},
            {"title": "Side-Cut & Edges", "slug": "side-cut-and-edges", "start": 15092, "cat": "equipment"},
            {"title": "Snowboard Boots & Bindings", "slug": "snowboard-boots-and-bindings", "start": 15151, "cat": "equipment"},
            {"title": "Binding Placement & Stance Setup", "slug": "binding-placement-and-stance-setup", "start": 15204, "cat": "equipment"},
            # Maori Translations
            {"title": "Maori Introductions & Greetings", "slug": "maori-introductions-and-greetings", "start": 15314, "cat": "general"},
            {"title": "Maori Numbers & Useful Terms", "slug": "maori-numbers-and-useful-terms", "start": 15376, "cat": "general"},
            {"title": "Maori Snowboard & Body Parts", "slug": "maori-snowboard-and-body-parts", "start": 15476, "cat": "general"},
            # Glossary
            {"title": "Snowboard Jargon Glossary", "slug": "snowboard-jargon-glossary", "start": 15536, "cat": "general"},
            {"title": "Tricktionary", "slug": "tricktionary", "start": 16284, "cat": "freestyle"},
        ],
    },
}


def read_source():
    """Read the source markdown file."""
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        return f.readlines()


def preprocess_content(lines: list[str]) -> list[str]:
    """Apply preprocessing rules to remove VLM image descriptions.

    Strategy: line-by-line pattern filtering rather than state machine,
    to avoid accidentally swallowing manual content that appears after VLM blocks.

    VLM descriptions use patterns that the manual never uses:
    - ### and #### headers (manual only uses # H1)
    - > blockquotes
    - Numbered analysis items: "1. **Technique...**"
    - Bold key-value bullets: "- **Key**: Value"
    - Image links: ![...](images/...)
    - VLM concluding phrases: "This image...", "Overall, the image..."
    """
    # First pass: handle multi-line image links by joining them
    joined = []
    in_img_link = False
    img_buffer = []
    for line in lines:
        stripped = line.strip()
        if not in_img_link:
            if stripped.startswith('![') and '](images/' not in stripped and '](http' not in stripped:
                in_img_link = True
                img_buffer = [line]
                continue
            joined.append(line)
        else:
            img_buffer.append(line)
            if '](images/' in stripped or '](http' in stripped:
                # Complete image link — mark as single line for removal
                joined.append('![MULTILINE_IMAGE](images/placeholder)\n')
                in_img_link = False
                img_buffer = []
            elif stripped.startswith('#'):
                # Never finished the image link, this is a header
                # Output the buffered lines and this one
                joined.extend(img_buffer)
                in_img_link = False
                img_buffer = []

    # If still in img link at end, flush
    if img_buffer:
        joined.extend(img_buffer)

    # Second pass: filter VLM-specific lines
    result = []
    for line in joined:
        stripped = line.strip()

        # ── Always remove ──
        # Image links
        if re.match(r'^!\[.*\]\(images/', stripped):
            continue
        # VLM_PROCESSED markers
        if '<!-- VLM_PROCESSED -->' in stripped:
            continue
        # VLM image reference: > **[Image: ...]**
        if re.match(r'^>\s*\*\*\[Image:', stripped):
            continue
        # All blockquote lines (manual doesn't use blockquotes for content)
        if stripped.startswith('>'):
            continue
        # H3 and H4 headers (only VLM uses these; manual uses only H1)
        if re.match(r'^#{2,4}\s', stripped):
            continue
        # Numbered VLM analysis items: "1. **Technique/Skill**"
        if re.match(r'^\d+\.\s+\*\*', stripped):
            continue
        # Bold key-value bullets: "- **Stance Width**: The snowboarder..."
        if re.match(r'^-\s+\*\*[^*]+\*\*\s*:', stripped):
            continue
        # Indented bold key-value: "   - **Key**: Value"
        if re.match(r'^\s+-\s+\*\*[^*]+\*\*\s*:', stripped):
            continue
        # VLM concluding/intro phrases
        if re.match(r'^(This image|This instructional|The image|Overall,|In summary,|The technique being demonstrated|The specific skill being demonstrated)', stripped):
            continue
        # VLM descriptive paragraphs about what's shown in photos
        if re.match(r'^The snowboarder(s)?\s+(is|are)\s+(executing|performing|demonstrating|shown|depicted|in the midst)', stripped):
            continue
        if re.match(r'^The rider(s)?\s+(is|are)\s+(executing|performing|demonstrating|shown|depicted)', stripped):
            continue
        # VLM residual annotation lines (indented or not)
        if re.search(r'no visible labels.*arrows.*diagrams', stripped, re.IGNORECASE):
            continue
        if re.search(r'no (additional )?annotations.*labels', stripped, re.IGNORECASE):
            continue
        # VLM section separator: lone "---" that appears in sequence
        # (manual uses --- too, but not in isolation between blank lines)
        if stripped == '---':
            continue

        result.append(line)

    # Compress 3+ consecutive blank lines to 2
    compressed = []
    blank_count = 0
    for line in result:
        if line.strip() == '':
            blank_count += 1
            if blank_count <= 2:
                compressed.append(line)
        else:
            blank_count = 0
            compressed.append(line)

    return compressed


def get_topic_end(section_key: str, topic_idx: int, all_lines_count: int) -> int:
    """Determine where a topic ends (line number, exclusive)."""
    section = SECTIONS[section_key]
    topics = section["topics"]

    if topic_idx < len(topics) - 1:
        # End at the start of the next topic in same section
        return topics[topic_idx + 1]["start"]

    # Last topic in section - find start of next section
    section_keys = list(SECTIONS.keys())
    current_idx = section_keys.index(section_key)

    if current_idx < len(section_keys) - 1:
        next_section = SECTIONS[section_keys[current_idx + 1]]
        return next_section["topics"][0]["start"]

    # Last topic of last section
    return all_lines_count + 1


def extract_topic_content(lines: list[str], start: int, end: int) -> str:
    """Extract and preprocess content for a topic (1-indexed lines)."""
    # Convert to 0-indexed
    topic_lines = lines[start - 1: end - 1]
    processed = preprocess_content(topic_lines)

    # Strip leading/trailing blank lines
    while processed and processed[0].strip() == '':
        processed.pop(0)
    while processed and processed[-1].strip() == '':
        processed.pop()

    return ''.join(processed)


def make_frontmatter(topic: dict, section_key: str) -> str:
    """Generate YAML frontmatter for a topic file."""
    name = f"sbinz-{section_key}-{topic['slug']}"
    return f"""---
name: {name}
source_document: SBINZ-manual-FullPDF-30 may 2025.pdf
source_organization: SBINZ
language: en
description: "{topic['title']} - SBINZ snowboard instruction knowledge"
tags: [sbinz, section-{section_key}, {topic['cat']}]
---
"""


def build_index_json() -> dict:
    """Build the _index.json structure."""
    index = {
        "title": "SBINZ Snowboard Manual - Full Knowledge Base",
        "version": "May 2025",
        "source": "Snowboard Instruction New Zealand",
        "generated_at": datetime.now().isoformat(),
        "total_topics": sum(len(s["topics"]) for s in SECTIONS.values()),
        "sections": {},
    }

    for key, section in SECTIONS.items():
        topics_list = []
        for t in section["topics"]:
            topics_list.append({
                "slug": t["slug"],
                "title": t["title"],
                "tags": ["sbinz", f"section-{key}", t["cat"]],
            })
        index["sections"][key] = {
            "title": section["title"],
            "path": f"sections/{section['dir']}/",
            "topic_count": len(topics_list),
            "topics": topics_list,
        }

    return index


def build_index_md() -> str:
    """Build the _index.md content."""
    total = sum(len(s["topics"]) for s in SECTIONS.values())
    lines = [
        "# SBINZ Snowboard Manual - Full Knowledge Base\n",
        "\n",
        "**Source:** Snowboard Instruction New Zealand\n",
        "**Version:** May 2025\n",
        f"**Total Topics:** {total}\n",
        "\n",
        "## How to Use\n",
        "\n",
        "This knowledge base contains the **complete content** from the SBINZ snowboard instruction manual,\n",
        "structured into searchable topic files with full original text preserved.\n",
        "\n",
        "**To search:** `grep -ri \"keyword\" knowledge/sbinz-full/`\n",
        "**To browse:** Check section indexes below\n",
        "\n",
        "---\n",
        "\n",
    ]

    section_names = {
        "a": "Section A: Creating a Learning Environment",
        "b": "Section B: Technical Understanding",
        "c": "Section C: Teaching Beginner Snowboarders",
        "d": "Section D: Teaching Intermediate Snowboarders",
        "e": "Section E: Teaching Advanced Snowboarders",
        "f": "Section F: Equipment & Reference",
    }

    for key, section in SECTIONS.items():
        lines.append(f"## {section_names.get(key, section['title'])}\n")
        lines.append("\n")
        lines.append(f"**Path:** `sections/{section['dir']}/`\n")
        lines.append(f"**Topics:** {len(section['topics'])}\n")
        lines.append("\n")
        for t in section["topics"]:
            lines.append(
                f"- [{t['title']}](sections/{section['dir']}/{t['slug']}.md)\n"
            )
        lines.append("\n")

    return ''.join(lines)


def main():
    print(f"Reading source: {SOURCE_FILE}")
    lines = read_source()
    total_lines = len(lines)
    print(f"Total lines: {total_lines}")

    # Create directory structure
    for section in SECTIONS.values():
        section_dir = OUTPUT_DIR / "sections" / section["dir"]
        section_dir.mkdir(parents=True, exist_ok=True)

    # Process each section and topic
    total_topics = 0
    total_output_lines = 0

    for section_key, section in SECTIONS.items():
        section_dir = OUTPUT_DIR / "sections" / section["dir"]
        print(f"\n{'='*60}")
        print(f"Section {section_key.upper()}: {section['title']}")
        print(f"{'='*60}")

        for i, topic in enumerate(section["topics"]):
            end = get_topic_end(section_key, i, total_lines)
            content = extract_topic_content(lines, topic["start"], end)
            frontmatter = make_frontmatter(topic, section_key)

            full_content = frontmatter + "\n" + content + "\n"
            output_lines = full_content.count('\n')
            total_output_lines += output_lines

            output_path = section_dir / f"{topic['slug']}.md"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_content)

            total_topics += 1
            content_lines = content.count('\n')
            print(f"  [{topic['start']:5d}-{end:5d}] {topic['slug']}.md ({content_lines} lines)")

    # Build indexes
    print(f"\n{'='*60}")
    print("Building indexes...")

    index_json = build_index_json()
    with open(OUTPUT_DIR / "_index.json", 'w', encoding='utf-8') as f:
        json.dump(index_json, f, indent=2, ensure_ascii=False)
    print(f"  _index.json written")

    index_md = build_index_md()
    with open(OUTPUT_DIR / "_index.md", 'w', encoding='utf-8') as f:
        f.write(index_md)
    print(f"  _index.md written")

    # Summary
    print(f"\n{'='*60}")
    print(f"COMPLETE")
    print(f"  Total topics: {total_topics}")
    print(f"  Total output lines: {total_output_lines}")
    print(f"  Output directory: {OUTPUT_DIR}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
