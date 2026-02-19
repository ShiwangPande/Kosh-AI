'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { Lock, ShieldCheck, CheckCircle2, Eye, EyeOff, ArrowRight } from 'lucide-react';
import api from '@/lib/api';
import ThemeToggle from '@/components/theme-toggle';

export default function LoginPage() {
    const router = useRouter();
    const [isRegister, setIsRegister] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [showPassword, setShowPassword] = useState(false);

    const [form, setForm] = useState({
        email: '',
        password: '',
        business_name: '',
        phone: '',
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            if (isRegister) {
                await api.register({
                    email: form.email,
                    password: form.password,
                    business_name: form.business_name,
                    phone: form.phone,
                });
            }
            await api.login(form.email, form.password);
            router.push('/dashboard');
        } catch (err: any) {
            setError(err.message || 'Something went wrong');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-container">
            <div className="status-indicator">
                <div className="status-dot"></div>
                All systems operational
            </div>

            <div style={{ position: 'absolute', top: '24px', right: '24px' }}>
                <ThemeToggle />
            </div>

            <motion.div
                initial={{ opacity: 0, y: 12, scale: 0.96 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
                className="auth-card"
            >
                <div className="logo">⬡ Kosh-AI</div>
                <div className="brand-subtitle">AI Procurement Intelligence</div>

                <h1 style={{ fontSize: '28px', fontWeight: 900, letterSpacing: '-0.5px' }}>
                    {isRegister ? 'Create Account' : 'Welcome back'}
                </h1>
                <p className="subtitle" style={{ fontWeight: 600, fontSize: '15px', marginBottom: '32px' }}>
                    {isRegister
                        ? 'Start optimizing your procurement today'
                        : 'Procurement Intelligence Dashboard'}
                </p>

                <AnimatePresence mode="wait">
                    {error && (
                        <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            style={{
                                background: 'rgba(239,68,68,0.1)',
                                border: '1px solid rgba(239,68,68,0.3)',
                                borderRadius: '12px',
                                padding: '12px',
                                marginBottom: '24px',
                                color: '#ef4444',
                                fontSize: '13px',
                                textAlign: 'center',
                                fontWeight: 500
                            }}
                        >
                            {error}
                        </motion.div>
                    )}
                </AnimatePresence>

                <form onSubmit={handleSubmit}>
                    {isRegister && (
                        <div className="animate-in" style={{ animationDelay: '0.1s' }}>
                            <div className="form-group">
                                <label className="form-label">Business Name</label>
                                <input
                                    className="form-input"
                                    type="text"
                                    placeholder="Your Business Name"
                                    value={form.business_name}
                                    onChange={(e) => setForm({ ...form, business_name: e.target.value })}
                                    required
                                />
                            </div>
                            <div className="form-group">
                                <label className="form-label">Phone</label>
                                <input
                                    className="form-input"
                                    type="tel"
                                    placeholder="+91 9876543210"
                                    value={form.phone}
                                    onChange={(e) => setForm({ ...form, phone: e.target.value })}
                                />
                            </div>
                        </div>
                    )}

                    <div className="form-group">
                        <label className="form-label" style={{ fontWeight: 800 }}>Email Address</label>
                        <input
                            className="form-input"
                            type="email"
                            placeholder="you@business.com"
                            value={form.email}
                            onChange={(e) => setForm({ ...form, email: e.target.value })}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label" style={{ fontWeight: 800 }}>Security Password</label>
                        <div style={{ position: 'relative' }}>
                            <input
                                className="form-input"
                                type={showPassword ? "text" : "password"}
                                placeholder="••••••••"
                                value={form.password}
                                onChange={(e) => setForm({ ...form, password: e.target.value })}
                                required
                                minLength={8}
                                style={{ paddingRight: '45px' }}
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                style={{
                                    position: 'absolute',
                                    right: '12px',
                                    top: '50%',
                                    transform: 'translateY(-50%)',
                                    background: 'transparent',
                                    border: 'none',
                                    cursor: 'pointer',
                                    padding: '6px',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    color: 'var(--text-primary)',
                                    opacity: 0.7,
                                    transition: 'all 0.2s',
                                }}
                                onMouseEnter={(e) => {
                                    e.currentTarget.style.opacity = '1';
                                    e.currentTarget.style.color = 'var(--primary)';
                                }}
                                onMouseLeave={(e) => {
                                    e.currentTarget.style.opacity = '0.7';
                                    e.currentTarget.style.color = 'var(--text-primary)';
                                }}
                                aria-label={showPassword ? "Hide password" : "Show password"}
                            >
                                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                            </button>
                        </div>
                        <div style={{ textAlign: 'right', marginTop: '8px' }}>
                            <Link href="/forgot-password" style={{ fontSize: '13px', color: 'var(--primary)', textDecoration: 'none', fontWeight: 600 }}>
                                Forgot Password?
                            </Link>
                        </div>
                    </div>

                    <button
                        type="submit"
                        className="btn btn-primary"
                        disabled={loading}
                        style={{ width: '100%', justifyContent: 'center', marginTop: '16px', height: '48px', borderRadius: '14px', fontSize: '15px' }}
                    >
                        {loading ? (
                            <>
                                <div className="spinner-xs" style={{ marginRight: '8px' }}></div>
                                Signing in...
                            </>
                        ) : isRegister ? 'Create Account' : 'Sign In'}
                    </button>

                    <div className="trust-signals">
                        <span><Lock size={12} /> Secure login</span>
                        <span>•</span>
                        <span><ShieldCheck size={12} /> SOC2-ready</span>
                        <span>•</span>
                        <span><CheckCircle2 size={12} /> 10,000+ invoices</span>
                    </div>
                </form>

                <p style={{
                    textAlign: 'center',
                    marginTop: '32px',
                    fontSize: '14px',
                    color: 'var(--text-muted)',
                }}>
                    {isRegister ? 'Already have an account?' : "New to Kosh-AI?"}{' '}
                    <span
                        onClick={() => { setIsRegister(!isRegister); setError(''); }}
                        style={{ color: 'var(--primary-light)', cursor: 'pointer', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                    >
                        {isRegister ? 'Sign In' : (
                            <>Create account <ArrowRight size={14} /></>
                        )}
                    </span>
                </p>
            </motion.div>
        </div>
    );
}
