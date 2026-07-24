import { afterEach, describe, expect, it, vi } from "vitest";
import { getCurrentUser } from "./authApi";

describe("getCurrentUser", () => {
  afterEach(() => vi.restoreAllMocks());

  it("returns null for an unauthenticated request", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 401 })));
    await expect(getCurrentUser()).resolves.toBeNull();
  });

  it("loads the profile using same-origin cookies", async () => {
    const profile = { id: "user-1", email: "user@example.com" };
    const fetchMock = vi.fn().mockResolvedValue(Response.json(profile));
    vi.stubGlobal("fetch", fetchMock);

    await expect(getCurrentUser()).resolves.toEqual(profile);
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/auth/me",
      expect.objectContaining({ credentials: "same-origin" }),
    );
  });
});
