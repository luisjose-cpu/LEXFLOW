# P1 Validation

## Commands

```bash
npm install
npm run lint
npm run test
npm run build
cd apps/api && python -m pytest
```

Or:

```bash
npm run p1:check
```

## Expected Coverage

- Web compiles with shared packages.
- Web placeholder surfaces render.
- API exposes P1 status endpoints.
- Existing tenant and audit tests remain green.
