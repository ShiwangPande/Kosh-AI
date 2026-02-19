'use client';

import { useState } from 'react';
import { HelpCircle, X, ChevronRight, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '@/lib/api';
import Link from 'next/link';

interface ContextHelpProps {
    slug: string;
    label?: string;
}

export function ContextHelp({ slug, label }: ContextHelpProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [article, setArticle] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    const handleOpen = async () => {
        setIsOpen(true);
        if (!article) {
            setLoading(true);
            try {
                const data = await api.getDocArticle(slug);
                setArticle(data);
            } catch (err) {
                console.error('Failed to load context help', err);
            } finally {
                setLoading(false);
            }
        }
    };

    return (
        <>
            <button
                onClick={handleOpen}
                className="inline-flex items-center gap-1.5 text-xs font-medium text-gray-400 hover:text-primary transition-colors"
            >
                <HelpCircle size={14} />
                {label && <span>{label}</span>}
            </button>

            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: 10 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: 10 }}
                        className="absolute z-50 mt-2 w-80 p-4 bg-[#1a1a20] border border-white/10 rounded-xl shadow-2xl origin-top-left"
                        style={{ maxWidth: '90vw' }}
                    >
                        <div className="flex justify-between items-start mb-3">
                            <h4 className="text-sm font-bold text-white pr-6">
                                {article?.title || 'Loading help...'}
                            </h4>
                            <button
                                onClick={() => setIsOpen(false)}
                                className="p-1 hover:bg-white/10 rounded-full text-gray-400"
                            >
                                <X size={14} />
                            </button>
                        </div>

                        {loading ? (
                            <div className="py-4 flex justify-center">
                                <Loader2 size={20} className="animate-spin text-primary" />
                            </div>
                        ) : article ? (
                            <div className="space-y-3">
                                <p className="text-xs text-gray-300 leading-relaxed">
                                    {article.summary}
                                </p>
                                <Link
                                    href={`/docs/${article.slug}`}
                                    className="flex items-center gap-1 text-xs font-bold text-primary hover:underline"
                                >
                                    Read full article <ChevronRight size={12} />
                                </Link>
                            </div>
                        ) : (
                            <p className="text-xs text-red-400">
                                Help content currently unavailable.
                            </p>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
}
