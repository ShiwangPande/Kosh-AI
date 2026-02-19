'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { api } from '@/lib/api';
import { Search, Book, Menu, X, ChevronRight, Home } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function DocsLayout({ children }: { children: React.ReactNode }) {
    const [categories, setCategories] = useState<string[]>([]);
    const [articles, setArticles] = useState<any[]>([]);
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<any[]>([]);
    const pathname = usePathname();

    useEffect(() => {
        api.getDocCategories().then(setCategories);
        api.listArticles().then(setArticles);
    }, []);

    useEffect(() => {
        const handler = setTimeout(() => {
            if (searchQuery.length > 2) {
                api.searchDocs(searchQuery).then(setSearchResults);
            } else {
                setSearchResults([]);
            }
        }, 300);
        return () => clearTimeout(handler);
    }, [searchQuery]);

    return (
        <div className="flex h-screen bg-black text-white overflow-hidden">
            {/* Mobile Sidebar Overlay */}
            <AnimatePresence>
                {isSidebarOpen && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-40 bg-black/50 md:hidden"
                        onClick={() => setIsSidebarOpen(false)}
                    />
                )}
            </AnimatePresence>

            {/* Sidebar */}
            <motion.aside
                initial={false}
                animate={{ x: isSidebarOpen ? 0 : '-100%' }}
                transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                className={`
                    fixed md:relative z-50 w-72 h-full border-r border-white/10
                    bg-[#0a0a0f] backdrop-blur-xl flex flex-col
                    ${!isSidebarOpen && 'md:w-0 md:opacity-0 md:overflow-hidden'}
                `}
            >
                <div className="p-6 border-b border-white/10 flex items-center justify-between">
                    <Link href="/dashboard" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
                        <div className="p-2 rounded-lg bg-primary/20">
                            <Book size={20} className="text-primary" />
                        </div>
                        <span className="font-bold text-lg">Kosh Docs</span>
                    </Link>
                    <button onClick={() => setIsSidebarOpen(false)} className="md:hidden p-2 text-gray-400">
                        <X size={20} />
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto p-4 space-y-8">
                    {categories.map(cat => (
                        <div key={cat}>
                            <h3 className="px-3 text-xs font-bold text-gray-500 uppercase tracking-wider mb-2">
                                {cat}
                            </h3>
                            <div className="space-y-1">
                                {articles
                                    .filter(a => a.category === cat)
                                    .map(article => {
                                        const isActive = pathname === `/docs/${article.slug}`;
                                        return (
                                            <Link
                                                key={article.id}
                                                href={`/docs/${article.slug}`}
                                                className={`
                                                    flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-all
                                                    ${isActive
                                                        ? 'bg-primary/20 text-primary font-medium'
                                                        : 'text-gray-400 hover:text-white hover:bg-white/5'}
                                                `}
                                            >
                                                {isActive && <ChevronRight size={14} />}
                                                {article.title}
                                            </Link>
                                        );
                                    })}
                            </div>
                        </div>
                    ))}
                </div>

                <div className="p-4 border-t border-white/10">
                    <Link href="/dashboard" className="flex items-center gap-2 px-4 py-3 rounded-xl bg-white/5 hover:bg-white/10 text-sm font-medium text-gray-300 transition-colors">
                        <Home size={16} /> Back to Dashboard
                    </Link>
                </div>
            </motion.aside>

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-w-0">
                {/* Header */}
                <header className="h-16 border-b border-white/10 flex items-center px-6 gap-4 bg-[#0a0a0f]/80 backdrop-blur-md sticky top-0 z-30">
                    <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="p-2 -ml-2 text-gray-400 hover:text-white rounded-lg hover:bg-white/5">
                        <Menu size={20} />
                    </button>

                    <div className="flex-1 max-w-2xl relative">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={16} />
                            <input
                                type="text"
                                placeholder="Search explicitly ('invoice', 'alert', 'save money')"
                                value={searchQuery}
                                onChange={e => setSearchQuery(e.target.value)}
                                className="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
                            />
                        </div>

                        {/* Search Results Dropdown */}
                        <AnimatePresence>
                            {searchResults.length > 0 && (
                                <motion.div
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: 10 }}
                                    className="absolute top-full left-0 right-0 mt-2 bg-[#1a1a20] border border-white/10 rounded-xl shadow-2xl overflow-hidden z-50"
                                >
                                    {searchResults.map(result => (
                                        <Link
                                            key={result.id}
                                            href={`/docs/${result.slug}`}
                                            onClick={() => { setSearchQuery(''); setSearchResults([]); }}
                                            className="block px-4 py-3 hover:bg-white/5 border-b border-white/5 last:border-0 transition-colors"
                                        >
                                            <div className="font-medium text-white text-sm">{result.title}</div>
                                            <div className="text-xs text-gray-500 line-clamp-1">{result.summary}</div>
                                        </Link>
                                    ))}
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                </header>

                {/* Page Content */}
                <main className="flex-1 overflow-y-auto p-6 md:p-12 relative">
                    <div className="max-w-3xl mx-auto w-full">
                        {children}
                    </div>
                </main>
            </div>
        </div>
    );
}
