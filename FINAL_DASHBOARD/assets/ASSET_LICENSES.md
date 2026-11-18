# Asset licences and provenance

| Asset | Where it is used | Source | Licence | Notes |
|---|---|---|---|---|
| Stadium hero drawing (SVG, inline in `components/hero.py`) | Executive Overview page, top of the page | Drawn for this project in code | Part of this project (same terms as the dashboard) | No photograph. No team logo, crest, colour scheme or name of any franchise. No external URL. Decorative only. |
| Ground schematic (inline SVG on the Cricket Visuals page) | Cricket Visuals | Drawn for this project | Part of this project | Decorative. Carries no data and no field positions. |
| `assets/style.css` | Every page | Written for this project | Part of this project | Colours: navy, gold and a subtle red accent. |
| `assets/FINAL_RESEARCH_REPORT.pdf` | Download on page 8 | The project's own research report | Part of this project | Unchanged. |
| Player cards | Cricket Visuals, Player cards tab | Initials generated from player names in the research file | Not an image | No player photographs are used or searched for. |

## What was deliberately not used

- No player photographs, team photographs or stadium photographs. Photographs need a licence that was not available for this build, and fabricating or downloading them would breach the brief.
- No external image URLs, so no page depends on a third-party server staying up or allowing hot-linking.
- No Rajasthan Royals (or any other franchise) logo, crest or trademark. The palette is inspired only by general colours and does not imply any affiliation.
- No shot-location, wagon-wheel or pitch-coordinate imagery. The raw data does not hold those positions (see README, section 10).

## If you add a licensed photograph later

1. Keep the file in `assets/` and record the source URL, photographer or rights holder, licence name and date in a new row above.
2. Confirm the licence allows commercial and public use, and whether attribution text is required.
3. Add the attribution text on the page that shows the image.
4. Rebuild the checksums: `python tests\build_manifest.py`.
