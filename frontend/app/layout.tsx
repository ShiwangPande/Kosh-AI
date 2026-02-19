import type { Metadata } from 'next';
import { Toaster } from 'react-hot-toast';
import './globals.css';

export const metadata: Metadata = {
    title: 'Kosh-AI — Procurement Intelligence',
    description: 'AI-powered procurement intelligence engine for merchants. Upload invoices, compare suppliers, and get smart recommendations.',
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <head>
                <link rel="preconnect" href="https://fonts.googleapis.com" />
                <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
                <link
                    href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap"
                    rel="stylesheet"
                />
            </head>
            <body>
                {children}
                <Toaster
                    position="bottom-right"
                    toastOptions={{
                        className: 'glass-card',
                        style: {
                            background: 'var(--bg-glass)',
                            color: 'var(--text-primary)',
                            border: '1px solid var(--border)',
                            backdropFilter: 'var(--glass-blur)',
                            fontSize: '14px',
                            fontWeight: 500,
                            borderRadius: 'var(--radius-sm)',
                        },
                    }}
                />
            </body>
        </html>
    );
}

