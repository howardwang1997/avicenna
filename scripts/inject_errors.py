#!/usr/bin/env python3
"""
Error injection script: creates knowledge/heygo-snowboard-noisy/ from
knowledge/heygo-snowboard/ with 11 controlled errors (~8% of 131 files).

Generates knowledge/error-manifest.json documenting every injection.
"""

import json
import os
import glob
import shutil

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_KB = os.path.join(ROOT_DIR, "knowledge", "heygo-snowboard")
DST_KB = os.path.join(ROOT_DIR, "knowledge", "heygo-snowboard-noisy")
MANIFEST_PATH = os.path.join(ROOT_DIR, "knowledge", "error-manifest.json")

# ---------------------------------------------------------------------------
# Error specifications
# ---------------------------------------------------------------------------

ERROR_SPECS = [
    # --- factual (4) ---
    {
        "file": "advanced-carving/advanced-angulation.md",
        "error_type": "factual",
        "mode": "replace",
        "search_text": "how the trailing ankle must be actively flexed (pulling the toes up)",
        "replacement_text": "how the trailing ankle must be actively extended (pushing the toes down)",
        "append_after": None,
        "append_text": None,
        "description": "Dorsiflexion changed to plantarflexion for the trailing ankle — subtle single-detail swap that reverses the correct biomechanical cue.",
        "contradiction_target": None,
    },
    {
        "file": "advanced-freestyle/park-jumps-360s.md",
        "error_type": "factual",
        "mode": "replace",
        "search_text": "The upper body and head will lead rotationally into the spin for the first 270 and the lower body will then continue to spin to complete the trick.",
        "replacement_text": "The lower body and hips will lead rotationally into the spin for the first 270 and the upper body will then continue to spin to complete the trick.",
        "append_after": None,
        "append_text": None,
        "description": "Upper/lower body rotational lead order reversed for 360 spin technique.",
        "contradiction_target": None,
    },
    {
        "file": "exploring-carving/intro-carving-angulation.md",
        "error_type": "factual",
        "mode": "replace",
        "search_text": (
            "Heelside angulation should be through the knees and hips mostly; "
            "however, it is also useful to encourage dorsiflexion in the ankles, "
            "gently pulling the toes up inside the boots. "
            "Toeside angulation should be focused in the ankles and knees by "
            "progressively lowering the knees over the toe edge and closing the ankle joint."
        ),
        "replacement_text": (
            "Heelside angulation should be focused in the ankles and knees mostly "
            "by progressively flexing the ankles, gently pulling the toes up inside the boots. "
            "Toeside angulation should be through the knees and hips by "
            "progressively lowering the hips over the toe edge and opening the hip joint."
        ),
        "append_after": None,
        "append_text": None,
        "description": "Heelside and toeside joint emphasis swapped — heelside now incorrectly focuses on ankles/knees, toeside on knees/hips.",
        "contradiction_target": None,
    },
    {
        "file": "advanced-freestyle/halfpipe-transition.md",
        "error_type": "factual",
        "mode": "replace",
        "search_text": "Landing on the uphill edge should be encouraged as riders progress.",
        "replacement_text": "Landing on the downhill edge should be encouraged as riders progress.",
        "append_after": None,
        "append_text": None,
        "description": "uphill edge changed to downhill edge — single word swap that reverses a safety-critical landing cue.",
        "contradiction_target": None,
    },
    # --- contradiction (2) ---
    {
        "file": "biomechanics/joints.md",
        "error_type": "contradiction",
        "mode": "replace",
        "search_text": (
            "This is the key to the success of a snowboarder and their ability to "
            "create lateral movements on their snowboard. It can also aid in "
            "vertical movement, when used with other joints."
        ),
        "replacement_text": (
            "This is the key to the success of a snowboarder and their ability to "
            "create vertical movements on their snowboard. It can also aid in "
            "lateral movement, when used with other joints."
        ),
        "append_after": None,
        "append_text": None,
        "description": "Ankle joint's primary role swapped from lateral to vertical — contradicts movements/four-movement-options.md which identifies ankle as key for lateral movement.",
        "contradiction_target": "movements/four-movement-options.md",
    },
    {
        "file": "teaching-children/negative-behaviours.md",
        "error_type": "contradiction",
        "mode": "replace",
        "search_text": (
            "This tactic is a last resort, only to be used if the child's "
            "behaviour is having a negative effect on other students or it is "
            "becoming a safety issue."
        ),
        "replacement_text": (
            "This tactic should be the first approach tried, as it immediately "
            "establishes clear boundaries and expectations. If the child's "
            "behaviour persists after clear boundaries are set, the instructor "
            "can then move to softer approaches like diversion and investigation."
        ),
        "append_after": None,
        "append_text": None,
        "description": "Ultimatum changed from last resort to first approach — contradicts the same file's ordering that lists Diversion Tactic and Finding the Cause before The Ultimatum.",
        "contradiction_target": "teaching-children/negative-behaviours.md (same file, section ordering)",
    },
    # --- fabricated (2) ---
    {
        "file": "advanced-freestyle/butters.md",
        "error_type": "fabricated",
        "mode": "append",
        "search_text": None,
        "replacement_text": None,
        "append_after": (
            "Achieving smooth butter tricks can be likened to dancing on a "
            "snowboard. Dance moves involve balancing over one leg, spinning "
            "around, transferring weight to the other and also balancing over "
            "both feet when desired. This can help students not only move in a "
            "way beneficial to the trick but also to visualise the moves they "
            "need to make to perform the right dance combo / butter trick."
        ),
        "append_text": (
            "\n\nThe Pendulum Progression Method is particularly effective for "
            "teaching butter tricks. Developed within the NZSIA Freestyle "
            "Teaching Framework (2019), this four-phase approach has the student "
            "swing the board like a pendulum: first with small oscillations in a "
            "nose-tail press pattern, then with increasing amplitude until "
            "rotational momentum is added. Phase 1: Static oscillation on flat "
            "ground, Phase 2: Dynamic oscillation with travel, Phase 3: "
            "Oscillation with edge transition, Phase 4: Full butter integration. "
            "This structured method has been shown to reduce the learning curve "
            "for complex butter combinations by approximately 40%."
        ),
        "description": "Fabricated 'Pendulum Progression Method' and 'NZSIA Freestyle Teaching Framework (2019)' with fake 40% improvement statistic.",
        "contradiction_target": None,
    },
    {
        "file": "competitive-snowboarding/freeride-contests.md",
        "error_type": "fabricated",
        "mode": "append",
        "search_text": None,
        "replacement_text": None,
        "append_after": (
            "- Plan for line options B and C, should a specific feature not be "
            "possible or the athlete loses their line on the face."
        ),
        "append_text": (
            "\n\n# COGNITIVE TERRAIN MAPPING PROTOCOL\n\n"
            "Developed by Dr. Sarah Chen at the NZ Sports Science Institute, "
            "the Cognitive Terrain Mapping Protocol (CTMP) is now standard "
            "practice in elite freeride preparation. Athletes mentally project a "
            "colour-coded overlay onto the venue: green zones for safe turn "
            "areas, amber zones for commitment points, and red zones for no-fall "
            "areas. During the visualisation phase, athletes walk through their "
            "planned line while physically pointing to each zone, which research "
            "has shown improves spatial memory retention by 65% compared to "
            "photo-based planning alone. Include at least three CTMP sessions "
            "before competition day."
        ),
        "description": "Fabricated 'Cognitive Terrain Mapping Protocol (CTMP)', fictional 'Dr. Sarah Chen' at 'NZ Sports Science Institute', and fake 65% improvement statistic.",
        "contradiction_target": None,
    },
    # --- reversed_cause_effect (3) ---
    {
        "file": "advanced-carving/high-performance-carving.md",
        "error_type": "reversed_cause_effect",
        "mode": "replace",
        "search_text": "- Focus on keeping the COM low and inside the turn.",
        "replacement_text": "- Focus on maintaining a higher edge angle, which will naturally draw the COM low and inside the turn.",
        "append_after": None,
        "append_text": None,
        "description": "Cause-effect reversed: originally lowering COM (cause) enables high edge angle (effect); now high edge angle (cause) supposedly draws COM low (effect).",
        "contradiction_target": None,
    },
    {
        "file": "rider-analysis/understanding-cause-effect.md",
        "error_type": "reversed_cause_effect",
        "mode": "replace",
        "search_text": '"Did the rider\'s vertical movement create desirable pressure management or distribution?"',
        "replacement_text": '"Did the desirable pressure in the board prompt the rider\'s vertical movement?"',
        "append_after": None,
        "append_text": None,
        "description": "Cause-effect reversed: originally rider movement (cause) creates board pressure (effect); now board pressure (cause) prompts rider movement (effect).",
        "contradiction_target": None,
    },
    {
        "file": "exploring-freestyle/backside-180s.md",
        "error_type": "reversed_cause_effect",
        "mode": "replace",
        "search_text": (
            "In an active stance, flex down a little and pre-wind by turning the "
            "upper body towards the nose of the board. Now jump up, at the same "
            "time unwinding the upper body to spin 180 degrees."
        ),
        "replacement_text": (
            "In an active stance, jump up to begin the spin, which will naturally "
            "create a pre-wind through the counter-rotation of the body. The "
            "stored rotational energy from this reactive pre-wind drives the full "
            "180 degree rotation."
        ),
        "append_after": None,
        "append_text": None,
        "description": "Cause-effect reversed: originally pre-wind first (cause) then jump/spin (effect); now jump first (cause) supposedly creates reactive pre-wind (effect).",
        "contradiction_target": None,
    },
]

# ---------------------------------------------------------------------------
# Injection logic
# ---------------------------------------------------------------------------


def apply_error(filepath: str, spec: dict) -> tuple[str, str]:
    """Apply a single error to a file. Returns (original_snippet, modified_snippet)."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if spec["mode"] == "replace":
        search = spec["search_text"]
        count = content.count(search)
        assert count == 1, (
            f"Expected exactly 1 match for search_text in {spec['file']}, "
            f"found {count}."
        )
        new_content = content.replace(search, spec["replacement_text"], 1)
        original_snippet = search
        modified_snippet = spec["replacement_text"]

    elif spec["mode"] == "append":
        anchor = spec["append_after"]
        count = content.count(anchor)
        assert count == 1, (
            f"Expected exactly 1 match for append_after anchor in {spec['file']}, "
            f"found {count}."
        )
        insert_pos = content.index(anchor) + len(anchor)
        new_content = content[:insert_pos] + spec["append_text"] + content[insert_pos:]
        original_snippet = anchor
        modified_snippet = anchor + spec["append_text"]

    else:
        raise ValueError(f"Unknown mode: {spec['mode']}")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)

    return original_snippet, modified_snippet


def main():
    # Step 1: Clean slate (idempotent)
    if os.path.exists(DST_KB):
        shutil.rmtree(DST_KB)
        print(f"Removed existing {DST_KB}")

    # Step 2: Copy source KB
    shutil.copytree(SRC_KB, DST_KB)
    md_files = glob.glob(os.path.join(DST_KB, "**", "*.md"), recursive=True)
    print(f"Copied {len(md_files)} .md files to {DST_KB}")

    # Step 3: Apply errors
    errors_manifest = []
    type_counts = {}

    for spec in ERROR_SPECS:
        filepath = os.path.join(DST_KB, spec["file"])
        assert os.path.exists(filepath), f"File not found: {filepath}"

        original, modified = apply_error(filepath, spec)

        type_counts[spec["error_type"]] = type_counts.get(spec["error_type"], 0) + 1

        errors_manifest.append({
            "file_path": spec["file"],
            "error_type": spec["error_type"],
            "original_content": original,
            "modified_content": modified,
            "description": spec["description"],
            "contradiction_target": spec["contradiction_target"],
        })

        print(f"  [{spec['error_type']}] {spec['file']}")

    # Step 4: Write manifest
    manifest = {
        "version": "1.0",
        "source_kb": "knowledge/heygo-snowboard",
        "noisy_kb": "knowledge/heygo-snowboard-noisy",
        "total_files_in_kb": len(md_files),
        "total_files_modified": len(ERROR_SPECS),
        "error_type_counts": type_counts,
        "errors": errors_manifest,
    }

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"\nManifest written to {MANIFEST_PATH}")
    print(f"Total errors injected: {len(ERROR_SPECS)}")
    print(f"Error type counts: {type_counts}")


if __name__ == "__main__":
    main()
