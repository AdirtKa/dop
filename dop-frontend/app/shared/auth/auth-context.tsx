import {
    createContext,
    useContext,
    useEffect,
    useMemo,
    useState,
    type ReactNode,
} from "react";

import { getMe, login, logout, refreshAccessToken } from "~/shared/api/auth";
import type { AuthUser, LoginPayload } from "~/shared/api/types";
import {
    clearStoredAccessToken,
    getStoredAccessToken,
    storeAccessToken,
} from "./auth-storage";

type AuthStatus = "loading" | "authenticated" | "anonymous";

type AuthContextValue = {
    accessToken: string | null;
    errorMessage: string | null;
    isAdmin: boolean;
    isAuthenticated: boolean;
    status: AuthStatus;
    user: AuthUser | null;
    loginWithPassword: (payload: LoginPayload) => Promise<void>;
    logoutUser: () => Promise<void>;
    refreshUserSession: () => Promise<string | null>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

async function resolveUserFromToken(accessToken: string): Promise<AuthUser> {
    return getMe(accessToken);
}

export function AuthProvider({ children }: { children: ReactNode }) {
    const [status, setStatus] = useState<AuthStatus>("loading");
    const [user, setUser] = useState<AuthUser | null>(null);
    const [accessToken, setAccessToken] = useState<string | null>(null);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    useEffect(() => {
        let isMounted = true;

        async function bootstrapAuth() {
            const storedToken = getStoredAccessToken();

            if (storedToken) {
                try {
                    const currentUser = await resolveUserFromToken(storedToken);

                    if (!isMounted) {
                        return;
                    }

                    setAccessToken(storedToken);
                    setUser(currentUser);
                    setStatus("authenticated");
                    return;
                } catch {
                    clearStoredAccessToken();
                }
            }

            try {
                const refreshed = await refreshAccessToken();
                const currentUser = await resolveUserFromToken(refreshed.access_token);

                if (!isMounted) {
                    return;
                }

                storeAccessToken(refreshed.access_token);
                setAccessToken(refreshed.access_token);
                setUser(currentUser);
                setStatus("authenticated");
            } catch {
                if (!isMounted) {
                    return;
                }

                clearStoredAccessToken();
                setAccessToken(null);
                setUser(null);
                setStatus("anonymous");
            }
        }

        bootstrapAuth().catch(() => {
            if (!isMounted) {
                return;
            }

            clearStoredAccessToken();
            setAccessToken(null);
            setUser(null);
            setStatus("anonymous");
        });

        return () => {
            isMounted = false;
        };
    }, []);

    async function loginWithPassword(payload: LoginPayload) {
        setErrorMessage(null);

        try {
            const response = await login(payload);

            storeAccessToken(response.access_token);
            setAccessToken(response.access_token);
            setUser(response.user);
            setStatus("authenticated");
        } catch (error) {
            const message = error instanceof Error ? error.message : "Не удалось выполнить вход";
            setErrorMessage(message);
            throw error;
        }
    }

    async function logoutUser() {
        try {
            await logout();
        } finally {
            clearStoredAccessToken();
            setAccessToken(null);
            setUser(null);
            setStatus("anonymous");
            setErrorMessage(null);
        }
    }

    async function refreshUserSession(): Promise<string | null> {
        try {
            const refreshed = await refreshAccessToken();
            const currentUser = await resolveUserFromToken(refreshed.access_token);

            storeAccessToken(refreshed.access_token);
            setAccessToken(refreshed.access_token);
            setUser(currentUser);
            setStatus("authenticated");
            setErrorMessage(null);

            return refreshed.access_token;
        } catch (error) {
            clearStoredAccessToken();
            setAccessToken(null);
            setUser(null);
            setStatus("anonymous");
            setErrorMessage(error instanceof Error ? error.message : "Сессия истекла");

            return null;
        }
    }

    const value = useMemo<AuthContextValue>(() => ({
        accessToken,
        errorMessage,
        isAdmin: user?.role === "admin",
        isAuthenticated: status === "authenticated",
        status,
        user,
        loginWithPassword,
        logoutUser,
        refreshUserSession,
    }), [accessToken, errorMessage, status, user]);

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
    const context = useContext(AuthContext);

    if (!context) {
        throw new Error("useAuth must be used within AuthProvider");
    }

    return context;
}
