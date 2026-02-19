'use client';

import { useEffect, useState } from 'react';
import { Moon, Sun } from 'lucide-react';

export default function ThemeToggle({ style }: { style?: React.CSSProperties }) {
    const [theme, setTheme] = useState('dark');
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
        const saved = localStorage.getItem('theme') || 'dark';
        setTheme(saved);
        document.documentElement.setAttribute('data-theme', saved);
    }, []);

    const toggle = () => {
        const next = theme === 'dark' ? 'light' : 'dark';
        setTheme(next);
        localStorage.setItem('theme', next);
        document.documentElement.setAttribute('data-theme', next);
    };

    if (!mounted) return null;

    return (
        <button
            onClick={toggle}
            className="btn btn-secondary btn-sm"
            title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            style={{ display: 'flex', alignItems: 'center', gap: '8px', ...style }}
        >
            {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
            <span style={{ fontSize: '13px' }}>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
        </button>
    );
}
