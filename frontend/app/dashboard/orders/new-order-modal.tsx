'use client';

import { useState, useEffect } from 'react';
import api from '@/lib/api';
import { Plus, Trash2, X, Loader2, Package, Calendar, User, ShoppingCart, IndianRupee, Briefcase } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'react-hot-toast';

interface Supplier {
    id: string;
    name: string;
}

interface Product {
    id: string;
    name: string;
    sku_code: string;
}

interface OrderItem {
    product_id: string;
    description: string;
    quantity: number;
    unit_price: number;
}

export function NewOrderModal({ onOrderCreated }: { onOrderCreated: () => void }) {
    const [open, setOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [suppliers, setSuppliers] = useState<Supplier[]>([]);
    const [products, setProducts] = useState<Product[]>([]);

    // Form Data
    const [selectedSupplierId, setSelectedSupplierId] = useState<string>('');
    const [poNumber, setPoNumber] = useState('');
    const [deliveryDate, setDeliveryDate] = useState('');
    const [items, setItems] = useState<OrderItem[]>([]);

    useEffect(() => {
        if (open) {
            fetchSuppliers();
            setItems([]);
            setSelectedSupplierId('');
            setPoNumber('');
            setDeliveryDate('');
        }
    }, [open]);

    useEffect(() => {
        if (selectedSupplierId) {
            fetchSupplierProducts(selectedSupplierId);
        } else {
            setProducts([]);
        }
    }, [selectedSupplierId]);

    const fetchSuppliers = async () => {
        try {
            const data: any = await api.getSuppliers({ per_page: '100', approved_only: 'true' });
            setSuppliers(data.items);
        } catch (e) {
            console.error("Failed to fetch suppliers", e);
        }
    };

    const fetchSupplierProducts = async (supplierId: string) => {
        try {
            const data: any = await api.getSupplierProducts(supplierId, { per_page: '100' });
            setProducts(data.items);
        } catch (e) {
            console.error("Failed to fetch products", e);
        }
    };

    const addItem = () => {
        setItems([...items, { product_id: '', description: '', quantity: 1, unit_price: 0 }]);
    };

    const removeItem = (index: number) => {
        const newItems = [...items];
        newItems.splice(index, 1);
        setItems(newItems);
    };

    const updateItem = (index: number, field: keyof OrderItem, value: any) => {
        const newItems = [...items];
        if (field === 'product_id') {
            const product = products.find(p => p.id === value);
            newItems[index].product_id = value;
            newItems[index].description = product ? product.name : '';
        } else {
            (newItems[index] as any)[field] = value;
        }
        setItems(newItems);
    };

    const handleSubmit = async () => {
        const tid = toast.loading('Dispatching procurement instruction...');
        setIsLoading(true);
        try {
            const payload = {
                supplier_id: selectedSupplierId,
                po_number: poNumber || null,
                expected_delivery_date: deliveryDate || null,
                items: items.map(item => ({
                    product_id: item.product_id || null,
                    description: item.description,
                    quantity: Number(item.quantity),
                    unit_price: Number(item.unit_price)
                }))
            };

            await api.createOrder(payload);
            toast.success('Order cycle initiated successfully.', { id: tid });
            setOpen(false);
            onOrderCreated();
        } catch (e: any) {
            toast.error(e.message || "Error creating order", { id: tid });
        } finally {
            setIsLoading(true); // Keep loading while closing for feel
            setTimeout(() => setIsLoading(false), 300);
        }
    };

    const totalAmount = items.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0);

    return (
        <>
            <button className="btn btn-primary" onClick={() => setOpen(true)} style={{ borderRadius: '12px', gap: '8px' }}>
                <Package size={18} /> Initiate Order
            </button>

            <AnimatePresence>
                {open && (
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
                                maxWidth: '1000px', width: '95%', padding: 0,
                                border: '1px solid var(--border-glow)', overflow: 'hidden',
                                maxHeight: '90vh', display: 'flex', flexDirection: 'column'
                            }}
                        >
                            <div style={{ padding: '24px 32px', background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                                    <div style={{ padding: '10px', borderRadius: '12px', background: 'var(--primary-glow)', color: 'var(--primary)' }}>
                                        <ShoppingCart size={24} />
                                    </div>
                                    <div>
                                        <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 900 }}>Procurement Instruction</h3>
                                        <p style={{ margin: '2px 0 0', color: 'var(--text-muted)', fontSize: '13px' }}>Configure fulfillment parameters and SKU selection</p>
                                    </div>
                                </div>
                                <button className="btn btn-secondary" onClick={() => setOpen(false)} style={{ width: '36px', height: '36px', padding: 0, justifyContent: 'center', borderRadius: '50%' }}>
                                    <X size={20} />
                                </button>
                            </div>

                            <div style={{ flex: 1, overflowY: 'auto', padding: '32px' }}>
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '24px', marginBottom: '32px' }}>
                                    <div className="form-group">
                                        <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                            <Briefcase size={14} /> Fulfillment Partner *
                                        </label>
                                        <select
                                            className="form-input"
                                            value={selectedSupplierId}
                                            onChange={(e) => setSelectedSupplierId(e.target.value)}
                                            style={{ height: '44px', borderRadius: '12px', background: 'var(--bg-glass)' }}
                                        >
                                            <option value="">Choose Supplier</option>
                                            {suppliers.map(s => (
                                                <option key={s.id} value={s.id}>{s.name}</option>
                                            ))}
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                            <Calendar size={14} /> Expected Delivery
                                        </label>
                                        <input
                                            className="form-input"
                                            type="date"
                                            value={deliveryDate}
                                            onChange={(e) => setDeliveryDate(e.target.value)}
                                            style={{ height: '44px', borderRadius: '12px', background: 'var(--bg-glass)' }}
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label className="form-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                            <Package size={14} /> PO Reference (Optional)
                                        </label>
                                        <input
                                            className="form-input"
                                            placeholder="System generated"
                                            value={poNumber}
                                            onChange={(e) => setPoNumber(e.target.value)}
                                            style={{ height: '44px', borderRadius: '12px', background: 'var(--bg-glass)' }}
                                        />
                                    </div>
                                </div>

                                <div style={{ borderTop: '1px solid var(--border)', paddingTop: '24px' }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                                        <h4 style={{ fontSize: '15px', fontWeight: 800, margin: 0 }}>Line Item Configuration</h4>
                                        <button
                                            className="btn btn-secondary btn-sm"
                                            onClick={addItem}
                                            disabled={!selectedSupplierId}
                                            style={{ borderRadius: '10px', height: '36px', gap: '8px' }}
                                        >
                                            <Plus size={16} /> Append Item
                                        </button>
                                    </div>

                                    {items.length === 0 ? (
                                        <div style={{ padding: '48px', textAlign: 'center', border: '2px dashed var(--border)', borderRadius: '16px', color: 'var(--text-muted)' }}>
                                            <div style={{ opacity: 0.3, marginBottom: '16px' }}><Package size={40} style={{ margin: '0 auto' }} /></div>
                                            <p style={{ margin: 0, fontSize: '14px' }}>Select a partner to begin SKU allocation.</p>
                                        </div>
                                    ) : (
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                            {items.map((item, idx) => (
                                                <motion.div
                                                    key={idx}
                                                    initial={{ opacity: 0, x: -10 }}
                                                    animate={{ opacity: 1, x: 0 }}
                                                    style={{
                                                        display: 'grid', gridTemplateColumns: 'minmax(200px, 3fr) minmax(150px, 2fr) 80px 120px 48px', gap: '16px',
                                                        alignItems: 'end', padding: '16px', background: 'var(--bg-secondary)', borderRadius: '14px',
                                                        border: '1px solid var(--border)'
                                                    }}
                                                >
                                                    <div className="form-group" style={{ marginBottom: 0 }}>
                                                        <label className="form-label" style={{ fontSize: '11px', fontWeight: 800 }}>SKU SELECTION</label>
                                                        <select
                                                            className="form-input"
                                                            style={{
                                                                height: '36px',
                                                                padding: '0 12px',
                                                                fontSize: '13px',
                                                                borderRadius: '8px',
                                                                background: 'var(--bg-secondary)',
                                                                color: 'var(--text-primary)'
                                                            }}
                                                            value={item.product_id}
                                                            onChange={(e) => updateItem(idx, 'product_id', e.target.value)}
                                                        >
                                                            <option value="">Unlisted / Custom</option>
                                                            {products.map(p => (
                                                                <option key={p.id} value={p.id}>{p.name}</option>
                                                            ))}
                                                        </select>
                                                    </div>
                                                    <div className="form-group" style={{ marginBottom: 0 }}>
                                                        <label className="form-label" style={{ fontSize: '11px', fontWeight: 800 }}>NOMENCLATURE</label>
                                                        <input
                                                            className="form-input"
                                                            style={{ height: '36px', padding: '0 12px', fontSize: '13px', borderRadius: '8px' }}
                                                            value={item.description}
                                                            onChange={(e) => updateItem(idx, 'description', e.target.value)}
                                                            placeholder="Item identifier"
                                                        />
                                                    </div>
                                                    <div className="form-group" style={{ marginBottom: 0 }}>
                                                        <label className="form-label" style={{ fontSize: '11px', fontWeight: 800 }}>QTY</label>
                                                        <input
                                                            className="form-input"
                                                            type="number" min="1"
                                                            style={{ height: '36px', padding: '0 12px', fontSize: '13px', borderRadius: '8px' }}
                                                            value={item.quantity}
                                                            onChange={(e) => updateItem(idx, 'quantity', parseFloat(e.target.value))}
                                                        />
                                                    </div>
                                                    <div className="form-group" style={{ marginBottom: 0 }}>
                                                        <label className="form-label" style={{ fontSize: '11px', fontWeight: 800 }}>VALUATION (₹)</label>
                                                        <input
                                                            className="form-input"
                                                            type="number" min="0" step="0.01"
                                                            style={{ height: '36px', padding: '0 12px', fontSize: '13px', borderRadius: '8px', fontWeight: 700 }}
                                                            value={item.unit_price}
                                                            onChange={(e) => updateItem(idx, 'unit_price', parseFloat(e.target.value))}
                                                        />
                                                    </div>
                                                    <button
                                                        className="btn"
                                                        style={{
                                                            color: 'var(--error)',
                                                            background: 'rgba(239, 68, 68, 0.1)',
                                                            border: '1px solid rgba(239, 68, 68, 0.2)',
                                                            height: '36px',
                                                            width: '36px',
                                                            padding: '8px',
                                                            display: 'flex',
                                                            alignItems: 'center',
                                                            justifyContent: 'center',
                                                            borderRadius: '10px',
                                                            justifySelf: 'center'
                                                        }}
                                                        onClick={() => removeItem(idx)}
                                                    >
                                                        <Trash2 size={16} />
                                                    </button>
                                                </motion.div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            </div>

                            <div style={{ padding: '24px 32px', background: 'var(--bg-secondary)', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div>
                                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600 }}>AGGREGATE VALUATION</div>
                                    <div style={{ fontSize: '24px', fontWeight: 900, color: 'var(--text-primary)' }}>
                                        ₹{totalAmount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                                    </div>
                                </div>
                                <div style={{ display: 'flex', gap: '16px' }}>
                                    <button className="btn btn-secondary" onClick={() => setOpen(false)} style={{ borderRadius: '12px', padding: '0 24px' }}>Discard</button>
                                    <button
                                        className="btn btn-primary"
                                        onClick={handleSubmit}
                                        disabled={isLoading || !selectedSupplierId || items.length === 0}
                                        style={{ borderRadius: '12px', padding: '0 32px', fontSize: '15px', fontWeight: 700 }}
                                    >
                                        {isLoading ? <Loader2 className="anim-spin" size={20} /> : 'Dispatch Instruction'}
                                    </button>
                                </div>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
}

