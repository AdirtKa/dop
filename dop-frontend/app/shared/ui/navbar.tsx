import { useState } from "react";
import { NavLink } from "react-router";

import "./navbar.css";

const navItems = [
    { label: "Главная", to: "/" },
    { label: "Наши\nсотрудники", to: "/employees" },
    { label: "События", to: "/events" },
];

export function Navbar() {
    const [isLoginOpen, setIsLoginOpen] = useState(false);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    const closeMobileMenu = () => {
        setIsMobileMenuOpen(false);
    };

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
                    {navItems.map((item) => (
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
                    <button
                        type="button"
                        className="navbar__login-button"
                        onClick={() => setIsLoginOpen((prev) => !prev)}
                    >
                        Есть аккаунт?
                    </button>

                    {isLoginOpen && (
                        <div className="navbar__login-popup">
                            <form className="navbar__login-form">
                                <div className="navbar__field">
                                    <label className="navbar__label" htmlFor="username">
                                        Логин
                                    </label>
                                    <input
                                        id="username"
                                        name="username"
                                        type="text"
                                        className="navbar__input"
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
                                        className="navbar__input"
                                    />
                                </div>

                                <button type="submit" className="navbar__submit">
                                    Войти
                                </button>
                            </form>
                        </div>
                    )}
                </div>
            </nav>

            {isMobileMenuOpen && (
                <div className="navbar__mobile-menu">
                    {navItems.map((item) => (
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