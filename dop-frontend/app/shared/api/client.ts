const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

function joinHeaders(headers?: HeadersInit): Headers {
    const mergedHeaders = new Headers(headers);

    if (!mergedHeaders.has("Accept")) {
        mergedHeaders.set("Accept", "application/json");
    }

    return mergedHeaders;
}

export function buildApiUrl(path: string): string {
    return `${API_BASE_URL}${path}`;
}

export async function apiRequest<T>(
    path: string,
    options?: RequestInit,
): Promise<T> {
    const response = await fetch(buildApiUrl(path), {
        ...options,
        credentials: "include",
        headers: joinHeaders(options?.headers),
    });

    if (!response.ok) {
        const text = await response.text();
        throw new Error(text || `API request failed: ${response.status}`);
    }

    if (response.status === 204) {
        return undefined as T;
    }

    const contentType = response.headers.get("content-type");

    if (contentType?.includes("application/json")) {
        return (await response.json()) as T;
    }

    return undefined as T;
}
