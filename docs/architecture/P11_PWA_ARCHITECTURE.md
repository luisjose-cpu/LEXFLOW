# P11 PWA Architecture

## Frontend

P11 adds mobile-first Next.js routes under `/m/*`.

Shared surfaces:

- `MobileClientExperience`
- `MobileLawyerExperience`
- `MobileShell`
- Fixed bottom navigation
- PWA registration component

The current implementation uses deterministic demo data in the web app while the API exposes matching role-specific endpoint contracts.

## Backend

Services:

- `MobileClientService`
- `MobileLawyerService`

Client endpoints reuse the secure client portal scope. Lawyer endpoints require internal legal roles and `cases:read`.

## PWA Assets

- `apps/web/app/manifest.ts`
- `apps/web/public/sw.js`
- `apps/web/public/offline.html`
- `apps/web/components/pwa-register.tsx`

The service worker uses a small cache-first fallback for known mobile shell assets and a network-first strategy for GET requests.

## Future Native Path

The same API contracts can be consumed by the future Expo app. Native work should keep role separation, tenant scoping, and audit behavior from the PWA implementation.
