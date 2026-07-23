#!/usr/bin/env bash
# MANAGED FILE - Updates pulled from template. See MANAGED_FILES.md
#
# Idempotently inject the MANAGED FILE marker into a managed file.
#
# Usage: inject_managed_prefix.sh <path>
#
# Picks comment syntax based on the file kind and inserts the marker on the
# appropriate line. If a previous-format marker is present (e.g. one carrying
# the "Do not edit" wording), it is replaced in place. Files already at the
# current marker, plus a small skip list (self-documenting / machine-only /
# examples), are left untouched.
set -eu

PREFIX_TEXT="MANAGED FILE - Updates pulled from template. See MANAGED_FILES.md"

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <path>" >&2
    exit 64
fi

file="$1"

if [ ! -f "$file" ]; then
    exit 0
fi

case "$file" in
    MANAGED_FILES.md|.template-sync-sha|.upstream-sync-sha|.template-version)
        exit 0
        ;;
    src/examples/*|tests/examples/*)
        exit 0
        ;;
esac

# Pick the comment-syntax variant for this file kind.
first_line=$(head -n 1 "$file" 2>/dev/null || true)
new_marker=""
case "$file" in
    .claude/skills/*/SKILL.md|*.md)
        new_marker="<!-- $PREFIX_TEXT -->"
        ;;
    *.py|*.yml|*.yaml|*.sh|*.toml|*.cfg|*.ini|*.config|Makefile|*/Makefile)
        new_marker="# $PREFIX_TEXT"
        ;;
    *)
        exit 0
        ;;
esac

# If an existing MANAGED FILE line is present in the header, normalise it in
# place — handles wording changes (e.g. dropping "Do not edit") without
# stacking duplicate markers.
existing_lineno=$(head -n 20 "$file" | grep -nF "MANAGED FILE" | head -n 1 | cut -d: -f1 || true)
if [ -n "$existing_lineno" ]; then
    existing_line=$(sed -n "${existing_lineno}p" "$file")
    if [ "$existing_line" = "$new_marker" ]; then
        exit 0
    fi
    awk -v ln="$existing_lineno" -v new="$new_marker" '
        NR == ln { print new; next }
        { print }
    ' "$file" > "$file.tmp"
    cat "$file.tmp" > "$file" && rm "$file.tmp"
    exit 0
fi

prepend_line() {
    line="$1"
    target="$2"
    {
        printf '%s\n' "$line"
        cat "$target"
    } > "$target.tmp"
    cat "$target.tmp" > "$target" && rm "$target.tmp"
}

insert_after_first_line() {
    line="$1"
    target="$2"
    awk -v inject="$line" 'NR == 1 { print; print inject; next } { print }' \
        "$target" > "$target.tmp"
    cat "$target.tmp" > "$target" && rm "$target.tmp"
}

insert_after_second_marker() {
    line="$1"
    marker="$2"
    target="$3"
    awk -v inject="$line" -v marker="$marker" '
        BEGIN { count = 0; done = 0 }
        {
            print
            if (!done && $0 == marker) {
                count++
                if (count == 2) {
                    print inject
                    done = 1
                }
            }
        }
    ' "$target" > "$target.tmp"
    cat "$target.tmp" > "$target" && rm "$target.tmp"
}

case "$file" in
    .claude/skills/*/SKILL.md)
        if [ "$first_line" = "---" ]; then
            insert_after_second_marker "$new_marker" "---" "$file"
        else
            prepend_line "$new_marker" "$file"
        fi
        ;;
    *.md)
        prepend_line "$new_marker" "$file"
        ;;
    *.py|*.yml|*.yaml|*.sh|*.toml|*.cfg|*.ini|*.config|Makefile|*/Makefile)
        case "$first_line" in
            '#!'*)
                insert_after_first_line "$new_marker" "$file"
                ;;
            *)
                prepend_line "$new_marker" "$file"
                ;;
        esac
        ;;
esac

exit 0
