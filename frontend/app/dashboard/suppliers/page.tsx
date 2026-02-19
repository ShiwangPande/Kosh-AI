'use client';

import { useState } from 'react';
import api from '@/lib/api';
import { usePaginated } from '@/hooks';
import { toast } from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Factory,
    Plus,
    Search,
    Filter,
    CheckCircle2,
    AlertCircle,
    MapPin,
    Tag,
    CreditCard,
    User,
    Mail,
    Phone,
    X,
    ChevronDown,
    Zap,
    TrendingUp,
    Clock
} from 'lucide-react';
import { PageHeader, ScoreBar, EmptyState } from '@/components';

export default function SuppliersPage() {
    const [showForm, setShowForm] = useState(false);
    const [search, setSearch] = useState('');
    const { data: suppliers, loading, refetch } = usePaginated<any>(
        (params) => api.getSuppliers({ ...params, search, approved_only: 'false' }) as any,
        {}
    );

    const [form, setForm] = useState({
        name: '', contact_person: '', email: '', phone: '',
        category: '', city: '', credit_terms: '0',
    });

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        const tid = toast.loading('Registering new supplier...');
        try {
            await api.createSupplier({
                ...form,
                credit_terms: parseInt(form.credit_terms) || 0,
            });
            setShowForm(false);
            setForm({ name: '', contact_person: '', email: '', phone: '', category: '', city: '', credit_terms: '0' });
            toast.success('Supplier registered successfully!', { id: tid });
            refetch();
        } catch (err: any) {
            toast.error(err.message || 'Registration failed', { id: tid });
        }
    };

    return (
        <div style={{ padding: '0 4px' }}>
            <PageHeader
                title="Suppliers"
                subtitle="High-fidelity directory of your procurement partner network"
                breadcrumb={[{ label: 'Dashboard', href: '/dashboard' }, { label: 'Suppliers' }]}
                actions={
                    <button className="btn btn-primary" onClick={() => setShowForm(!showForm)} style={{ borderRadius: '12px' }}>
                        {showForm ? <X size={18} /> : <Plus size={18} />} {showForm ? 'Discard' : 'Register Supplier'}
                    </button>
                }
            />

            <AnimatePresence>
                {showForm && (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="glass-card"
                        style={{ marginBottom: '32px', overflow: 'hidden', border: '1px solid var(--primary-glow)', background: 'var(--bg-glass)' }}
                    >
                        <div style={{ padding: '32px' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
                                <div style={{ padding: '8px', borderRadius: '10px', background: 'var(--primary-glow)', color: 'var(--primary)' }}>
                                    <Plus size={20} />
                                </div>
                                <h3 style={{ margin: 0, fontWeight: 900 }}>New Partner Registration</h3>
                            </div>
                            <form onSubmit={handleCreate}>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px' }}>
                                    <div className="form-group">
                                        <label className="form-label">Full Business Name *</label>
                                        <input className="form-input" required value={form.name}
                                            onChange={(e) => setForm({ ...form, name: e.target.value })}
                                            style={{ borderRadius: '10px' }}
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Contact Liaison</label>
                                        <input className="form-input" value={form.contact_person}
                                            onChange={(e) => setForm({ ...form, contact_person: e.target.value })}
                                            style={{ borderRadius: '10px' }}
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Email Address</label>
                                        <input className="form-input" type="email" value={form.email}
                                            onChange={(e) => setForm({ ...form, email: e.target.value })}
                                            style={{ borderRadius: '10px' }}
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Primary Phone</label>
                                        <input className="form-input" value={form.phone}
                                            onChange={(e) => setForm({ ...form, phone: e.target.value })}
                                            style={{ borderRadius: '10px' }}
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Industry Sector</label>
                                        <input className="form-input" placeholder="e.g. Pharma, FMCG"
                                            value={form.category}
                                            onChange={(e) => setForm({ ...form, category: e.target.value })}
                                            style={{ borderRadius: '10px' }}
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Operation City</label>
                                        <input className="form-input" value={form.city}
                                            onChange={(e) => setForm({ ...form, city: e.target.value })}
                                            style={{ borderRadius: '10px' }}
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label">Credit Cycle (Days)</label>
                                        <input className="form-input" type="number" value={form.credit_terms}
                                            onChange={(e) => setForm({ ...form, credit_terms: e.target.value })}
                                            style={{ borderRadius: '10px' }}
                                        />
                                    </div>
                                </div>
                                <div style={{ marginTop: '32px', display: 'flex', gap: '12px' }}>
                                    <button type="submit" className="btn btn-primary" style={{ padding: '12px 32px', borderRadius: '12px' }}>
                                        Establish Partnership
                                    </button>
                                </div>
                            </form>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            <div style={{ display: 'flex', gap: '16px', marginBottom: '32px', alignItems: 'center' }}>
                <div style={{ position: 'relative', flex: 1, maxWidth: '400px' }}>
                    <Search size={18} style={{ position: 'absolute', left: '16px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                    <input
                        className="form-input"
                        placeholder="Search by name or category..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        style={{ paddingLeft: '48px', height: '48px', borderRadius: '14px', background: 'var(--bg-glass)', border: '1px solid var(--border)' }}
                    />
                </div>
                <button className="btn btn-secondary" style={{ height: '48px', padding: '0 20px', borderRadius: '14px', gap: '10px' }}>
                    <Filter size={18} /> Global Filter
                </button>
            </div>

            {loading ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '100px 40px', gap: '20px' }}>
                    <div className="anim-pulse" style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'var(--primary-glow)' }} />
                    <span style={{ color: 'var(--text-muted)', fontSize: '15px' }}>Mapping your network...</span>
                </div>
            ) : (
                <div className="table-container glass-card" style={{ border: '1px solid var(--border-glow)', boxShadow: 'var(--shadow-md)' }}>
                    <table style={{ borderCollapse: 'collapse' }}>
                        <thead>
                            <tr>
                                <th style={{ padding: '16px 24px' }}>Partner Entity</th>
                                <th>Sector</th>
                                <th>Credit</th>
                                <th style={{ width: '160px' }}>Reliability</th>
                                <th style={{ width: '160px' }}>Price Stability</th>
                                <th style={{ width: '160px' }}>Fulfillment</th>
                                <th style={{ textAlign: 'right', paddingRight: '24px' }}>Tier</th>
                            </tr>
                        </thead>
                        <tbody>
                            {suppliers.length === 0 ? (
                                <tr>
                                    <td colSpan={8} style={{ padding: 0 }}>
                                        <EmptyState
                                            title="Partner Network is Empty"
                                            description="Start building your procurement network by adding your first supplier or uploading an invoice."
                                            icon={<Factory size={40} />}
                                            action={
                                                <button className="btn btn-primary" onClick={() => setShowForm(true)}>
                                                    <Plus size={18} /> Register Supplier
                                                </button>
                                            }
                                        />
                                    </td>
                                </tr>
                            ) : (
                                <AnimatePresence>
                                    {suppliers.map((s: any, idx: number) => (
                                        <motion.tr
                                            key={s.id}
                                            initial={{ opacity: 0, x: -10 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: idx * 0.05 }}
                                            style={{ cursor: 'pointer' }}
                                        >
                                            <td style={{ padding: '20px 24px' }}>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                                                    <div style={{
                                                        width: '40px', height: '40px', borderRadius: '12px',
                                                        background: 'var(--bg-hover)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                        fontWeight: 800, color: 'var(--primary)', fontSize: '16px', textTransform: 'uppercase'
                                                    }}>
                                                        {s.name.charAt(0)}
                                                    </div>
                                                    <div>
                                                        <div style={{ fontWeight: 800, color: 'var(--text-primary)', fontSize: '15px' }}>{s.name}</div>
                                                        <div style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px', marginTop: '2px' }}>
                                                            <MapPin size={10} /> {s.city || 'Global'}
                                                        </div>
                                                    </div>
                                                </div>
                                            </td>
                                            <td>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', fontWeight: 600 }}>
                                                    <Tag size={12} style={{ color: 'var(--primary)' }} />
                                                    {s.category || 'Standard'}
                                                </div>
                                            </td>
                                            <td>
                                                <div style={{ fontSize: '13px', color: 'var(--text-primary)', fontWeight: 700 }}>
                                                    {s.credit_terms || 0} Days
                                                </div>
                                            </td>
                                            <td>
                                                <ScoreBar value={s.reliability_score || 0} />
                                            </td>
                                            <td>
                                                <ScoreBar value={s.price_consistency_score || 0} />
                                            </td>
                                            <td>
                                                <ScoreBar value={s.delivery_speed_score || 0} />
                                            </td>
                                            <td style={{ textAlign: 'right', paddingRight: '24px' }}>
                                                <span className={`badge ${s.is_approved ? 'badge-success' : 'badge-warning'}`} style={{ fontWeight: 800, borderRadius: '8px', padding: '6px 10px' }}>
                                                    {s.is_approved ? 'ELITE' : 'ENTRY'}
                                                </span>
                                            </td>
                                        </motion.tr>
                                    ))}
                                </AnimatePresence>
                            )}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
}

