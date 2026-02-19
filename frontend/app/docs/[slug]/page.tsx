'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import ReactMarkdown from 'react-markdown';
import { notFound } from 'next/navigation';
import { Loader2, ThumbsUp, ThumbsDown } from 'lucide-react';
import { motion } from 'framer-motion';

export default function DocArticlePage({ params }: { params: { slug: string } }) {
    const [article, setArticle] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [feedback, setFeedback] = useState<'yes' | 'no' | null>(null);

    useEffect(() => {
        api.getDocArticle(params.slug)
            .then(setArticle)
            .catch(() => setArticle(null))
            .finally(() => setLoading(false));
    }, [params.slug]);

    if (loading) {
        return (
            <div className="flex h-96 items-center justify-center">
                <Loader2 className="animate-spin text-primary" size={32} />
            </div>
        );
    }

    if (!article) return notFound();

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ type: 'spring', damping: 25 }}
            className="prose prose-invert max-w-none"
        >
            <div className="flex items-center gap-3 text-sm text-gray-400 mb-6">
                <span>Docs</span>
                <span>/</span>
                <span className="text-white font-medium">{article.category}</span>
            </div>

            <div className="bg-gradient-to-r from-primary/10 to-transparent p-6 rounded-2xl border border-primary/20 mb-10">
                <h1 className="text-4xl font-black tracking-tight mb-2">{article.title}</h1>
                <p className="text-lg text-gray-300 mb-0">{article.summary}</p>
            </div>

            <div className="prose-headings:font-bold prose-headings:text-white prose-p:text-gray-300 prose-strong:text-white prose-li:text-gray-300 prose-code:text-primary">
                <ReactMarkdown>{article.content}</ReactMarkdown>
            </div>

            <div className="mt-16 pt-8 border-t border-white/10 flex flex-col items-center justify-center gap-4">
                <p className="text-gray-400 font-medium">Was this article helpful?</p>
                <div className="flex gap-4">
                    <button
                        onClick={() => setFeedback('yes')}
                        className={`p-3 rounded-full transition-all ${feedback === 'yes' ? 'bg-green-500/20 text-green-500 ring-2 ring-green-500' : 'bg-white/5 hover:bg-white/10 text-gray-400'}`}
                    >
                        <ThumbsUp size={24} />
                    </button>
                    <button
                        onClick={() => setFeedback('no')}
                        className={`p-3 rounded-full transition-all ${feedback === 'no' ? 'bg-red-500/20 text-red-500 ring-2 ring-red-500' : 'bg-white/5 hover:bg-white/10 text-gray-400'}`}
                    >
                        <ThumbsDown size={24} />
                    </button>
                </div>
                {feedback && (
                    <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-sm text-gray-500">
                        Thanks for your feedback! We'll use it to improve our docs.
                    </motion.p>
                )}
            </div>
        </motion.div>
    );
}
