# Test fonts

Golden-image tests use a bundled TrueType font so renders are identical in the
devcontainer and CI.

## DejaVuSans.ttf

- **Source:** DejaVu fonts project (bundled with matplotlib in the devcontainer)
- **License:** Bitstream Vera / DejaVu Fonts License (see below)
- **Usage:** `font_path` for `render_text` golden fixtures only
- **Subset:** ASCII printable range only (U+0020-U+007E) to stay under the
  `check-added-large-files` 500 KB pre-commit limit. Glyph outlines are
  preserved, so renders are identical to the full font.

### Regenerating the subset

If a golden fixture needs glyphs outside ASCII, re-subset the full font
(no project dependency on `fonttools`; install it ephemerally):

```bash
SRC=$(find / -name DejaVuSans.ttf -path '*matplotlib*' 2>/dev/null | head -1)
uv run --with fonttools pyftsubset "$SRC" \
  --unicodes=20-7e \
  --output-file=packages/brother_ptouch_label/tests/assets/DejaVuSans.ttf \
  --no-hinting --desubroutinize
just gen-text-images
```

### License summary

Copyright (c) 2003 by Bitstream, Inc. All Rights Reserved. Bitstream Vera is
a trademark of Bitstream, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy of
the fonts accompanying this license ("Fonts") and associated documentation files
(the "Font Software"), to reproduce and distribute the Font Software, including
without limitation the rights to use, copy, merge, publish, distribute, and/or
sell copies of the Font Software, and to permit persons to whom the Font Software
is furnished to do so, subject to the following conditions:

The above copyright and trademark notices and this permission notice shall be
included in all copies of one or more of the Font Software typefaces.

The Font Software may be modified, altered, or added to, and particular
redistributions of the modified Font Software must carry the above copyright
notice and this permission notice.

Full text: https://dejavu-fonts.github.io/License.html
