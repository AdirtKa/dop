const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export async function apiRequest<T>(
    path: string,
    options?: RequestInit,
): Promise<T> {
    const url = `${API_BASE_URL}${path}`;

    console.log("Fetch URL:", url);

    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                Accept: "application/json",
                ...options?.headers,
            },
        });

        console.log("Response received:", response);
        console.log("Response status:", response.status);

        if (!response.ok) {
            const text = await response.text();
            console.error("API error body:", text);
            throw new Error(`API request failed: ${response.status}`);
        }

        const data = await response.json();

        console.log("Response data:", data);

        return data as T;
    } catch (error) {
        console.error("Fetch failed:", error);
        throw error;
    }
}