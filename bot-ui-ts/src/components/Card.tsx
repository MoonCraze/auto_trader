import React from 'react';

interface CardProps {
    title: string;
    children: React.ReactNode;
    className?: string;
}

const Card: React.FC<CardProps> = ({ title, children, className }) => {
    return (
        // The outer card container is a flex column
        <div className={`bg-gray-800/50 p-4 rounded-lg flex flex-col ${className}`}>
            <h3 className="text-lg font-semibold text-white mb-3 border-b border-gray-700 pb-2 flex-shrink-0">
                {title}
            </h3>
            {/* <<< FIX: This inner container will grow and handle overflow --- */}
            <div className="flex-grow overflow-hidden">
                {children}
            </div>
        </div>
    );
};

export default Card;