import { Link } from "@tanstack/react-router";
import { useState, useCallback } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faBars, faXmark } from "@fortawesome/free-solid-svg-icons";

interface NavigationItem {
    label: string;
    to: string;
    search?: Record<string, unknown>;
    isButton?: boolean;
}

const navigationItems: NavigationItem[] = [
    {
        label: "About Us",
        to: "/about",
    },
    {
        label: "API Docs",
        to: "/docs",
    },
    {
        label: "Get Started",
        to: "/map",
        isButton: true,
    },
];

const Header: React.FC = () => {
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    const toggleMobileMenu = useCallback(() => {
        setIsMobileMenuOpen((prev) => !prev);
    }, []);

    const closeMobileMenu = useCallback(() => {
        setIsMobileMenuOpen(false);
    }, []);

    return (
        <header className="fixed z-50 top-0 left-0 h-20 w-full bg-white backdrop-blur-md shadow-sm">
            <div className="flex items-center justify-between h-full px-4 mx-auto max-w-7xl">
                {/* Logo */}
                <div className="flex items-center">
                    <Link to="/" onClick={closeMobileMenu}>
                        <h1 className="ml-2 text-xl font-bold font-montserrat bg-gradient-to-b from-[#4FACFE] from-21% to-[#00F2FE] bg-clip-text text-transparent">
                            OpenInfra
                        </h1>
                    </Link>
                </div>

                {/* Mobile Menu Toggle Button */}
                <button
                    type="button"
                    className="text-xl hidden max-lg:block absolute right-4 text-[#6C7580] cursor-pointer hover:text-[#4FACFE] transition-colors"
                    onClick={toggleMobileMenu}
                    aria-label="Toggle mobile menu"
                    aria-expanded={isMobileMenuOpen}
                >
                    <FontAwesomeIcon icon={faBars} />
                </button>

                {/* Navigation */}
                <nav
                    className={`flex items-center max-lg:flex-col max-lg:absolute max-lg:top-0 max-lg:right-0 max-lg:bg-white max-lg:w-4/5 max-lg:h-screen max-lg:pt-20 max-lg:transition-transform max-lg:duration-500 max-lg:ease-in-out ${
                        isMobileMenuOpen
                            ? "max-lg:translate-x-0"
                            : "max-lg:translate-x-full"
                    }`}
                >
                    {/* Mobile Menu Close Button */}
                    <button
                        type="button"
                        className="absolute top-6 right-6 text-3xl text-[#6C7580] hidden max-lg:block cursor-pointer hover:text-[#4FACFE] transition-colors"
                        onClick={closeMobileMenu}
                        aria-label="Close mobile menu"
                    >
                        <FontAwesomeIcon icon={faXmark} />
                    </button>

                    {/* Navigation Links */}
                    {navigationItems.map((item) => {
                        if (item.isButton) {
                            return (
                                <Link
                                    key={item.to}
                                    to={item.to}
                                    search={item.search}
                                    onClick={closeMobileMenu}
                                    className="ml-8 text-base h-10 bg-linear-to-r from-[#00F2FE] from-21% to-[#4FACFE] px-6 flex items-center rounded-full max-lg:mx-2 max-lg:w-4/5 max-lg:text-xl max-lg:flex-col max-lg:justify-center hover:shadow-lg transition-shadow"
                                >
                                    <span className="text-white font-semibold text-center">
                                        {item.label}
                                    </span>
                                </Link>
                            );
                        }

                        return (
                            <Link
                                key={item.to}
                                to={item.to}
                                onClick={closeMobileMenu}
                                className="ml-8 text-base text-[#6C7580] max-lg:text-lg max-lg:ml-2 max-lg:my-2 hover:text-[#4FACFE] transition-colors"
                            >
                                {item.label}
                            </Link>
                        );
                    })}
                </nav>
            </div>
        </header>
    );
};

export default Header;
