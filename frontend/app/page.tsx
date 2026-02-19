'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Cookies from 'js-cookie';

export default function Home() {
    const router = useRouter();

    useEffect(() => {
        const token = Cookies.get('access_token');
        if (token) {
            router.push('/dashboard');
        } else {
            router.push('/login');
        }
    }, [router]);

    return (
        <div className="auth-container">
            <div className="spinner" />
        </div>
    );
}
