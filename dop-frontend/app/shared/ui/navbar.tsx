import { useEffect, useState, type FormEvent } from "react";
import { NavLink } from "react-router";

import { useAuth } from "~/shared/auth/auth-context";
import "./navbar.css";

const navItems = [
    { label: "Главная", to: "/" },
    { label: "Наши\nсотрудники", to: "/employees" },
    { label: "События", to: "/events" },
    { label: "Календарь", to: "/events-calendar", authOnly: true },
];

export function Navbar() {
    const {
        errorMessage,
        isAdmin,
        isAuthenticated,
        loginWithPassword,
        logoutUser,
        status,
        user,
    } = useAuth();
    const [isLoginOpen, setIsLoginOpen] = useState(false);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    const closeMobileMenu = () => {
        setIsMobileMenuOpen(false);
    };

    useEffect(() => {
        if (isAuthenticated) {
            setIsLoginOpen(false);
            setPassword("");
        }
    }, [isAuthenticated]);

    const visibleNavItems = navItems.filter((item) => !item.authOnly || isAuthenticated);

    async function handleSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setIsSubmitting(true);

        try {
            await loginWithPassword({ username, password });
            setPassword("");
        } finally {
            setIsSubmitting(false);
        }
    }

    async function handleLogout() {
        setIsSubmitting(true);

        try {
            await logoutUser();
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <header className="navbar">
            <nav className="navbar__inner">
                <button
                    type="button"
                    className="navbar__burger"
                    onClick={() => setIsMobileMenuOpen((prev) => !prev)}
                    aria-label="Открыть меню"
                    aria-expanded={isMobileMenuOpen}
                >
                    <span />
                    <span />
                    <span />
                </button>

                <div className="navbar__links">
                    {visibleNavItems.map((item) => (
                        <NavLink
                            key={item.to}
                            to={item.to}
                            className={({ isActive }) =>
                                isActive ? "navbar__link active" : "navbar__link"
                            }
                        >
                            {item.label.split("\n").map((line) => (
                                <span key={line}>{line}</span>
                            ))}
                        </NavLink>
                    ))}
                </div>

                <div className="navbar__login-wrapper">
                    {status === "loading" ? (
                        <span className="navbar__session-text">Проверка сессии...</span>
                    ) : isAuthenticated && user ? (
                        <div className="navbar__session">
                            <div className="navbar__session-text">
                                <strong>{user.username}</strong>
                                <span>{isAdmin ? "Администратор" : user.role}</span>
                            </div>
                            <button
                                type="button"
                                className="navbar__login-button"
                                onClick={handleLogout}
                                disabled={isSubmitting}
                            >
                                Выйти
                            </button>
                        </div>
                    ) : (
                        <>
                            <button
                                type="button"
                                className="navbar__login-button"
                                onClick={() => setIsLoginOpen((prev) => !prev)}
                            >
                                Есть аккаунт?
                            </button>

                            {isLoginOpen && (
                        <div className="navbar__login-popup">
                            <form className="navbar__login-form" onSubmit={handleSubmit}>
                                <div className="navbar__field">
                                    <label className="navbar__label" htmlFor="username">
                                        Логин
                                    </label>
                                    <input
                                        id="username"
                                        name="username"
                                        type="text"
                                        value={username}
                                        onChange={(event) => setUsername(event.target.value)}
                                        className="navbar__input"
                                        autoComplete="username"
                                        required
                                    />
                                </div>

                                <div className="navbar__field">
                                    <label className="navbar__label" htmlFor="password">
                                        Пароль
                                    </label>
                                    <input
                                        id="password"
                                        name="password"
                                        type="password"
                                        value={password}
                                        onChange={(event) => setPassword(event.target.value)}
                                        className="navbar__input"
                                        autoComplete="current-password"
                                        required
                                    />
                                </div>

                                {errorMessage ? (
                                    <p className="navbar__error">{errorMessage}</p>
                                ) : null}

                                <button type="submit" className="navbar__submit" disabled={isSubmitting}>
                                    Войти
                                </button>
                            </form>
                        </div>
                            )}
                        </>
                    )}
                </div>
            </nav>

            {isMobileMenuOpen && (
                <div className="navbar__mobile-menu">
                    {visibleNavItems.map((item) => (
                        <NavLink
                            key={item.to}
                            to={item.to}
                            onClick={closeMobileMenu}
                            className={({ isActive }) =>
                                isActive ? "navbar__mobile-link active" : "navbar__mobile-link"
                            }
                        >
                            {item.label.replace("\n", " ")}
                        </NavLink>
                    ))}
                </div>
            )}
        </header>
    );
}
