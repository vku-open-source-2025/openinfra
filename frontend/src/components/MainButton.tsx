import React from 'react';

interface MainButtonProps {
    children: React.ReactNode;
    onClick?: () => void;
}

const MainButton: React.FC<MainButtonProps> = ({ children, onClick }) => {
    return (
        <button
            onClick={onClick}
            className="px-6 py-3 bg-gradient-to-r from-main-start to-main-end text-white font-semibold rounded-lg shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200"
        >
            {children}
        </button>
    );
};

export default MainButton;
