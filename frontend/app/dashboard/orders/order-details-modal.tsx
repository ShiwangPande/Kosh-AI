'use client';

import { useState, useEffect } from 'react';
import { X, Printer } from 'lucide-react';
import api from '@/lib/api';

interface OrderItem {
    description: string;
    quantity: number;
    unit_price: number;
    product_id?: string;
}

interface Order {
    id: string;
    po_number: string;
    supplier_id: string;
    status: string;
    total_amount: number;
    created_at: string;
    expected_delivery_date?: string;
    items: OrderItem[];
    supplier?: { id: string; name: string };
}

export default function OrderDetailsModal({ order: initialOrder, onClose }: { order: any, onClose: () => void }) {
    const [order, setOrder] = useState<Order | null>(initialOrder);

    // Fetch full details to ensure we have supplier info for print
    useEffect(() => {
        if (initialOrder?.id) {
            api.getOrder(initialOrder.id)
                .then((data: any) => setOrder(data))
                .catch(err => console.error("Failed to fetch order details", err));
        }
    }, [initialOrder]);

    // Update document title for print filename
    useEffect(() => {
        const originalTitle = document.title;
        if (order) {
            const supplierName = order.supplier?.name || 'Unknown Supplier';
            document.title = `${supplierName} - ${order.po_number}`;
        }
        return () => {
            document.title = originalTitle;
        };
    }, [order]);

    const printOrder = () => {
        window.print();
    };

    if (!order) return null;

    return (
        <div style={{
            position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }}>
            {/* ─── SCREEN VIEW ─── */}
            <div className="card print-hide" style={{ width: '800px', maxHeight: '90vh', display: 'flex', flexDirection: 'column' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid var(--border)', paddingBottom: '16px' }}>
                    <div>
                        <h3 className="card-title" style={{ marginBottom: '4px', fontSize: '24px' }}>{order.po_number}</h3>
                        <div style={{ color: 'var(--text-muted)', fontSize: '14px' }}>
                            Created on {new Date(order.created_at).toLocaleDateString()}
                        </div>
                    </div>
                    <div style={{ display: 'flex', gap: '8px' }}>
                        <button className="btn btn-secondary btn-sm" onClick={printOrder}>
                            <Printer size={16} /> Print
                        </button>
                        <button className="btn btn-secondary btn-sm" onClick={onClose}>
                            <X size={18} />
                        </button>
                    </div>
                </div>

                <div style={{ overflowY: 'auto', flex: 1, paddingRight: '8px' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
                        <div>
                            <h4 style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>Supplier</h4>
                            <div style={{ fontWeight: 600 }}>{order.supplier?.name || order.supplier_id}</div>
                        </div>
                        <div>
                            <h4 style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>Details</h4>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                                <span>Status:</span>
                                <span className={`badge badge-secondary`} style={{ textTransform: 'uppercase', fontSize: '10px' }}>{order.status}</span>
                            </div>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                                <span>Expected Delivery:</span>
                                <span>{order.expected_delivery_date ? new Date(order.expected_delivery_date).toLocaleDateString() : '—'}</span>
                            </div>
                        </div>
                    </div>

                    <div className="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Description</th>
                                    <th style={{ textAlign: 'right' }}>Qty</th>
                                    <th style={{ textAlign: 'right' }}>Unit Price</th>
                                    <th style={{ textAlign: 'right' }}>Total</th>
                                </tr>
                            </thead>
                            <tbody>
                                {order.items.map((item, idx) => (
                                    <tr key={idx}>
                                        <td>
                                            <div style={{ fontWeight: 500 }}>{item.description}</div>
                                        </td>
                                        <td style={{ textAlign: 'right' }}>{item.quantity}</td>
                                        <td style={{ textAlign: 'right' }}>₹{item.unit_price?.toLocaleString()}</td>
                                        <td style={{ textAlign: 'right' }}>₹{(item.quantity * item.unit_price)?.toLocaleString()}</td>
                                    </tr>
                                ))}
                            </tbody>
                            <tfoot>
                                <tr style={{ borderTop: '2px solid var(--border)' }}>
                                    <td colSpan={3} style={{ textAlign: 'right', fontWeight: 700 }}>Total Result</td>
                                    <td style={{ textAlign: 'right', fontWeight: 700, fontSize: '16px' }}>
                                        ₹{order.total_amount?.toLocaleString()}
                                    </td>
                                </tr>
                            </tfoot>
                        </table>
                    </div>
                </div>

                <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '1px solid var(--border)', textAlign: 'right' }}>
                    <button className="btn btn-primary" onClick={onClose}>Close</button>
                </div>
            </div>

            {/* ─── PRINT ONLY VIEW ─── */}
            <div className="print-only print-area" style={{ padding: '40px', fontFamily: 'serif', color: 'black' }}>
                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '60px', borderBottom: '2px solid black', paddingBottom: '20px' }}>
                    <div>
                        <h1 style={{ fontSize: '42px', fontWeight: 900, margin: 0, letterSpacing: '-1px' }}>PURCHASE ORDER</h1>
                        <div style={{ fontSize: '14px', marginTop: '8px', opacity: 0.7 }}>Kosh-AI Procurement Intelligence</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '18px', fontWeight: 700 }}>{order.po_number}</div>
                        <div style={{ fontSize: '14px' }}>Date: {new Date(order.created_at).toLocaleDateString()}</div>
                    </div>
                </div>

                {/* Info Grid */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '60px', marginBottom: '60px' }}>
                    <div>
                        <h3 style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '1px', borderBottom: '1px solid #ccc', paddingBottom: '8px', marginBottom: '16px' }}>Vendor</h3>
                        <div style={{ fontSize: '16px', fontWeight: 700, marginBottom: '4px' }}>{order.supplier?.name || order.supplier_id}</div>
                        <div style={{ fontSize: '14px', lineHeight: '1.5' }}>
                            Supplier ID: #{order.supplier_id.substring(0, 8)}<br />
                            Generated via Kosh-AI Network
                        </div>
                    </div>
                    <div>
                        <h3 style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '1px', borderBottom: '1px solid #ccc', paddingBottom: '8px', marginBottom: '16px' }}>Order Details</h3>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', borderBottom: '1px dashed #eee', paddingBottom: '4px' }}>
                            <span style={{ fontSize: '14px' }}>Expected Delivery:</span>
                            <span style={{ fontWeight: 600 }}>{order.expected_delivery_date ? new Date(order.expected_delivery_date).toLocaleDateString() : 'Immediate'}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', borderBottom: '1px dashed #eee', paddingBottom: '4px' }}>
                            <span style={{ fontSize: '14px' }}>Payment Terms:</span>
                            <span style={{ fontWeight: 600 }}>Net 30</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                            <span style={{ fontSize: '14px' }}>Status:</span>
                            <span style={{ fontWeight: 600, textTransform: 'uppercase' }}>{order.status}</span>
                        </div>
                    </div>
                </div>

                {/* Table */}
                <table style={{ width: '100%', borderCollapse: 'collapse', marginBottom: '40px' }}>
                    <thead>
                        <tr style={{ background: '#f5f5f5' }}>
                            <th style={{ textAlign: 'left', padding: '12px', borderBottom: '2px solid black', fontSize: '12px', textTransform: 'uppercase' }}>Item Description</th>
                            <th style={{ textAlign: 'center', padding: '12px', borderBottom: '2px solid black', fontSize: '12px', textTransform: 'uppercase', width: '80px' }}>Qty</th>
                            <th style={{ textAlign: 'right', padding: '12px', borderBottom: '2px solid black', fontSize: '12px', textTransform: 'uppercase', width: '120px' }}>Unit Price</th>
                            <th style={{ textAlign: 'right', padding: '12px', borderBottom: '2px solid black', fontSize: '12px', textTransform: 'uppercase', width: '120px' }}>Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        {order.items.map((item, idx) => (
                            <tr key={idx}>
                                <td style={{ padding: '16px 12px', borderBottom: '1px solid #eee' }}>
                                    <div style={{ fontWeight: 600, fontSize: '14px' }}>{item.description}</div>
                                    <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>SKU: {item.product_id ? item.product_id.substring(0, 8) : 'N/A'}</div>
                                </td>
                                <td style={{ textAlign: 'center', padding: '16px 12px', borderBottom: '1px solid #eee' }}>{item.quantity}</td>
                                <td style={{ textAlign: 'right', padding: '16px 12px', borderBottom: '1px solid #eee' }}>₹{item.unit_price?.toLocaleString()}</td>
                                <td style={{ textAlign: 'right', padding: '16px 12px', borderBottom: '1px solid #eee', fontWeight: 600 }}>₹{(item.quantity * item.unit_price)?.toLocaleString()}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>

                {/* Footer Totals */}
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '80px' }}>
                    <div style={{ width: '250px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px', paddingBottom: '12px', borderBottom: '1px solid #eee' }}>
                            <span>Subtotal:</span>
                            <span>₹{order.total_amount?.toLocaleString()}</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px', paddingBottom: '12px', borderBottom: '1px solid #eee' }}>
                            <span>Tax (0%):</span>
                            <span>₹0.00</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '20px', fontWeight: 900, borderTop: '2px solid black', paddingTop: '16px' }}>
                            <span>Total:</span>
                            <span>₹{order.total_amount?.toLocaleString()}</span>
                        </div>
                    </div>
                </div>

                {/* Authorization */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '40px', marginTop: 'auto' }}>
                    <div>
                        <div style={{ height: '60px', borderBottom: '1px solid black', marginBottom: '8px' }}></div>
                        <div style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '1px' }}>Authorized Signature</div>
                    </div>
                    <div>
                        <div style={{ height: '60px', borderBottom: '1px solid black', marginBottom: '8px' }}></div>
                        <div style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '1px' }}>Date</div>
                    </div>
                </div>
            </div>
        </div>
    );
}
