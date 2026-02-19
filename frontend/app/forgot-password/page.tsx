'use client';
import { useState } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import { ArrowLeft, CheckCircle, Mail } from 'lucide-react';

export default function ForgotPasswordPage() {
    const [email, setEmail] = useState('');
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            await api.forgotPassword(email);
            setSuccess(true);
        } catch (err: any) {
            setError(err.message || 'Something went wrong');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-card animate-in">
                <div className="logo">⬡ Kosh-AI</div>

                {success ? (
                    <div style={{ textAlign: 'center' }}>
                        <div style={{
                            width: '64px', height: '64px', borderRadius: '50%',
                            background: 'rgba(16, 185, 129, 0.1)', color: 'var(--success)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            margin: '0 auto 24px'
                        }}>
                            <CheckCircle size={32} />
                        </div>
                        <h2>Check your email</h2>
                        <p className="subtitle" style={{ maxWidth: '300px', margin: '16px auto' }}>
                            We've sent a 6-digit OTP to <strong>{email}</strong>.
                            Please use it to reset your password.
                        </p>
                        <Link href={`/reset-password?email=${encodeURIComponent(email)}`} className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}>
                            Verify OTP & Reset Password
                        </Link>
                        <button
                            className="btn-link"
                            onClick={() => setSuccess(false)}
                            style={{ display: 'block', width: '100%', marginTop: '16px', color: 'var(--text-muted)', fontSize: '13px' }}
                        >
                            Try another email
                        </button>
                    </div>
                ) : (
                    <>
                        <h1>Reset Password</h1>
                        <p className="subtitle">Enter your email to receive an OTP</p>

                        {error && (
                            <div className="badge badge-error" style={{ width: '100%', padding: '12px', marginBottom: '20px', borderRadius: '8px', justifyContent: 'center' }}>
                                {error}
                            </div>
                        )}

                        <form onSubmit={handleSubmit}>
                            <div className="form-group">
                                <label className="form-label">Email Address</label>
                                <div style={{ position: 'relative' }}>
                                    <Mail size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                                    <input
                                        className="form-input"
                                        type="email"
                                        required
                                        placeholder="you@company.com"
                                        value={email}
                                        onChange={e => setEmail(e.target.value)}
                                        style={{ paddingLeft: '38px' }}
                                    />
                                </div>
                            </div>

                            <button type="submit" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }} disabled={loading}>
                                {loading ? 'Sending OTP...' : 'Send OTP'}
                            </button>
                        </form>

                        <div style={{ marginTop: '24px', textAlign: 'center' }}>
                            <Link href="/login" className="btn-link" style={{ fontSize: '14px', color: 'var(--text-secondary)', display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                                <ArrowLeft size={16} /> Back to Login
                            </Link>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
