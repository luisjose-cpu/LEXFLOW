# PRODUCTION_CHECKLIST

- [ ] `npm run p14:check` passes in CI.
- [ ] JWT secret replaced and stored in managed secrets.
- [ ] Database uses managed PostgreSQL with backups enabled.
- [ ] S3 bucket has encryption, versioning, and lifecycle policy.
- [ ] Object malware scanning enabled.
- [ ] CORS origins set to production domains only.
- [ ] Edge/WAF rate limits configured.
- [ ] HTTPS enforced.
- [ ] Signed webhooks implemented for real providers.
- [ ] Backup restore drill completed.
- [ ] Logs and metrics exported to monitoring stack.
- [ ] Alert routing tested.
- [ ] External security review completed.
- [ ] Pilot tenant data processing agreement approved.
