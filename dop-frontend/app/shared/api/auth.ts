import { apiRequest } from "./client";
import type { AuthUser, LoginPayload, LoginResponse, TokenResponse } from "./types";

function createJsonRequestInit(method: string, body?: unknown, accessToken?: string): RequestInit {
    const headers = new Headers();

    if (body !== undefined) {
        headers.set("Content-Type", "application/json");
    }

    if (accessToken) {
        headers.set("Authorization", `Bearer ${accessToken}`);
    }

    return {
        method,
        headers,
        body: body !== undefined ? JSON.stringify(body) : undefined,
    };
}

export function login(payload: LoginPayload): Promise<LoginResponse> {
    return apiRequest<LoginResponse>("/auth/login", createJsonRequestInit("POST", payload));
}

export function refreshAccessToken(): Promise<TokenResponse> {
    return apiRequest<TokenResponse>("/auth/refresh", { method: "POST" });
}

export function logout(): Promise<void> {
    return apiRequest<void>("/auth/logout", { method: "POST" });
}

export function getMe(accessToken: string): Promise<AuthUser> {
    return apiRequest<AuthUser>("/auth/me", createJsonRequestInit("GET", undefined, accessToken));
}
