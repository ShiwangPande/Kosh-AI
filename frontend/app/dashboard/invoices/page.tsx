'use client';

import { useState, useRef, useEffect, useMemo } from 'react';
import api from '@/lib/api';
import { usePaginated } from '@/hooks';
import { toast } from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';

import {
    FileUp,
    Search,
    Trash2,
    AlertCircle,
    CheckCircle,
    Clock,
    X,
    ClipboardCheck,
    Loader2,
    Calendar,
    IndianRupee,
    ChevronRight,
    ArrowUpRight,
    Ban,
    Filter,
    ArrowRight,
    Plus
} from 'lucide-react';
import { PageHeader, EmptyState } from '@/components';
import { useOnboarding } from '@/app/providers/onboarding-provider';

export default function InvoicesPage() {
    const { completeStep } = useOnboarding();
    const [uploading, setUploading] = useState(false);
    const [dragActive, setDragActive] = useState(false);
    const [reviewId, setReviewId] = useState<string | null>(null);
    const [search, setSearch] = useState('');
    const fileRef = useRef<HTMLInputElement>(null);

    const fetcher = useMemo(() => (params: Record<string, string>) => api.getInvoices(params) as any, []);

    const { data: invoices, loading, refetch } = usePaginated<any>(
        fetcher
    );

    // ── Polling for processing invoices ──────────────────────
    useEffect(() => {
        const hasProcessing = invoices.some(
            (inv: any) => inv.ocr_status === 'processing' || inv.ocr_status === 'pending'
        );

        if (hasProcessing) {
            const interval = setInterval(() => {
                refetch(true); // Silent refetch
            }, 10000);
            return () => clearInterval(interval);
        }
    }, [invoices, refetch]);

    const handleUpload = async (file: File) => {
        const toastId = toast.loading(`Uploading ${file.name}...`);
        setUploading(true);
        try {
            await api.uploadInvoice(file);
            toast.success('Invoice uploaded successfully! Processing started.', { id: toastId });
            refetch();
            completeStep('UPLOAD_INVOICE');
        } catch (err: any) {
            toast.error(err.message || 'Upload failed', { id: toastId });
        } finally {
            setUploading(false);
        }
    };

    const handleCancel = async (id: string) => {
        try {
            await api.cancelInvoice(id);
            toast.success('Invoice processing cancelled');
            refetch();
        } catch (err: any) {
            toast.error(err.message || 'Cancel failed');
        }
    };

    const handleDelete = async (id: string, fileNumber: string) => {
        try {
            await api.deleteInvoice(id);
            toast.success('Invoice deleted');
            refetch();
        } catch (err: any) {
            toast.error(err.message || 'Delete failed');
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setDragActive(false);
        const file = e.dataTransfer.files[0];
        if (file) handleUpload(file);
    };

    const statusBadge = (status: string) => {
        const configs: Record<string, { class: string, icon: any, label: string }> = {
            completed: { class: 'badge-success', icon: CheckCircle, label: 'Verified' },
            processing: { class: 'badge-info', icon: Loader2, label: 'OCR Processing' },
            pending: { class: 'badge-warning', icon: Clock, label: 'In Queue' },
            failed: { class: 'badge-error', icon: AlertCircle, label: 'Extraction Failed' },
            needs_review: { class: 'badge-warning', icon: ClipboardCheck, label: 'Ready for Review' },
        };
        const conf = configs[status] || { class: 'badge-info', icon: AlertCircle, label: status };
        const Icon = conf.icon;

        return (
            <span className={`badge ${conf.class}`} style={{ gap: '6px', padding: '6px 12px' }}>
                <Icon size={12} className={status === 'processing' ? 'anim-spin' : ''} />
                {conf.label}
            </span>
        );
    };

    return (
        <div style={{ padding: '0 4px' }}>
            <PageHeader
                title="Invoices"
                subtitle="Manage purchase records and trigger extraction intelligence"
                breadcrumb={[{ label: 'Dashboard', href: '/dashboard' }, { label: 'Invoices' }]}
                actions={
                    <div style={{ display: 'flex', gap: '12px' }}>
                        <div style={{ position: 'relative', width: '240px' }}>
                            <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                            <input
                                className="form-input"
                                value={search}
                                onChange={e => setSearch(e.target.value)}
                                placeholder="Search serial numbers..."
                                style={{ paddingLeft: '38px', height: '40px', borderRadius: '12px', background: 'var(--bg-hover)' }}
                            />
                        </div>
                        <button className="btn btn-secondary" style={{ width: '40px', padding: 0, justifyContent: 'center', borderRadius: '12px' }}>
                            <Filter size={18} />
                        </button>
                    </div>
                }
            />

            {invoices.length > 0 || search ? (
                <>
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.1 }}
                        className={`upload-zone glass-card ${dragActive ? 'dragging' : ''}`}
                        onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
                        onDragLeave={() => setDragActive(false)}
                        onDrop={handleDrop}
                        onClick={() => fileRef.current?.click()}
                        style={{
                            marginBottom: '32px',
                            padding: '32px',
                            border: '2px dashed var(--border)',
                            background: dragActive ? 'var(--primary-glow)' : 'var(--bg-glass)',
                            borderRadius: 'var(--radius-lg)',
                            display: 'flex',
                            flexDirection: 'row',
                            alignItems: 'center',
                            gap: '24px',
                            textAlign: 'left'
                        }}
                    >
                        <input
                            ref={fileRef}
                            type="file"
                            accept=".pdf,.png,.jpg,.jpeg,.tiff"
                            style={{ display: 'none' }}
                            onChange={(e) => {
                                const file = e.target.files?.[0];
                                if (file) handleUpload(file);
                            }}
                        />
                        <div style={{
                            width: '48px', height: '48px',
                            borderRadius: '12px',
                            background: 'var(--primary-glow)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            color: 'var(--primary)',
                            flexShrink: 0
                        }}>
                            {uploading ? <Loader2 className="anim-spin" size={24} /> : <FileUp size={24} />}
                        </div>
                        <div style={{ flex: 1 }}>
                            <h3 style={{ fontSize: '16px', fontWeight: 800, marginBottom: '2px' }}>
                                {uploading ? 'Shielding your data...' : (dragActive ? 'Release to upload' : 'Add Purchase Document')}
                            </h3>
                            <p style={{ color: 'var(--text-muted)', fontSize: '13px', margin: 0 }}>
                                {uploading ? 'Uploading and optimizing for high-precision OCR' : 'Drop your PDF or Image here to start intelligence extraction.'}
                            </p>
                        </div>
                        <button className="btn btn-primary btn-sm" style={{ borderRadius: '10px', height: '36px' }}>
                            <Plus size={16} /> Select File
                        </button>
                    </motion.div>

                    <div className="table-container glass-card elevation-1" style={{ border: '1px solid var(--border-glow)', boxShadow: 'var(--shadow-md)' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                            <thead>
                                <tr>
                                    <th style={{ padding: '16px 24px' }}><div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><Calendar size={14} /> Created At</div></th>
                                    <th>Invoice #</th>
                                    <th><div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}><IndianRupee size={14} /> Amount</div></th>
                                    <th>Status</th>
                                    <th style={{ width: '140px' }}>Confidence</th>
                                    <th style={{ textAlign: 'right', paddingRight: '24px' }}>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                <AnimatePresence>
                                    {invoices.map((inv: any, idx: number) => (
                                        <motion.tr
                                            key={inv.id}
                                            initial={{ opacity: 0, x: -10 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: idx * 0.05 }}
                                            style={{ cursor: 'pointer' }}
                                        >
                                            <td style={{ padding: '16px 24px', color: 'var(--text-muted)', fontSize: '13px', fontWeight: 500 }}>
                                                {new Date(inv.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}
                                            </td>
                                            <td style={{ fontWeight: 800, color: 'var(--text-primary)', fontSize: '14px' }}>
                                                {inv.invoice_number || '—'}
                                            </td>
                                            <td style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                                                {inv.total_amount ? `₹${inv.total_amount.toLocaleString()}` : '—'}
                                            </td>
                                            <td>{statusBadge(inv.ocr_status)}</td>
                                            <td>
                                                {inv.ocr_confidence != null ? (
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                                        <div className="score-bar" style={{ width: '60px', height: '6px' }}>
                                                            <div className="score-fill" style={{
                                                                width: `${inv.ocr_confidence * 100}%`,
                                                                background: inv.ocr_confidence > 0.8 ? 'var(--success)' : (inv.ocr_confidence > 0.5 ? 'var(--warning)' : 'var(--error)')
                                                            }} />
                                                        </div>
                                                        <span style={{ fontSize: '11px', fontWeight: 800 }}>{(inv.ocr_confidence * 100).toFixed(0)}%</span>
                                                    </div>
                                                ) : '—'}
                                            </td>
                                            <td style={{ textAlign: 'right', paddingRight: '24px' }}>
                                                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                                                    {inv.ocr_status === 'needs_review' ? (
                                                        <button
                                                            onClick={() => setReviewId(inv.id)}
                                                            className="btn btn-primary btn-sm"
                                                            style={{ borderRadius: '10px', height: '32px' }}
                                                        >
                                                            Verify Now <ArrowRight size={14} style={{ marginLeft: '4px' }} />
                                                        </button>
                                                    ) : (inv.ocr_status === 'completed' && (
                                                        <button
                                                            className="btn btn-secondary btn-sm"
                                                            style={{ borderRadius: '10px', height: '32px' }}
                                                            onClick={() => setReviewId(inv.id)}
                                                        >
                                                            Details
                                                        </button>
                                                    ))}
                                                    <button onClick={() => handleDelete(inv.id, inv.invoice_number)} className="btn btn-secondary btn-sm" style={{ width: '32px', height: '32px', padding: 0, justifyContent: 'center' }}>
                                                        <Trash2 size={14} />
                                                    </button>
                                                </div>
                                            </td>
                                        </motion.tr>
                                    ))}
                                </AnimatePresence>
                            </tbody>
                        </table>
                    </div>
                </>
            ) : (
                <div style={{ marginTop: '40px' }}>
                    <input
                        ref={fileRef}
                        type="file"
                        accept=".pdf,.png,.jpg,.jpeg,.tiff"
                        style={{ display: 'none' }}
                        onChange={(e) => {
                            const file = e.target.files?.[0];
                            if (file) handleUpload(file);
                        }}
                    />
                    <EmptyState
                        title="Shielding Your Procurement Data"
                        description="Upload your first purchase record to start automated intelligence extraction and inventory orchestration."
                        icon={<FileUp size={44} />}
                        action={
                            <button
                                className="btn btn-primary"
                                onClick={() => fileRef.current?.click()}
                                style={{ padding: '0 32px', height: '48px', borderRadius: '14px', fontSize: '16px' }}
                            >
                                <Plus size={20} /> Get Started Now
                            </button>
                        }
                    />
                </div>
            )}

            <AnimatePresence>
                {reviewId && (
                    <ReviewModal
                        invoiceId={reviewId}
                        onClose={() => setReviewId(null)}
                        onVerified={() => {
                            setReviewId(null);
                            refetch();
                        }}
                    />
                )}
            </AnimatePresence>
        </div>
    );
}

function ReviewModal({ invoiceId, onClose, onVerified }: { invoiceId: string, onClose: () => void, onVerified: () => void }) {
    const [items, setItems] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        api.getInvoiceItems(invoiceId)
            .then(setItems)
            .finally(() => setLoading(false));
    }, [invoiceId]);

    const handleChange = (index: number, field: string, value: any) => {
        const newItems = [...items];
        newItems[index] = { ...newItems[index], [field]: value };
        setItems(newItems);
    };

    const handleVerify = async () => {
        const tid = toast.loading('Applying corrections and updating intelligence...');
        setSubmitting(true);
        try {
            const corrections = items.map(item => ({
                item_id: item.id,
                description: item.raw_description,
                quantity: parseFloat(item.quantity) || 0,
                unit_price: parseFloat(item.unit_price) || 0,
                total_price: parseFloat(item.total_price) || 0,
                batch_number: item.batch_number,
                expiry_date: item.expiry_date,
                hsn_code: item.hsn_code,
                mrp: parseFloat(item.mrp) || 0,
            }));
            await api.verifyInvoice(invoiceId, corrections);
            toast.success('Invoice verified! Market intelligence updated.', { id: tid });
            onVerified();
        } catch (err: any) {
            toast.error(err.message, { id: tid });
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="modal-overlay"
            style={{ zIndex: 1000 }}
        >
            <motion.div
                initial={{ scale: 0.95, y: 20 }}
                animate={{ scale: 1, y: 0 }}
                exit={{ scale: 0.95, y: 20 }}
                className="modal-content glass-card"
                style={{
                    maxWidth: '1200px', width: '95%', padding: 0,
                    border: '1px solid var(--border-glow)', overflow: 'hidden',
                    maxHeight: '90vh', display: 'flex', flexDirection: 'column'
                }}
            >
                <div style={{ padding: '24px 32px', background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                        <div style={{ padding: '10px', borderRadius: '12px', background: 'var(--primary-glow)', color: 'var(--primary)' }}>
                            <ClipboardCheck size={24} />
                        </div>
                        <div>
                            <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 900 }}>Extraction Verification</h3>
                            <p style={{ margin: '2px 0 0', color: 'var(--text-muted)', fontSize: '13px' }}>Final human check to ensure 100% data fidelity</p>
                        </div>
                    </div>
                    <button className="btn btn-secondary" onClick={onClose} style={{ width: '36px', height: '36px', padding: 0, justifyContent: 'center', borderRadius: '50%' }}>
                        <X size={20} />
                    </button>
                </div>

                <div style={{ flex: 1, overflowY: 'auto', padding: '32px' }}>
                    {loading ? (
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '100px 0', gap: '20px' }}>
                            <Loader2 className="anim-spin" size={40} style={{ color: 'var(--primary)' }} />
                            <span style={{ color: 'var(--text-muted)', fontSize: '14px' }}>Analyzing OCR data points...</span>
                        </div>
                    ) : (
                        <div className="table-container" style={{ borderRadius: '12px', border: '1px solid var(--border)' }}>
                            <table style={{ borderCollapse: 'collapse' }}>
                                <thead>
                                    <tr>
                                        <th style={{ padding: '12px 16px' }}>Product Description</th>
                                        <th>HSN</th>
                                        <th>Batch</th>
                                        <th style={{ width: '100px' }}>Expiry</th>
                                        <th style={{ width: '100px' }}>Qty</th>
                                        <th style={{ width: '120px' }}>Rate (₹)</th>
                                        <th style={{ width: '140px' }}>Total (₹)</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {items.map((item, i) => (
                                        <tr key={item.id} style={{ borderBottom: '1px solid var(--border)' }}>
                                            <td style={{ padding: '12px 16px' }}>
                                                <input
                                                    className="form-input"
                                                    value={item.raw_description || ''}
                                                    onChange={e => handleChange(i, 'raw_description', e.target.value)}
                                                    style={{ background: 'transparent', border: 'none', padding: 0, height: 'auto', fontWeight: 600, width: '100%' }}
                                                />
                                            </td>
                                            <td>
                                                <input className="form-input text-xs" value={item.hsn_code || ''} onChange={e => handleChange(i, 'hsn_code', e.target.value)} style={{ background: 'transparent', border: 'none', padding: 0, height: 'auto', width: '100%' }} />
                                            </td>
                                            <td>
                                                <input className="form-input text-xs" value={item.batch_number || ''} onChange={e => handleChange(i, 'batch_number', e.target.value)} style={{ background: 'transparent', border: 'none', padding: 0, height: 'auto', width: '100%' }} />
                                            </td>
                                            <td>
                                                <input className="form-input text-xs" value={item.expiry_date || ''} placeholder="MM/YY" onChange={e => handleChange(i, 'expiry_date', e.target.value)} style={{ background: 'transparent', border: 'none', padding: 0, height: 'auto', width: '100%' }} />
                                            </td>
                                            <td>
                                                <input className="form-input text-xs" type="number" value={item.quantity} onChange={e => handleChange(i, 'quantity', e.target.value)} style={{ background: 'transparent', border: 'none', padding: 0, height: 'auto', width: '100%' }} />
                                            </td>
                                            <td>
                                                <input className="form-input text-xs" type="number" value={item.unit_price} onChange={e => handleChange(i, 'unit_price', e.target.value)} style={{ background: 'transparent', border: 'none', padding: 0, height: 'auto', width: '100%', fontWeight: 700 }} />
                                            </td>
                                            <td style={{ fontWeight: 800, color: 'var(--text-primary)' }}>
                                                ₹{(item.total_price || 0).toLocaleString()}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>

                <div style={{ padding: '24px 32px', background: 'var(--bg-secondary)', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'flex-end', gap: '16px' }}>
                    <button className="btn btn-secondary" onClick={onClose} disabled={submitting} style={{ borderRadius: '12px', minWidth: '120px' }}>
                        Discard changes
                    </button>
                    <button className="btn btn-primary" onClick={handleVerify} disabled={submitting || loading} style={{ borderRadius: '12px', padding: '12px 32px' }}>
                        {submitting ? <Loader2 className="anim-spin" size={20} /> : <><CheckCircle size={18} /> Confirm & Verify</>}
                    </button>
                </div>
            </motion.div>
        </motion.div>
    );
}

