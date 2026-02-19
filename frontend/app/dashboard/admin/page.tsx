'use client';

import { useState, useEffect, useCallback } from 'react';
import api from '@/lib/api';
import { useAuth, usePaginated } from '@/hooks';
import { Settings, ShieldAlert, Save, Activity, ShieldCheck, UserCheck, Clock, Sliders, ChevronRight } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-hot-toast';
import { PageHeader, EmptyState } from '@/components';

export default function AdminPage() {
    const { isAdmin } = useAuth();
    const [weights, setWeights] = useState({
        credit_score: 0.3,
        price_score: 0.25,
        reliability_score: 0.2,
        switching_friction: 0.15,
        delivery_speed: 0.1,
    });
    const [saving, setSaving] = useState(false);

    const fetchLogs = useCallback((params: any) => api.getLogs(params) as any, []);

    const { data: logs, loading: logsLoading } = usePaginated<any>(fetchLogs);

    useEffect(() => {
        api.getWeights()
            .then((w: any) => setWeights(w))
            .catch(() => { });
    }, []);

    const handleSaveWeights = async () => {
        const total = Object.values(weights).reduce((a, b) => a + b, 0);
        if (Math.abs(total - 1) > 0.01) {
            toast.error(`Weights must aggregate to 1.00 (Current: ${total.toFixed(2)})`);
            return;
        }

        const tid = toast.loading('Synchronizing scoring weights...');
        setSaving(true);
        try {
            await api.updateWeights(weights);
            toast.success('Heuristics updated successfully.', { id: tid });
        } catch (err: any) {
            toast.error(err.message || 'Synchronization failed', { id: tid });
        } finally {
            setSaving(false);
        }
    };

    if (!isAdmin) {
        return (
            <div style={{ padding: '80px 20px' }}>
                <EmptyState
                    title="Security Clearance Required"
                    description="You are attempting to access a restricted administrative zone. Please authenticate with executive credentials."
                    icon={<ShieldAlert size={40} />}
                />
            </div>
        );
    }

    const weightLabels: Record<string, string> = {
        credit_score: 'Credit Score',
        price_score: 'Price Score',
        reliability_score: 'Reliability',
        switching_friction: 'Switching Friction',
        delivery_speed: 'Delivery Speed',
    };

    return (
        <div style={{ padding: '0 4px' }}>
            <PageHeader
                title="System Control"
                subtitle="Configure global heuristics and audit autonomous operations"
                breadcrumb={[{ label: 'Dashboard', href: '/dashboard' }, { label: 'Admin' }]}
                actions={
                    <button
                        className="btn btn-primary"
                        onClick={handleSaveWeights}
                        disabled={saving}
                        style={{ borderRadius: '12px', gap: '8px', padding: '0 24px' }}
                    >
                        {saving ? <ShieldCheck className="anim-pulse" size={18} /> : <Save size={18} />}
                        {saving ? 'Synchronizing...' : 'Save Heuristics'}
                    </button>
                }
            />

            <div style={{ display: 'grid', gridTemplateColumns: 'minmax(300px, 1fr) 2fr', gap: '24px', alignItems: 'start' }}>
                {/* Weights Configuration */}
                <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="glass-card elevation-1"
                    style={{ padding: '32px' }}
                >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
                        <div style={{ padding: '10px', borderRadius: '12px', background: 'var(--primary-glow)', color: 'var(--primary)' }}>
                            <Sliders size={20} />
                        </div>
                        <div>
                            <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 900 }}>Scoring Heuristics</h3>
                            <p style={{ margin: 0, fontSize: '12px', color: 'var(--text-muted)' }}>Adjust the Kosh AI value algorithm</p>
                        </div>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                        {Object.entries(weights).map(([key, value]) => (
                            <div key={key} className="form-group" style={{ marginBottom: 0 }}>
                                <label className="form-label" style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                                    {weightLabels[key] || key}
                                    <span style={{ fontWeight: 800, color: 'var(--primary)' }}>{(value * 100).toFixed(0)}%</span>
                                </label>
                                <input
                                    className="form-input"
                                    type="range"
                                    step="0.05"
                                    min="0"
                                    max="1"
                                    value={value}
                                    onChange={(e) => setWeights({ ...weights, [key]: parseFloat(e.target.value) || 0 })}
                                    style={{ padding: 0, height: '6px', background: 'var(--bg-secondary)', borderRadius: '3px' }}
                                />
                            </div>
                        ))}
                    </div>

                    <div style={{
                        marginTop: '32px', padding: '20px', borderRadius: '16px',
                        background: 'var(--bg-secondary)', border: '1px solid var(--border)',
                        display: 'flex', justifyContent: 'space-between', alignItems: 'center'
                    }}>
                        <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-muted)' }}>Aggregate Sum</div>
                        <div style={{
                            fontSize: '20px', fontWeight: 900,
                            color: Math.abs(Object.values(weights).reduce((a, b) => a + b, 0) - 1) < 0.01
                                ? 'var(--success)' : 'var(--error)'
                        }}>
                            {Object.values(weights).reduce((a, b) => a + b, 0).toFixed(2)}
                        </div>
                    </div>
                </motion.div>

                {/* Activity Logs */}
                <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="table-container glass-card elevation-1"
                    style={{ padding: 0 }}
                >
                    <div style={{ padding: '24px 32px', borderBottom: '1px solid var(--border)', background: 'var(--bg-secondary)', display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <Activity size={18} style={{ color: 'var(--text-muted)' }} />
                        <h3 className="card-title" style={{ margin: 0, fontSize: '15px', fontWeight: 900 }}>Autonomous Activity Ledger</h3>
                    </div>

                    {logsLoading ? (
                        <div style={{ padding: '100px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
                            <div className="anim-pulse" style={{ width: '40px', height: '40px', background: 'var(--primary-glow)', borderRadius: '50%' }} />
                            <div style={{ color: 'var(--text-muted)', fontSize: '14px' }}>Syncing audit trail...</div>
                        </div>
                    ) : logs.length === 0 ? (
                        <div style={{ padding: '60px' }}>
                            <EmptyState title="No Activity Logs" description="Audit trails will appear here after system interactions." icon={<Clock size={40} />} />
                        </div>
                    ) : (
                        <div className="table-container">
                            <table style={{ borderCollapse: 'collapse' }}>
                                <thead>
                                    <tr>
                                        <th style={{ padding: '16px 32px' }}>Instruction</th>
                                        <th>Entity Space</th>
                                        <th>Clearance</th>
                                        <th style={{ textAlign: 'right', paddingRight: '32px' }}>Timestamp</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <AnimatePresence>
                                        {logs.map((log: any, idx: number) => (
                                            <motion.tr
                                                key={log.id}
                                                initial={{ opacity: 0, y: 10 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                transition={{ delay: idx * 0.05 }}
                                            >
                                                <td style={{ padding: '16px 32px', fontWeight: 700, color: 'var(--text-primary)' }}>
                                                    {log.action}
                                                </td>
                                                <td>
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', fontSize: '13px' }}>
                                                        <ChevronRight size={14} /> {log.resource_type || 'SYSTEM'}
                                                    </div>
                                                </td>
                                                <td>
                                                    <span className="badge badge-info" style={{ borderRadius: '6px', fontSize: '11px', padding: '4px 8px' }}>
                                                        {log.actor_role?.toUpperCase() || 'ANONYMOUS'}
                                                    </span>
                                                </td>
                                                <td style={{ textAlign: 'right', paddingRight: '32px', fontSize: '12px', color: 'var(--text-muted)' }}>
                                                    {log.created_at ? new Date(log.created_at).toLocaleString() : '—'}
                                                </td>
                                            </motion.tr>
                                        ))}
                                    </AnimatePresence>
                                </tbody>
                            </table>
                        </div>
                    )}
                </motion.div>
            </div>
        </div>
    );
}
