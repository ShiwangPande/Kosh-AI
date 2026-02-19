'use client';

import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { usePaginated } from '@/hooks';
import {
    ChevronRight,
    ArrowUpRight,
    TrendingDown,
    CheckCircle,
    XCircle,
    Lightbulb,
    Zap,
    ShieldCheck,
    Truck,
    IndianRupee,
    Loader2,
    Sparkles,
    Shield,
    Clock,
    Target,
    Package
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-hot-toast';
import { PageHeader, EmptyState } from '@/components';
import { useOnboarding } from '@/app/providers/onboarding-provider';

export default function RecommendationsPage() {
    const { completeStep } = useOnboarding();
    const { data: recs, loading, refetch } = usePaginated<any>(
        (params) => api.getRecommendations(params) as any
    );
    const [acceptingAll, setAcceptingAll] = useState(false);
    const [ignoringAll, setIgnoringAll] = useState(false);

    const handleAction = async (id: string, status: 'accepted' | 'rejected') => {
        const tid = toast.loading(status === 'accepted' ? 'Authorizing execution...' : 'Dismissing intelligence item...');
        try {
            await api.updateRecommendation(id, status);
            toast.success(status === 'accepted' ? 'Strategy authorized.' : 'Item dismissed.', { id: tid });
            refetch();
            completeStep('ACTION_DEMO');
        } catch (err: any) {
            toast.error(err.message || 'Operation failed', { id: tid });
        }
    };

    const handleAcceptAll = async () => {
        const pending = recs.filter((r: any) => r.status === 'pending');
        if (!pending.length) return;
        setAcceptingAll(true);
        const tid = toast.loading('Authorizing bulk execution...');
        try {
            await Promise.all(pending.map((r: any) => api.updateRecommendation(r.id, 'accepted')));
            toast.success('All strategies authorized.', { id: tid });
            refetch();
            completeStep('ACTION_DEMO');
        } catch (err: any) {
            toast.error(err.message || 'Bulk operation failed', { id: tid });
        } finally {
            setAcceptingAll(false);
        }
    };

    const handleIgnoreAll = async () => {
        const pending = recs.filter((r: any) => r.status === 'pending');
        if (!pending.length) return;
        setIgnoringAll(true);
        const tid = toast.loading('Dismissing all pending intelligence...');
        try {
            await Promise.all(pending.map((r: any) => api.updateRecommendation(r.id, 'rejected')));
            toast.success('All items dismissed.', { id: tid });
            refetch();
        } catch (err: any) {
            toast.error(err.message || 'Bulk operation failed', { id: tid });
        } finally {
            setIgnoringAll(false);
        }
    };

    return (
        <div style={{ padding: '0 4px' }}>
            <PageHeader
                title="Intelligence"
                subtitle="Autonomous strategic optimizations across your procurement stack"
                breadcrumb={[{ label: 'Dashboard', href: '/dashboard' }, { label: 'Intelligence' }]}
                actions={
                    !loading && recs.some((r: any) => r.status === 'pending') && (
                        <div style={{ display: 'flex', gap: '12px' }}>
                            <button
                                className="btn btn-primary"
                                onClick={handleAcceptAll}
                                disabled={acceptingAll || ignoringAll}
                                style={{ borderRadius: '12px', padding: '0 24px', height: '44px', gap: '8px' }}
                            >
                                {acceptingAll ? <Loader2 size={16} className="anim-spin" /> : <Sparkles size={16} />}
                                Authorized All
                            </button>
                            <button
                                className="btn btn-secondary"
                                onClick={handleIgnoreAll}
                                disabled={acceptingAll || ignoringAll}
                                style={{ borderRadius: '12px', padding: '0 24px', height: '44px', gap: '8px' }}
                            >
                                {ignoringAll ? <Loader2 size={16} className="anim-spin" /> : <XCircle size={16} />}
                                Dismiss All
                            </button>
                        </div>
                    )
                }
            />

            {loading ? (
                <div style={{ padding: '120px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '20px' }}>
                    <div className="anim-pulse" style={{ width: '64px', height: '64px', background: 'var(--primary-glow)', borderRadius: '50%' }} />
                    <div style={{ color: 'var(--text-muted)', fontSize: '15px' }}>Analyzing procurement patterns...</div>
                </div>
            ) : recs.length === 0 ? (
                <EmptyState
                    title="Insight Engine Standby"
                    description="Our algorithms are monitoring your supply chain. Optimization vectors will populate here once high-value savings are identified."
                    icon={<Zap size={40} />}
                />
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                    <AnimatePresence>
                        {recs.map((rec: any, idx: number) => (
                            <motion.div
                                key={rec.id}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: idx * 0.1 }}
                                className="glass-card elevation-1"
                                style={{ overflow: 'hidden', border: rec.status === 'pending' ? '1px solid var(--primary-glow)' : '1px solid var(--border)' }}
                            >
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'stretch' }}>
                                    <div style={{ padding: '32px', flex: 1 }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
                                            <span className={`badge ${rec.status === 'accepted' ? 'badge-success' :
                                                rec.status === 'rejected' ? 'badge-error' : 'badge-info'
                                                }`} style={{ borderRadius: '8px', padding: '6px 12px', fontWeight: 800 }}>
                                                {rec.status.toUpperCase()}
                                            </span>
                                            {rec.savings_estimate > 0 && (
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--success)', fontWeight: 900, background: 'var(--success-glow)', padding: '6px 12px', borderRadius: '8px', fontSize: '14px' }}>
                                                    <Target size={16} />
                                                    ESTIMATED SAVINGS: ₹{rec.savings_estimate.toLocaleString()}
                                                </div>
                                            )}
                                        </div>

                                        <h4 style={{ fontSize: '20px', fontWeight: 900, marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '10px' }}>
                                            <Package size={20} style={{ color: 'var(--primary)' }} />
                                            {rec.product_name || 'Generic SKU'}
                                        </h4>
                                        <div style={{
                                            display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px',
                                            background: 'var(--bg-secondary)', padding: '12px 16px', borderRadius: '12px', width: 'fit-content', border: '1px solid var(--border)'
                                        }}>
                                            <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>MIGRATE FROM</div>
                                            <span style={{ fontWeight: 800, color: 'var(--text-primary)' }}>{rec.current_supplier_name || 'Baseline'}</span>
                                            <ChevronRight size={16} style={{ color: 'var(--text-muted)' }} />
                                            <div style={{ fontSize: '13px', color: 'var(--primary)', fontWeight: 700 }}>TO</div>
                                            <span style={{ color: 'var(--primary)', fontWeight: 800 }}>{rec.recommended_supplier_name || 'Optimization Target'}</span>
                                        </div>

                                        <p style={{ color: 'var(--text-secondary)', fontSize: '15px', lineHeight: '1.7', maxWidth: '800px', marginBottom: '24px' }}>
                                            {rec.reason || 'Strategic pivot identified based on cross-supplier performance metrics and fulfillment reliability index.'}
                                        </p>

                                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: 'var(--text-muted)', background: 'var(--bg-glass)', padding: '8px 14px', borderRadius: '10px', border: '1px solid var(--border)' }}>
                                                <ShieldCheck size={16} style={{ color: 'var(--success)' }} /> RELIABILITY GUARANTEED
                                            </div>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: 'var(--text-muted)', background: 'var(--bg-glass)', padding: '8px 14px', borderRadius: '10px', border: '1px solid var(--border)' }}>
                                                <Truck size={16} style={{ color: 'var(--primary)' }} /> FAST FULFILLMENT
                                            </div>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', color: 'var(--text-muted)', background: 'var(--bg-glass)', padding: '8px 14px', borderRadius: '10px', border: '1px solid var(--border)' }}>
                                                <IndianRupee size={16} style={{ color: 'var(--success)' }} /> COST EFFICIENCY
                                            </div>
                                        </div>
                                    </div>

                                    {rec.status === 'pending' && (
                                        <div style={{
                                            width: '260px',
                                            background: 'linear-gradient(to bottom, var(--primary-glow), transparent)',
                                            borderLeft: '1px solid var(--border)',
                                            padding: '32px',
                                            display: 'flex',
                                            flexDirection: 'column',
                                            justifyContent: 'center',
                                            gap: '16px'
                                        }}>
                                            <button
                                                className="btn btn-primary"
                                                onClick={() => handleAction(rec.id, 'accepted')}
                                                style={{ width: '100%', height: '48px', justifyContent: 'center', borderRadius: '14px', gap: '10px', boxShadow: '0 8px 16px -4px var(--primary-glow)' }}
                                            >
                                                <Sparkles size={18} /> Execute
                                            </button>
                                            <button
                                                className="btn btn-secondary"
                                                onClick={() => handleAction(rec.id, 'rejected')}
                                                style={{ width: '100%', height: '48px', justifyContent: 'center', borderRadius: '14px', gap: '10px' }}
                                            >
                                                <XCircle size={18} /> Dismiss
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>
            )}
        </div>
    );
}
