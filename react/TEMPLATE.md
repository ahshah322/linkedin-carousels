# React carousel template (light design)

Based on the Logging reference carousel. One fixed pattern for every React post.
Preview board: `react/template-board.png`. Builder: `python3 tools/build_light.py react/specs/<topic>.json react/<topic>.pdf`.

## Canvas
- 1080 x 1350 px (4:5), exported as one PDF. Maximum 6 slides.
- A topic that fits on one page becomes a single image in the same style.

## Every slide
- Tag pill with hexagon badge, top-left (e.g. "JavaScript · ES6+").
- Two-line headline (line 1 navy, line 2 blue), short blue underline, one-line subtitle.
- Illustration top-right (clipboard, laptop, flow).
- Navy bottom bar: Save this post / Repost to help / Follow for more.

## Slide roles
1. Cover / overview: insight callout and numbered topic cards.
2. to 5. Concept slides: 2 to 3 sections (coloured label, 2-line explanation, dark code block), then a Key Point bar. Optional result line, flow cards or compare rows.
6. Last slide: combined example, "Your turn" question, profile card (photo, name, title, LinkedIn and GitHub @ahshah322).

## Colours
Navy #0A1B4F, blue #1E40E8, ink #14214F, code background #0E1B3D.
Card tints: blue #EEF3FF, green #EAF7EF, orange #FFF3E2, purple #F1EEFC, red #FDEDED.
Label pills use darker solid colours with white text.

## Type
- Nunito: headline 800 (78 to 96 px), subtitle 600 (29 px), body 24 to 27 px, card text 25 to 29 px.
- DM Mono: code 23 px, max 43 characters per line, max 5 lines per block.
- Code colours: keywords purple, strings orange, calls cyan, comments green, JSX tags blue.

## Post text
Short hook, what the slides cover, one question, 4 hashtags. Approved by Ali before anything is queued in Buffer.
