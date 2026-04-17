# World Wealth Rank

Zero-backend static leaderboard for ranking companies, countries, and assets in one unified list.

The site can be hosted with plain FTP, while the data can be refreshed automatically by GitHub Actions.

## How The Real Update Flow Works

The browser never stores API keys and never talks to paid data providers directly.

Instead:

1. GitHub Actions runs `scripts/build_data.py` on a schedule.
2. The script fetches fresh data and rebuilds `data/unified-rankings.json`.
3. GitHub commits the updated JSON back into the repo.
4. GitHub Pages can host the latest JSON/site automatically.
5. Optional: the same workflow uploads the static files to your FTP host.

## Current Data Sources

- Countries: World Bank GDP API, no API key required.
- Crypto: CoinGecko markets API, no API key required for this starter usage.
- Companies: Financial Modeling Prep market cap API if `FMP_API_KEY` is configured.
- Metals/assets: manual estimates in `config/entities.json` until you choose a commodity data provider.

If `FMP_API_KEY` is missing, company rows are kept from the existing local JSON so the site still builds.

## Local Files

```text
index.html
assets/
  app.js
  config.js
  fallback-data.js
  styles.css
config/
  entities.json
data/
  unified-rankings.json
scripts/
  build_data.py
  ftp_upload.py
.github/workflows/
  update-data.yml
```

## Preview Locally

You can open `index.html` directly. The page uses `assets/fallback-data.js` for file previews.

For the most accurate test, run:

```bash
python3 -m http.server 8080
```

Then open:

```text
http://localhost:8080
```

## GitHub Setup

1. Create a GitHub repo.
2. Upload/push this project to that repo.
3. In GitHub, go to `Settings -> Pages`.
4. Set the source to `GitHub Actions`.
5. Go to `Settings -> Secrets and variables -> Actions`.
6. Add the secrets you need.

Recommended secrets:

```text
FMP_API_KEY
FTP_HOST
FTP_USER
FTP_PASSWORD
FTP_REMOTE_DIR
```

`FMP_API_KEY` is only needed if you want live company market caps from Financial Modeling Prep.

FTP secrets are only needed if you want GitHub to upload the site to your FTP host automatically.

## Enable FTP Deploy

By default, the workflow builds data and deploys GitHub Pages.

To also upload to FTP:

1. Go to `Settings -> Secrets and variables -> Actions -> Variables`.
2. Add this variable:

```text
ENABLE_FTP_DEPLOY=true
```

3. Add your FTP secrets:

```text
FTP_HOST
FTP_USER
FTP_PASSWORD
FTP_REMOTE_DIR
```

If your FTP account opens directly inside the public website folder, set:

```text
FTP_REMOTE_DIR=/
```

If your host uses a folder like `public_html`, set:

```text
FTP_REMOTE_DIR=/public_html
```

## Use GitHub As JSON Host Only

If you want to keep your site on FTP but load JSON from GitHub, edit `assets/config.js`:

```js
window.WWR_CONFIG = {
  dataUrl: "https://YOUR_USERNAME.github.io/YOUR_REPO/data/unified-rankings.json"
};
```

Then upload only the site files to FTP. The FTP site will read the latest JSON from GitHub Pages.

## Manual Update

Run:

```bash
python3 scripts/build_data.py
```

Then upload:

```text
data/unified-rankings.json
assets/fallback-data.js
```

If you changed design/code, upload the full static site:

```text
index.html
assets/
data/
```
