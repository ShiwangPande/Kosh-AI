'use client';

import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import api from '@/lib/api';
import Cookies from 'js-cookie';

// ── useAuth ─────────────────────────────────────────────────

interface User {
    id: string;
    email: string;
    business_name: string;
    role: string;
    is_active: boolean;
}

export function useAuth() {
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const token = Cookies.get('access_token');
        if (token) {
            api.getMe()
                .then((u: any) => setUser(u))
                .catch((err) => {
                    // Only clear user if strictly unauthorized, not on rate limits
                    if (err.message === 'Unauthorized') {
                        setUser(null);
                    }
                    console.error("Auth check failed:", err.message);
                })
                .finally(() => setLoading(false));
        } else {
            setLoading(false);
        }
    }, []);

    const login = async (email: string, password: string) => {
        await api.login(email, password);
        const u: any = await api.getMe();
        setUser(u);
        return u;
    };

    const logout = () => {
        api.clearTokens();
        setUser(null);
        window.location.href = '/login';
    };

    return { user, loading, login, logout, isAdmin: user?.role === 'admin' };
}

// ── usePaginated ────────────────────────────────────────────

interface PaginatedResult<T> {
    items: T[];
    total: number;
    page: number;
    per_page: number;
    pages: number;
}

export function usePaginated<T>(
    fetcher: (params: Record<string, string>) => Promise<PaginatedResult<T>>,
    initialParams: Record<string, string> = {},
) {
    const [data, setData] = useState<T[]>([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Stablize params to prevent infinite loops if caller passes un-memoized object
    const paramsStr = JSON.stringify(initialParams);
    const params = useMemo(() => JSON.parse(paramsStr), [paramsStr]);

    // Use ref for fetcher to avoid dependency loop
    const fetcherRef = useRef(fetcher);
    useEffect(() => {
        fetcherRef.current = fetcher;
    }, [fetcher]);

    const fetch = useCallback(async (p: number, showLoading: boolean = true) => {
        if (showLoading) setLoading(true);
        setError(null);
        try {
            const result = await fetcherRef.current({ ...params, page: String(p), per_page: '20' });
            setData(result.items);
            setTotal(result.total);
        } catch (e: any) {
            setError(e.message);
        } finally {
            if (showLoading) setLoading(false);
        }
    }, [params]);

    // Initial load and page changes
    useEffect(() => {
        fetch(page, true);
    }, [fetch, page]);

    const refetch = useCallback((silent: boolean = false) => {
        fetch(page, !silent);
    }, [fetch, page]);

    return {
        data,
        total,
        page,
        setPage,
        loading,
        error,
        refetch
    };
}
