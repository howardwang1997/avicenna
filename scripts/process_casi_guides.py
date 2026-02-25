#!/usr/bin/env python3
"""
Process 12 CASI guide files into the HGSI knowledge base.
Steps: Read & Preprocess -> Semantic Split -> Section Assignment -> Output
"""

import re
import os
import yaml

NOTES_DIR = "/Users/howardwang/Desktop/playground/avicenna/notes/CASI_GUIDE"
OUTPUT_DIR = "/Users/howardwang/Desktop/playground/avicenna/knowledge/HGSI/sections"

# ============================================================
# Step 1: Preprocessing functions
# ============================================================

def read_file(filepath):
    """Read file and extract frontmatter + content."""
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    # Extract YAML frontmatter
    fm = {}
    content = text
    if text.startswith('---'):
        parts = text.split('---', 2)
        if len(parts) >= 3:
            try:
                fm = yaml.safe_load(parts[1])
            except:
                fm = {}
            content = parts[2]

    return fm, content


def is_vlm_line(stripped):
    """Check if a line is clearly VLM-generated description content."""
    # Numbered bold items: "1. **Technique/Skill Being Demonstrated**:"
    if re.match(r'^\d+\.\s+\*\*[^*]+\*\*\s*:', stripped):
        return True
    # Dash-bold-colon patterns: "- **Stance Width**: ..."
    if re.match(r'^-\s+\*\*\s*[^*]+\*\*\s*:', stripped):
        return True
    # H3/H4 numbered sections: "### 1. **..."
    if re.match(r'^#{2,4}\s+\d+\.\s+\*\*', stripped):
        return True
    # H3 VLM headings
    if re.match(r'^###\s+', stripped) and any(kw in stripped for kw in [
        'Technique', 'Body Position', 'Movement', 'Upper Body', 'Equipment',
        'Terrain & Env', 'Annotations', 'Summary', 'Design and Functionality',
        '技术', '身体姿势', '运动细节', '上半身', '设备', '地形', '标注', '总结',
        'Context', 'Overall', 'Equipment Details'
    ]):
        return True
    # H4 VLM headings
    if re.match(r'^####\s+', stripped) and any(kw in stripped for kw in [
        'Technique', 'Body Position', 'Movement', 'Upper Body', 'Equipment',
        'Terrain', 'Annotations', 'Design', '技术', '身体'
    ]):
        return True
    # Lines starting with image description patterns
    if stripped.startswith('This image') or stripped.startswith('The image') or stripped.startswith('这张图'):
        return True
    # Overall/Summary lines
    if stripped.startswith('Overall,') or stripped.startswith('In summary,') or stripped.startswith('综上所述'):
        return True
    # "Not applicable" VLM lines
    if stripped.startswith('Not applicable'):
        return True
    # "While not explicitly" patterns
    if stripped.startswith('While not explicitly') or stripped.startswith('While this image'):
        return True
    # Indented VLM bullets with stars
    if re.match(r'^-\s+\*\*[^*]+\*\*\s*$', stripped):
        return True
    # Bullet items with VLM image-analysis keywords
    if re.match(r'^\s*-\s+\*\*', stripped) and any(kw in stripped.lower() for kw in [
        'stance width', 'knee bend', 'weight distribution', 'center of gravity',
        'alignment', 'phase of movement', 'edge engagement', 'turn shape',
        'pressure control', 'hand position', 'arm placement', 'visual focus',
        'body separation', 'binding angles', 'slope angle', 'snow condition',
        'trail marker', 'landmark', 'board position', 'gear adjustment',
        '站姿', '膝盖弯曲', '重心分布', '肩部', '动作阶段', '边缘接触',
        '转弯形状', '压力控制', '手部位置', '手臂', '视觉焦点', '坡度',
    ]):
        return True
    return False


def remove_vlm_content(text):
    """Remove VLM-generated content from the text using a state machine.

    Strategy: When we encounter an image link ![...](images/...), we enter
    a VLM-skip state and skip everything until we hit a line that is clearly
    original content (a heading that's not VLM, a table, or other non-VLM content).
    """
    lines = text.split('\n')
    result = []
    i = 0
    in_vlm_block = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Remove <!-- VLM_PROCESSED --> markers
        if '<!-- VLM_PROCESSED -->' in stripped:
            i += 1
            continue

        # Detect image link start: ![...](images/...)
        # These can span multiple lines (alt text can be very long)
        if stripped.startswith('![') and ('images/' in stripped or 'images/' in ''.join(lines[i:min(i+10, len(lines))])):
            # Skip the image link (may span multiple lines)
            while i < len(lines):
                ln = lines[i].strip()
                if ln.endswith('.jpg)') or ln.endswith('.png)') or ('](' in ln and ln.endswith(')')):
                    i += 1
                    break
                # Single-line image link
                if re.match(r'^!\[.*\]\(.*\)$', ln):
                    i += 1
                    break
                i += 1
            in_vlm_block = True
            continue

        # Blockquotes are always VLM content
        if stripped.startswith('> '):
            i += 1
            in_vlm_block = True  # VLM block continues after blockquotes
            continue

        # If we're in a VLM block, check if this line should be skipped
        if in_vlm_block:
            # Blank lines in VLM blocks are skipped
            if stripped == '':
                i += 1
                continue

            # Isolated --- separators are VLM artifacts
            if stripped == '---':
                i += 1
                continue

            # Check if this is still VLM content
            if is_vlm_line(stripped):
                i += 1
                continue

            # Lines that are clearly VLM paragraph continuations
            # (no markdown structure, talking about images/techniques in VLM style)
            if not stripped.startswith('#') and not stripped.startswith('<table') and not stripped.startswith('|'):
                # Check if it looks like VLM prose (about images, techniques, etc.)
                vlm_keywords = [
                    'the image', 'this image', 'the snowboarder', 'the rider',
                    'the skier', 'the instructor', 'the child',
                    'demonstrates', 'depicting', 'showcas',
                    'effectively illustrate', 'captures a moment',
                    'the photograph', 'in this image', 'from the image',
                    'the background', 'the foreground',
                    '该图', '图中', '图像', '图片', '展示了',
                ]
                lower = stripped.lower()
                if any(kw in lower for kw in vlm_keywords):
                    i += 1
                    continue

                # Check for numbered VLM descriptions without bold
                if re.match(r'^\d+\.\s+\*\*', stripped):
                    i += 1
                    continue

                # Bullet points continuing VLM descriptions
                if stripped.startswith('- ') and any(kw in stripped.lower() for kw in [
                    'stance', 'position', 'technique', 'edge', 'turn',
                    'pressure', 'balance', 'alignment', 'movement',
                    'binding', 'helmet', 'goggles', 'jacket',
                    'snow surface', 'gentle slope', 'well-groomed',
                ]):
                    i += 1
                    continue

            # If we hit a real H1 heading, exit VLM block
            if stripped.startswith('# ') and not stripped.startswith('## ') and not stripped.startswith('### '):
                in_vlm_block = False
                result.append(line)
                i += 1
                continue

            # If we hit an H2+ heading that's NOT a VLM pattern, exit VLM block
            if re.match(r'^#{1,2}\s+', stripped) and not is_vlm_line(stripped):
                in_vlm_block = False
                result.append(line)
                i += 1
                continue

            # If we hit table or other structural content, exit VLM block
            if stripped.startswith('<table') or stripped.startswith('|') or stripped.startswith('$'):
                in_vlm_block = False
                result.append(line)
                i += 1
                continue

            # If the line starts with recognizable content patterns (original text)
            # Check if it's actual teaching content (not VLM)
            content_indicators = [
                'CASI ', 'QuickRide', 'Level ', 'Instructor', 'Candidate',
                'Workshop', 'Teaching', 'Evaluation', 'Students', 'Reference:',
                'When ', 'The CASI', 'Welcome', 'Congratulations',
                'CASI一', 'CASI二', 'CASI三', '课程', '考生', '教练',
                '培训', '评估', '认证', '指导', '学生', '教学',
                'MARKING', 'ASSESSMENT', 'RETEST',
            ]
            if any(stripped.startswith(kw) or kw in stripped[:50] for kw in content_indicators):
                in_vlm_block = False
                result.append(line)
                i += 1
                continue

            # If none of the above, it's likely still VLM content - skip
            # But be conservative: if the line looks like a regular paragraph
            # without VLM indicators and has been going for a while, stop
            i += 1
            continue

        # Normal mode (not in VLM block)
        # Still remove isolated VLM patterns that might appear outside blocks
        if stripped == '---':
            # Only keep --- if it serves as a separator between real content
            prev = result[-1].strip() if result else ''
            if prev == '' or prev.startswith('#'):
                i += 1
                continue

        result.append(line)
        i += 1

    return '\n'.join(result)


def clean_formatting(text):
    """Clean up formatting issues."""
    # Remove trailing whitespace from each line
    lines = text.split('\n')
    lines = [line.rstrip() for line in lines]
    text = '\n'.join(lines)

    # Compress 3+ consecutive blank lines to 2
    text = re.sub(r'\n{4,}', '\n\n\n', text)

    # Remove leading blank lines
    text = text.lstrip('\n')

    # Ensure ends with single newline
    text = text.rstrip('\n') + '\n'

    return text


def preprocess(filepath):
    """Full preprocessing pipeline."""
    fm, content = read_file(filepath)
    content = remove_vlm_content(content)
    content = clean_formatting(content)
    return fm, content


# ============================================================
# Step 2 & 3: File processing definitions
# ============================================================

# Each entry: (source_subdir, target_section, topic_slug, description, tags, language)
# For files that don't need splitting, we list a single entry.
# For files that need splitting, we define the split points.

FILE_CONFIGS = [
    # 1. KIDS_GUIDE -> 05-children-teaching (single file, no split needed)
    {
        'source': 'KIDS_GUIDE/content.md',
        'outputs': [
            {
                'section': '05-children-teaching',
                'slug': 'casi-kids-teaching-guide',
                'description': 'CASI Kids Can Snowboard Teaching Guide - comprehensive guide for teaching children snowboarding including duty of care, communication with parents and children, lesson presentation, age-specific teaching tips, equipment considerations, and toolbox activities',
                'tags': ['hgsi', '05-children-teaching', 'children', 'teaching-theory', 'progression'],
                'language': 'en',
            }
        ]
    },
    # 2. RIP_Instructor_Guide -> 02-lesson-planning
    {
        'source': 'RIP_Instructor_Guide/content.md',
        'outputs': [
            {
                'section': '02-lesson-planning',
                'slug': 'casi-rider-improvement-program',
                'description': 'CASI Rider Improvement Program (RIP) instructor guide - structured lesson program with progress cards, skill stages from Little Rippers through advanced freestyle and freeride stages',
                'tags': ['hgsi', '02-lesson-planning', 'progression', 'teaching-theory'],
                'language': 'en',
            }
        ]
    },
    # 3. course_flow -> 18-certification
    {
        'source': 'course_flow/content.md',
        'outputs': [
            {
                'section': '18-certification',
                'slug': 'casi-course-flow',
                'description': 'CASI certification course flow overview - prerequisites, teaching outcomes, riding outcomes, and standards for all CASI certification levels including Level 1 through Level 4, Park 1, and Park 2',
                'tags': ['hgsi', '18-certification', 'assessment', 'general'],
                'language': 'en',
            }
        ]
    },
    # 4. simple_en -> 19-reference
    {
        'source': 'simple_en/content.md',
        'outputs': [
            {
                'section': '19-reference',
                'slug': 'casi-simple-teaching-tips',
                'description': 'CASI S.I.M.P.L.E. Snowboard Teaching guide - COVID-era teaching tips covering first impressions, lesson planning, lesson delivery, demonstrations, ending lessons, and enjoyment',
                'tags': ['hgsi', '19-reference', 'teaching-theory', 'general'],
                'language': 'en',
            }
        ]
    },
    # 5. LEVEL 2 COURSE GUIDE -> 18-certification
    {
        'source': 'LEVEL 2 COURSE GUIDE 2016-EN/content.md',
        'outputs': [
            {
                'section': '18-certification',
                'slug': 'casi-level2-course-guide',
                'description': 'CASI Level 2 Instructor certification course guide - introduction, agenda, evaluation criteria, marking system, study guides, technical presentations, and candidate evaluation form',
                'tags': ['hgsi', '18-certification', 'assessment', 'teaching-theory'],
                'language': 'en',
            }
        ]
    },
    # 6. LEVEL 3 COURSE GUIDE -> 18-certification
    {
        'source': 'LEVEL 3 COURSE GUIDE 2016-EN/content.md',
        'outputs': [
            {
                'section': '18-certification',
                'slug': 'casi-level3-course-guide',
                'description': 'CASI Level 3 Instructor certification course guide - introduction, agenda, evaluation criteria, advanced teaching and riding standards, technical presentations',
                'tags': ['hgsi', '18-certification', 'assessment', 'technique'],
                'language': 'en',
            }
        ]
    },
    # 7. LEVEL 4 COURSE GUIDE -> 18-certification
    {
        'source': 'LEVEL 4 COURSE GUIDE 2016-EN/content.md',
        'outputs': [
            {
                'section': '18-certification',
                'slug': 'casi-level4-course-guide',
                'description': 'CASI Level 4 Instructor certification course guide - introduction, agenda, exam format, evaluation criteria, advanced teaching and riding standards, workshops',
                'tags': ['hgsi', '18-certification', 'assessment', 'technique'],
                'language': 'en',
            }
        ]
    },
    # 8. PARK 1 COURSE GUIDE -> 18-certification
    {
        'source': 'PARK 1 COURSE GUIDE 2016-EN/content.md',
        'outputs': [
            {
                'section': '18-certification',
                'slug': 'casi-park1-course-guide',
                'description': 'CASI Park Instructor 1 certification course guide - introduction, agenda, evaluation criteria for freestyle teaching and riding, workshops on core competencies and freestyle snowboarding, technical presentations',
                'tags': ['hgsi', '18-certification', 'assessment', 'freestyle'],
                'language': 'en',
            }
        ]
    },
    # 9. park_2_guide -> 18-certification
    {
        'source': 'park_2_guide/content.md',
        'outputs': [
            {
                'section': '18-certification',
                'slug': 'casi-park2-course-guide',
                'description': 'CASI Park Instructor 2 certification course guide - introduction, agenda, evaluation criteria, advanced freestyle teaching and riding standards, technical presentations',
                'tags': ['hgsi', '18-certification', 'assessment', 'freestyle'],
                'language': 'en',
            }
        ]
    },
    # 10. Level 1 Course Guide (Chinese) -> 18-certification (zh)
    {
        'source': 'Level 1 Cours Guide (Chinese)/content.md',
        'outputs': [
            {
                'section': '18-certification',
                'slug': 'casi-level1-course-guide-zh',
                'description': 'CASI Level 1 Instructor certification course guide (bilingual EN/ZH) - introduction, agenda, evaluation criteria, workshops, technical presentations, QuickRide system, and evaluation form',
                'tags': ['hgsi', '18-certification', 'assessment', 'teaching-theory'],
                'language': 'zh',
            }
        ]
    },
    # 11. L2_guide_chinese -> 18-certification (zh)
    {
        'source': 'L2_guide_chinese/content.md',
        'outputs': [
            {
                'section': '18-certification',
                'slug': 'casi-level2-course-guide-zh',
                'description': 'CASI Level 2 Instructor certification course guide (bilingual EN/ZH) - introduction, agenda, evaluation criteria, advanced teaching theory, analysis and improvement, physics and biomechanics, technical presentations',
                'tags': ['hgsi', '18-certification', 'assessment', 'teaching-theory'],
                'language': 'zh',
            }
        ]
    },
    # 12. Quick Ride Guide (Chinese) -> 19-reference (zh)
    {
        'source': 'Quick Ride Guide (Chinese)/content.md',
        'outputs': [
            {
                'section': '19-reference',
                'slug': 'casi-quickride-guide-zh',
                'description': 'CASI QuickRide teaching guide (Chinese) - comprehensive beginner teaching reference including alpine code, equipment setup, riding ability breakdown, skills concept, QuickRide 5-step system, terrain-based teaching, lift usage, children teaching, novice and intermediate skill development, and training cycle',
                'tags': ['hgsi', '19-reference', 'teaching-theory', 'progression', 'children'],
                'language': 'zh',
            }
        ]
    },
]


# ============================================================
# Step 4: Output generation
# ============================================================

def generate_output(section, slug, source_pdf, source_org, language, description, tags, content):
    """Generate the output file with YAML frontmatter."""
    name = f"hgsi-{section}-{slug}"

    # Format tags as YAML array without quotes: [tag1, tag2, tag3]
    tags_str = "[" + ", ".join(tags) + "]"

    frontmatter = f"""---
name: {name}
source_document: {source_pdf}
source_organization: {source_org}
language: {language}
description: "{description}"
tags: {tags_str}
---
"""
    return frontmatter + "\n" + content


def process_file(config):
    """Process a single file configuration."""
    source_path = os.path.join(NOTES_DIR, config['source'])

    if not os.path.exists(source_path):
        print(f"  ERROR: Source file not found: {source_path}")
        return []

    fm, content = preprocess(source_path)
    source_pdf = fm.get('source_pdf', config['source'])
    source_org = fm.get('source_organization', 'CASI')

    created_files = []

    for output_cfg in config['outputs']:
        section = output_cfg['section']
        slug = output_cfg['slug']
        desc = output_cfg['description']
        tags = output_cfg['tags']
        lang = output_cfg['language']

        # Use the full preprocessed content for each output
        output_content = generate_output(
            section, slug, source_pdf, source_org, lang, desc, tags, content
        )

        # Determine output filename
        filename = f"{slug}.md"
        output_path = os.path.join(OUTPUT_DIR, section, filename)

        # Write output
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output_content)

        created_files.append(output_path)
        print(f"  Created: {output_path}")

    return created_files


def main():
    """Main processing loop."""
    all_files = {}
    total = 0

    for i, config in enumerate(FILE_CONFIGS, 1):
        print(f"\n[{i}/12] Processing: {config['source']}")
        files = process_file(config)
        total += len(files)

        for f in files:
            section = f.split('/sections/')[1].split('/')[0]
            if section not in all_files:
                all_files[section] = []
            all_files[section].append(os.path.basename(f))

    # Final summary
    print("\n" + "=" * 60)
    print("PROCESSING COMPLETE")
    print("=" * 60)
    print(f"\nTotal files created: {total}")
    print("\nFiles per section:")
    for section in sorted(all_files.keys()):
        print(f"\n  {section}/")
        for fname in sorted(all_files[section]):
            print(f"    - {fname}")


if __name__ == '__main__':
    main()
