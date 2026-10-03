# GitHub Pages website

Public URL: https://RoboticReaper.github.io/OtherWise/

The supplied introduction website lives in `website/`. Its default page is
`index.html`; the alternate designs remain available at `studio.html` and
`field-notes.html`, with a gallery at `previews.html`. These are static
presentations, not a hosted recommendation backend.

The `Deploy website to GitHub Pages` workflow publishes only `website/` when
that folder or the workflow changes on `master`. It can also be run manually
from GitHub Actions. Pages uses **GitHub Actions** as its publishing source.
No package installation, build step, API keys, or external hosting is needed.

To preview locally from the repository root:

```sh
python3 -m http.server 8765 --directory website
```

Open http://localhost:8765/. Edit the files in `website/`, commit, and push to
`master` to update the public site. Keep asset links relative so they work under
GitHub Pages' `/OtherWise/` path.

The repository README and About website field link to the published site.
GitHub's repository page itself continues to show the source code and README.
