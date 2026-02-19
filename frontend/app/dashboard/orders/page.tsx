'use client';

import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { NewOrderModal } from './new-order-modal';
import OrderDetailsModal from './order-details-modal';
import { ShoppingCart, Package, Eye, Filter, Search, Calendar, ChevronRight, IndianRupee, Clock, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-hot-toast';
import { PageHeader, StatCard, EmptyState } from '@/components';

interface Order {
    id: string;
    po_number: string;
    supplier_id: string;
    status: string;
    total_amount: number;
    created_at: string;
    items: any[];
    supplier?: { id: string; name: string };
}

export default function OrdersPage() {
    const [orders, setOrders] = useState<Order[]>([]);
    const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [search, setSearch] = useState('');

    useEffect(() => {
        fetchOrders();
    }, []);

    const fetchOrders = async () => {
        setIsLoading(true);
        try {
            const data: any = await api.getOrders({ page: '1', per_page: '50' });
            setOrders(data.items || []);
        } catch (error) {
            console.error("Failed to fetch orders", error);
        } finally {
            setIsLoading(false);
        }
    };

    const getStatusBadge = (status: string) => {
        const configs: Record<string, { class: string, icon: any }> = {
            completed: { class: 'badge-success', icon: CheckCircle2 },
            sent: { class: 'badge-primary', icon: Clock },
            partial: { class: 'badge-warning', icon: AlertCircle },
            draft: { class: 'badge-secondary', icon: Package },
            cancelled: { class: 'badge-error', icon: XCircle },
        };
        const conf = configs[status.toLowerCase()] || { class: 'badge-secondary', icon: Package };
        const Icon = conf.icon;
        return (
            <span className={`badge ${conf.class}`} style={{ gap: '6px', padding: '6px 12px' }}>
                <Icon size={12} />
                {status}
            </span>
        );
    };

    return (
        <div style={{ padding: '0 4px' }}>
            <PageHeader
                title="Purchase Orders"
                subtitle="Execute procurement cycles and track fulfillment in real-time"
                breadcrumb={[{ label: 'Dashboard', href: '/dashboard' }, { label: 'Orders' }]}
                actions={<NewOrderModal onOrderCreated={() => { fetchOrders(); toast.success('Order cycle initiated.'); }} />}
            />

            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4 }}
                style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px', marginBottom: '32px' }}
            >
                <StatCard
                    label="Active Procurement"
                    value={orders.filter(o => o.status !== 'completed' && o.status !== 'cancelled').length.toString()}
                    icon={<Package size={20} />}
                    color="var(--primary)"
                />
                <StatCard
                    label="Completed (Month)"
                    value={orders.filter(o => o.status === 'completed').length.toString()}
                    icon={<CheckCircle2 size={20} />}
                    color="var(--success)"
                />
                <StatCard
                    label="Pending Delivery"
                    value={orders.filter(o => o.status === 'sent').length.toString()}
                    icon={<Clock size={20} />}
                    color="var(--warning)"
                />
            </motion.div>

            <div className="table-container glass-card elevation-1" style={{ padding: 0, border: '1px solid var(--border-glow)' }}>
                <div style={{ padding: '24px 32px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'var(--bg-secondary)' }}>
                    <h3 className="card-title" style={{ marginBottom: 0, fontSize: '16px', fontWeight: 900 }}>Order Repository</h3>
                    <div style={{ position: 'relative', width: '320px' }}>
                        <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                        <input
                            className="form-input"
                            placeholder="Filter repo by PO or Entity..."
                            style={{ paddingLeft: '38px', borderRadius: '10px', background: 'var(--bg-glass)' }}
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>
                </div>

                {isLoading ? (
                    <div style={{ padding: '100px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
                        <div className="anim-pulse" style={{ width: '40px', height: '40px', background: 'var(--primary-glow)', borderRadius: '50%' }} />
                        <div style={{ color: 'var(--text-muted)', fontSize: '14px' }}>Syncing repository...</div>
                    </div>
                ) : (
                    <div className="table-container">
                        <table style={{ borderCollapse: 'collapse' }}>
                            <thead>
                                <tr>
                                    <th style={{ padding: '16px 24px' }}>PO Reference</th>
                                    <th>Fulfillment Partner</th>
                                    <th>Initiated</th>
                                    <th>Lifecycle Status</th>
                                    <th>Nominal Value</th>
                                    <th>SKU Count</th>
                                    <th style={{ textAlign: 'right', paddingRight: '24px' }}>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {orders.length === 0 ? (
                                    <tr>
                                        <td colSpan={7} style={{ padding: 0 }}>
                                            <EmptyState
                                                title="No Procurement Logs"
                                                description="Your order history is currently empty. Initiate a new cycle or check back after sync."
                                                icon={<Package size={40} />}
                                            />
                                        </td>
                                    </tr>
                                ) : (
                                    <AnimatePresence>
                                        {orders
                                            .filter(order => {
                                                if (!search) return true;
                                                const query = search.toLowerCase();
                                                return (
                                                    order.po_number?.toLowerCase().includes(query) ||
                                                    order.supplier?.name.toLowerCase().includes(query) ||
                                                    order.supplier_id.toLowerCase().includes(query)
                                                );
                                            })
                                            .map((order, idx) => (
                                                <motion.tr
                                                    key={order.id}
                                                    initial={{ opacity: 0, x: -10 }}
                                                    animate={{ opacity: 1, x: 0 }}
                                                    transition={{ delay: idx * 0.03 }}
                                                    style={{ cursor: 'pointer' }}
                                                >
                                                    <td style={{ padding: '16px 24px', fontWeight: 800, color: 'var(--primary)', letterSpacing: '0.4px' }}>
                                                        {order.po_number || 'TRX-' + order.id.slice(0, 4).toUpperCase()}
                                                    </td>
                                                    <td>
                                                        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                                            <div style={{ width: '28px', height: '28px', borderRadius: '8px', background: 'var(--bg-hover)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 800 }}>
                                                                {order.supplier?.name.charAt(0)}
                                                            </div>
                                                            <span style={{ fontWeight: 600 }}>{order.supplier?.name || 'Unknown Entity'}</span>
                                                        </div>
                                                    </td>
                                                    <td style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
                                                        {new Date(order.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}
                                                    </td>
                                                    <td>{getStatusBadge(order.status)}</td>
                                                    <td style={{ fontWeight: 800, color: 'var(--text-primary)' }}>
                                                        ₹{order.total_amount?.toLocaleString() || '0'}
                                                    </td>
                                                    <td style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                                                        {order.items?.length || 0} Products
                                                    </td>
                                                    <td style={{ textAlign: 'right', paddingRight: '24px' }}>
                                                        <button
                                                            className="btn btn-secondary btn-sm"
                                                            style={{ width: '36px', height: '36px', padding: 0, justifyContent: 'center', borderRadius: '10px' }}
                                                            onClick={() => setSelectedOrder(order)}
                                                        >
                                                            <Eye size={16} />
                                                        </button>
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
            {selectedOrder && (
                <OrderDetailsModal
                    order={selectedOrder}
                    onClose={() => setSelectedOrder(null)}
                />
            )}
        </div>
    );
}
