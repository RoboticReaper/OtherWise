# OtherWise introduction — GitHub Pages

All three websites are English, static, and ready to upload. They need no package installation, build, API key, or backend. All assets are local and use relative paths, so they also work under a repository subpath.

## Fastest deployment: a dedicated repository

1. Create a GitHub repository, for example `otherwise-intro`.
2. Upload the **contents** of this folder to the repository root. Make sure `index.html`, `styles.css`, `site.js`, `.nojekyll`, and the `assets` folder stay together.
3. Open **Settings → Pages**.
4. Set **Source** to **Deploy from a branch**, choose **main**, choose **/(root)**, and save.
5. GitHub will show the published URL after the Pages deployment finishes.

For a repository named `otherwise-intro`, the URL is `https://YOUR-USERNAME.github.io/otherwise-intro/`.
For a repository named exactly `YOUR-USERNAME.github.io`, it is `https://YOUR-USERNAME.github.io/`.

## Included versions

- `index.html` — The Curiosity Galaxy; dark, animated topic map. Recommended default.
- `studio.html` — The Discovery Studio; light, product-first.
- `field-notes.html` — Field Notes; editorial, story-first.
- `previews.html` — A gallery linking to all three complete versions.

To make another version your default, copy its HTML contents into `index.html`, retaining `styles.css`, `site.js`, and `assets/`. Keep the original version file if you want the preview gallery to keep working.

## Optional: use this existing project repository

GitHub's branch-based Pages publishing accepts the repository root or a `/docs` directory. Upload these files to a dedicated repository to avoid mixing the website with the extension project. If you intentionally use `/docs` in an existing repository, retain any existing documentation and add these site files alongside it, then select `/docs` in Pages settings.

## Content and behavior

- Copy is based on `OtherWise_Pitch.pptx` and the current project README.
- The two matching diagrams were extracted from the supplied pitch deck.
- The interest paths and browser panel are clearly marked as illustrative. The website does not run the recommendation engine.
- Statistics include dated links to their research sources.
- The public project link points to `https://github.com/RoboticReaper/OtherWise`.
- Motion respects the system's reduced-motion setting. Main content remains readable without JavaScript.
- No analytics, external fonts, remote scripts, or data collection are included.
- Automated tests were skipped at the user's request. These files have not been published to GitHub.
