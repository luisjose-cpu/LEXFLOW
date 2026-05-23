# P9 Source Policy

## Rules

- Do not bypass CAPTCHA.
- Do not evade anti-bot controls.
- Do not run aggressive scraping.
- Prefer APIs, RSS, official feeds, licensed datasets, webhook integrations, or manual imports.
- P9 adapters are mock providers only.
- Every source and news action is tenant scoped.
- Favorites and case links are user/tenant scoped.
- Source sync and intelligence mutations are audited.

## Production Requirements

- Add rate limits per provider.
- Add provider terms-of-use review.
- Add allowlisted source configuration.
- Add webhook signature verification when supported.
- Add retention and takedown workflows for licensed content.
