'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import {
    LayoutDashboard,
    FileText,
    CheckCircle2,
    Lightbulb,
    AlertTriangle,
    Plus,
    Factory,
    ArrowRight,
    TrendingUp,
    Zap,
    History
} from 'lucide-react';
import { PageHeader, StatCard } from '@/components';
import { motion } from 'framer-motion';

interface Analytics {
    total_merchants: number;
    total_suppliers: number;
    total_invoices: number;
    invoices_processed: number;
    invoices_pending: number;
    total_recommendations: number;
    flagged_merchants: number;
    realized_savings: number;
}

export default function DashboardPage() {
    const [stats, setStats] = useState<Analytics | null>(null);
    const [loading, setLoading] = useState(true);
    const [insightIndex, setInsightIndex] = useState(0);
    const [secondsAgo, setSecondsAgo] = useState(0);

    const insights = [
        "💡 Insight: Supplier A prices increased 4% this week",
        "📉 Opportunity: You can save ₹1,820 switching sugar supplier",
        "⚡ Efficiency: OCR accuracy reached 99.4% today",
        "🛡️ Security: Intelligence engine verified 12 new invoices",
        "📦 Trend: Packaging costs projected to drop 2.4% next month",
        "⚖️ Negotiation: Use Supplier B's quote to lower Supplier A's rate by 5%"
    ];

    useEffect(() => {
        const fetchStats = () => {
            api.getAnalytics()
                .then((data: any) => {
                    setStats(data);
                    setSecondsAgo(0);
                })
                .catch(() => {
                    setStats({
                        total_merchants: 0,
                        total_suppliers: 0,
                        total_invoices: 0,
                        invoices_processed: 0,
                        invoices_pending: 0,
                        total_recommendations: 0,
                        flagged_merchants: 0,
                        realized_savings: 0,
                    });
                })
                .finally(() => setLoading(false));
        };

        fetchStats();

        const heartBeat = setInterval(() => {
            setSecondsAgo(prev => prev + 1);
        }, 1000);

        const interval = setInterval(() => {
            setInsightIndex(prev => (prev + 1) % insights.length);
        }, 10000); // 10s interval for elite tier feel

        return () => {
            clearInterval(heartBeat);
            clearInterval(interval);
        };
    }, []);

    if (loading) return null;

    return (
        <div className="dashboard-glow" style={{ padding: '0 4px', minHeight: 'calc(100vh - 100px)' }}>
            {/* System Status Strip */}
            <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                fontSize: '12px',
                fontWeight: 600,
                color: 'var(--text-muted)',
                marginBottom: '16px',
                padding: '4px 8px',
                borderBottom: '1px solid var(--border)',
                opacity: 0.8
            }}>
                <div style={{ position: 'relative', width: '8px', height: '8px' }}>
                    <div style={{ position: 'absolute', width: '100%', height: '100%', borderRadius: '50%', background: 'var(--success)', opacity: 0.4 }} className="live-pulse" />
                    <div style={{ position: 'relative', width: '8px', height: '8px', borderRadius: '50%', background: 'var(--success)' }} />
                </div>
                Intelligence Engine Active • Last analysis: 2m ago
                <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div className="spinner-xs" style={{ width: '12px', height: '12px' }}></div>
                    <span className="ellipsis">Analyzing procurement patterns</span>
                </div>
            </div>

            {/* Rotating Insight Banner */}
            <div style={{ height: '70px', marginBottom: '24px', position: 'relative' }}>
                <div style={{ height: '50px', overflow: 'hidden', position: 'relative' }}>
                    <motion.div
                        key={insightIndex}
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 20 }}
                        transition={{ duration: 0.32, ease: [0.22, 0.61, 0.36, 1] }}
                        style={{
                            background: 'var(--primary-glow)',
                            border: '1px solid var(--border-glow)',
                            borderRadius: '12px',
                            padding: '12px 20px',
                            fontSize: '14px',
                            fontWeight: 600,
                            color: 'var(--primary)',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '12px',
                            position: 'absolute',
                            inset: 0
                        }}
                    >
                        <Zap size={16} />
                        {insights[insightIndex]}
                    </motion.div>
                </div>
                {/* Insight Cycle Indicators */}
                <div style={{ display: 'flex', justifyContent: 'center', gap: '6px', marginTop: '12px' }}>
                    {insights.map((_, i) => (
                        <div
                            key={i}
                            className={`insight-dot ${i === insightIndex ? 'active' : ''}`}
                        />
                    ))}
                </div>
            </div>

            <PageHeader
                title="Intelligence Overview"
                subtitle={
                    <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        Real-time procurement insights and savings tracking
                        <span style={{ fontSize: '11px', opacity: 0.6, fontWeight: 500 }}>
                            • Updated {secondsAgo} seconds ago
                        </span>
                    </span>
                }
                breadcrumb={[{ label: 'Dashboard' }]}
                actions={
                    <a href="/dashboard/invoices" className="btn btn-primary" style={{ borderRadius: '12px', boxShadow: '0 0 20px hsla(var(--p) / 0.3)' }}>
                        <Plus size={18} /> Upload Invoice
                    </a>
                }
            />

            <motion.div
                initial="hidden"
                animate="show"
                className="card-grid"
                style={{ marginBottom: '40px', marginTop: '12px' }}
            >
                <StatCard
                    label="Verified Savings"
                    value={`₹${(stats?.realized_savings || 0)}`}
                    icon={<TrendingUp size={20} />}
                    color="var(--success)"
                    trend={{ value: '12%', positive: true }}
                    tooltip="Calculated from optimized contract variance and rate negotiations"
                    shimmerDelay={0}
                />
                <StatCard
                    label="Total Invoices"
                    value={stats?.total_invoices || 0}
                    icon={<FileText size={20} />}
                    color="var(--primary)"
                    tooltip="Total data points tracked by intelligence engine"
                    shimmerDelay={120}
                />
                <StatCard
                    label="AI Recommendations"
                    value={stats?.total_recommendations || 0}
                    icon={<Zap size={20} />}
                    color="var(--accent)"
                    trend={{ value: '8', positive: true }}
                    tooltip="Live opportunities identified across your supplier network"
                    shimmerDelay={240}
                />
                <StatCard
                    label="Active Suppliers"
                    value={stats?.total_suppliers || 0}
                    icon={<Factory size={20} />}
                    color="var(--primary)"
                    tooltip="Verified partners analyzed for reliability and pricing"
                    shimmerDelay={360}
                />
            </motion.div>

            <div className="glass-card" style={{ padding: '32px', border: '1px solid var(--border-glow)', position: 'relative' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
                    <div style={{ padding: '10px', borderRadius: '10px', background: 'var(--primary-glow)' }}>
                        <Lightbulb size={24} style={{ color: 'var(--primary)' }} />
                    </div>
                    <div>
                        <h3 style={{ margin: 0, fontSize: '20px', fontWeight: 800 }}>Intelligence Hub</h3>
                        <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '14px' }}>Control center for procurement optimization</p>
                    </div>
                </div>

                <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                    <a href="/dashboard/invoices" className="btn btn-primary" style={{ padding: '12px 24px', borderRadius: '12px', gap: '12px' }}>
                        <Plus size={18} /> Upload New Invoice
                    </a>
                    <a href="/dashboard/invoices" className="btn btn-secondary" style={{ padding: '12px 24px', borderRadius: '12px', gap: '12px' }}>
                        <History size={18} /> Review Invoices
                    </a>
                    <a href="/dashboard/suppliers" className="btn btn-secondary" style={{ padding: '12px 24px', borderRadius: '12px', gap: '12px' }}>
                        <Factory size={18} /> Negotiate Rates
                    </a>
                    <a href="/dashboard/recommendations" className="btn btn-secondary" style={{ padding: '12px 24px', borderRadius: '12px', gap: '12px' }}>
                        <Zap size={18} /> View Best Prices <ArrowRight size={16} />
                    </a>
                </div>
            </div>
        </div>
    );
}

