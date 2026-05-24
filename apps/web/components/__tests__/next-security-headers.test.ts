import { describe, expect, it } from "vitest";
import nextConfig from "../../next.config";

describe("Next security headers", () => {
  it("declares hardened production headers", async () => {
    const configuredHeaders = await nextConfig.headers?.();
    const headers = Object.fromEntries(
      configuredHeaders?.[0]?.headers.map((header) => [header.key, header.value]) ?? []
    );

    expect(configuredHeaders?.[0]?.source).toBe("/(.*)");
    expect(headers["X-Frame-Options"]).toBe("DENY");
    expect(headers["X-Content-Type-Options"]).toBe("nosniff");
    expect(headers["Referrer-Policy"]).toBe("no-referrer");
    expect(headers["Permissions-Policy"]).toContain("camera=()");
    expect(headers["Content-Security-Policy"]).toContain("default-src 'self'");
    expect(headers["Content-Security-Policy"]).toContain("frame-ancestors 'none'");
    expect(headers["Strict-Transport-Security"]).toContain("includeSubDomains");
  });
});
