#!/usr/bin/env bash
# Build a résumé PDF from its Markdown source.
# The tooling is tracked here (in the skill); the résumé content lives in the
# repo's resume/ dir, which is git-ignored (private CV — never published).
#
#   .claude/skills/author-resume/build.sh 2025.2.25_CN     # -> resume/2025.2.25_CN.pdf
#
# New version: cp resume/<old>.md resume/<new>.md, edit copy, then run with <new>.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
RESUME="$(cd "$HERE/../../.." && pwd)/resume"
[ -d "$RESUME" ] || { echo "resume dir not found: $RESUME"; exit 1; }

NAME="${1:?usage: build.sh <basename>   e.g. build.sh 2025.2.25_CN}"
NAME="${NAME%.md}"                                     # tolerate a .md suffix
cd "$RESUME"
MD="$NAME.md"; HTML="$NAME.html"; PDF="$NAME.pdf"; RAW="$NAME.raw.pdf"
[ -f "$MD" ] || { echo "no such source: $RESUME/$MD"; exit 1; }

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
[ -x "$CHROME" ] || { echo "Google Chrome not found at $CHROME"; exit 1; }

# ensure Microsoft YaHei is available (Word bundles it) so glyphs + pagination match
DF="/Applications/Microsoft Word.app/Contents/Resources/DFonts"
for f in msyh.ttc msyhbd.ttc; do
  if [ ! -f "$HOME/Library/Fonts/$f" ] && [ -f "$DF/$f" ]; then
    cp "$DF/$f" "$HOME/Library/Fonts/" && echo "installed font: $f"
  fi
done

# md -> html -> pdf -> compress
python3 "$HERE/md2html.py" "$MD" "$HTML"
"$CHROME" --headless=new --disable-gpu --no-pdf-header-footer --print-to-pdf="$RAW" "file://$RESUME/$HTML" 2>/dev/null
# Ghostscript recompresses images only (vector text + links untouched); 200dpi print-grade
gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.5 \
   -dDownsampleColorImages=true -dColorImageResolution=200 -dColorImageDownsampleType=/Bicubic \
   -dDownsampleGrayImages=true  -dGrayImageResolution=200  -dGrayImageDownsampleType=/Bicubic \
   -dAutoFilterColorImages=false -dColorImageFilter=/DCTEncode \
   -dNOPAUSE -dBATCH -dQUIET -sOutputFile="$PDF" "$RAW"
rm -f "$RAW"

PAGES=$(pdfinfo "$PDF" 2>/dev/null | awk '/Pages/{print $2}')
echo "built $RESUME/$PDF  ($(du -h "$PDF" | cut -f1), ${PAGES} pages)"
