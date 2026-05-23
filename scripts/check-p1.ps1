npm run lint
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

npm run test
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

npm run build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

npm run test:api
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
