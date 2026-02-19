'use client';
import { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import api from '@/lib/api';
import { ArrowLeft, CheckCircle, Key, Lock } from 'lucide-react';

function ResetPasswordForm() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const emailParam = searchParams.get('email') || '';

    const [form, setForm] = useState({
        email: emailParam,
        token: '',
        new_password: '',
        confirm_password: ''
    });

    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (form.new_password !== form.confirm_password) {
            setError("Passwords don't match");
            return;
        }

        if (form.new_password.length < 8) {
            setError("Password must be at least 8 characters");
            return;
        }

        setLoading(true);
        try {
            await api.resetPassword({
                email: form.email,
                token: form.token,
                new_password: form.new_password
            });
            setSuccess(true);
        } catch (err: any) {
            setError(err.message || 'Reset failed. Check OTP and try again.');
        } finally {
            setLoading(false);
        }
    };

    if (success) {
        return (
            <div className="auth-card animate-in" style={{ textAlign: 'center' }}>
                <div style={{
                    width: '64px', height: '64px', borderRadius: '50%',
                    background: 'rgba(16, 185, 129, 0.1)', color: 'var(--success)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    margin: '0 auto 24px'
                }}>
                    <CheckCircle size={32} />
                </div>
                <h1>Password Reset!</h1>
                <p className="subtitle">Your password has been successfully updated.</p>
                <Link href="/login" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }}>
                    Sign In Now
                </Link>
            </div>
        );
    }

    return (
        <div className="auth-card animate-in">
            <div className="logo">⬡ Kosh-AI</div>
            <h1>Set New Password</h1>
            <p className="subtitle">Enter the OTP sent to {form.email || 'your email'}</p>

            {error && (
                <div className="badge badge-error" style={{ width: '100%', padding: '12px', marginBottom: '20px', borderRadius: '8px', justifyContent: 'center' }}>
                    {error}
                </div>
            )}

            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label className="form-label">Email</label>
                    <input
                        className="form-input"
                        type="email"
                        required
                        value={form.email}
                        onChange={e => setForm({ ...form, email: e.target.value })}
                        disabled // Typically redundant if passed from URL, but good to show
                    />
                </div>

                <div className="form-group">
                    <label className="form-label">OTP Code</label>
                    <div style={{ position: 'relative' }}>
                        <Key size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                        <input
                            className="form-input"
                            type="text"
                            required
                            placeholder="123456"
                            value={form.token}
                            onChange={e => setForm({ ...form, token: e.target.value })}
                            style={{ paddingLeft: '38px', letterSpacing: '2px', fontWeight: 'bold' }}
                            maxLength={6}
                        />
                    </div>
                </div>

                <div className="form-group">
                    <label className="form-label">New Password</label>
                    <div style={{ position: 'relative' }}>
                        <Lock size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                        <input
                            className="form-input"
                            type="password"
                            required
                            placeholder="Min 8 characters"
                            value={form.new_password}
                            onChange={e => setForm({ ...form, new_password: e.target.value })}
                            style={{ paddingLeft: '38px' }}
                            minLength={8}
                        />
                    </div>
                </div>

                <div className="form-group">
                    <label className="form-label">Confirm Password</label>
                    <div style={{ position: 'relative' }}>
                        <Lock size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                        <input
                            className="form-input"
                            type="password"
                            required
                            placeholder="Confirm new password"
                            value={form.confirm_password}
                            onChange={e => setForm({ ...form, confirm_password: e.target.value })}
                            style={{ paddingLeft: '38px' }}
                        />
                    </div>
                </div>

                <button type="submit" className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }} disabled={loading}>
                    {loading ? 'Reseting...' : 'Reset Password'}
                </button>
            </form>

            <div style={{ marginTop: '24px', textAlign: 'center' }}>
                <Link href="/login" className="btn-link" style={{ fontSize: '14px', color: 'var(--text-secondary)', display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                    <ArrowLeft size={16} /> Back to Login
                </Link>
            </div>
        </div>
    );
}

export default function ResetPasswordPage() {
    return (
        <div className="auth-container">
            <Suspense fallback={<div>Loading...</div>}>
                <ResetPasswordForm />
            </Suspense>
        </div>
    );
}
