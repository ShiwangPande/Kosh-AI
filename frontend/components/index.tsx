'use client';

import { ReactNode, useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
    AlertCircle,
    CheckCircle2,
    Info,
    ChevronRight,
    Loader2,
    Plus,
    LayoutDashboard
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { ContextHelp } from './context-help';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface PageHeaderProps {
    title: string;
    subtitle?: ReactNode;
    actions?: ReactNode;
    breadcrumb?: { label: string; href?: string }[];
    helpSlug?: string;
}

export function PageHeader({ title, subtitle, actions, breadcrumb, helpSlug }: PageHeaderProps) {
    return (
        <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="page-header"
        >
            {breadcrumb && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                    <LayoutDashboard size={14} style={{ color: 'var(--text-muted)' }} />
                    {breadcrumb.map((item, i) => (
                        <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <ChevronRight size={14} style={{ color: 'var(--text-muted)' }} />
                            <span style={{ fontSize: '13px', color: item.href ? 'var(--text-muted)' : 'var(--text-primary)', fontWeight: item.href ? 500 : 700 }}>
                                {item.label}
                            </span>
                        </div>
                    ))}
                </div>
            )}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', gap: '16px' }}>
                <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <h1 style={{ margin: 0 }}>{title}</h1>
                        {helpSlug && <ContextHelp slug={helpSlug} label="Explain this" />}
                    </div>
                    {subtitle && <div style={{ margin: '4px 0 0', color: 'var(--text-muted)', fontSize: '14px' }}>{subtitle}</div>}
                </div>
                {actions && <div style={{ display: 'flex', gap: '12px' }}>{actions}</div>}
            </div>
            <div style={{ height: '1px', background: 'var(--border)', width: '100%', marginTop: '24px' }} />
        </motion.div>
    );
}

// ── Score Bar ──────────────────────────────────────────────

interface ScoreBarProps {
    value: number; // 0-1
    label?: string;
    width?: string;
}

export function ScoreBar({ value, label, width = '100%' }: ScoreBarProps) {
    const percent = Math.round(value * 100);
    return (
        <div style={{ width }}>
            {label && (
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                    <span style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: 500 }}>{label}</span>
                    <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--primary)' }}>{percent}%</span>
                </div>
            )}
            <div className="score-bar" style={{ height: '6px', background: 'var(--bg-primary)', overflow: 'hidden' }}>
                <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${percent}%` }}
                    transition={{ duration: 1, ease: 'easeOut' }}
                    className="score-fill"
                    style={{ height: '100%', borderRadius: '4px' }}
                />
            </div>
        </div>
    );
}

// ── Empty State ───────────────────────────────────────────

interface EmptyStateProps {
    icon?: ReactNode;
    title: string;
    description: string;
    action?: ReactNode;
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass-card"
            style={{
                textAlign: 'center',
                padding: '100px 48px',
                alignItems: 'center',
                justifyContent: 'center',
                background: 'var(--bg-glass)',
                border: '1px dashed var(--border-glow)',
                margin: '24px 0'
            }}
        >
            <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', damping: 12, stiffness: 200 }}
                style={{
                    width: '96px', height: '96px', borderRadius: '32px',
                    background: 'var(--primary-glow)', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    marginBottom: '32px', color: 'var(--primary)',
                    boxShadow: '0 20px 40px hsla(var(--p) / 0.1)'
                }}
            >
                {icon || <AlertCircle size={48} />}
            </motion.div>
            <h3 style={{ fontSize: '24px', fontWeight: 900, marginBottom: '16px', letterSpacing: '-0.5px' }}>{title}</h3>
            <p style={{ color: 'var(--text-muted)', maxWidth: '400px', margin: '0 auto 40px', lineHeight: 1.7, fontSize: '15px' }}>
                {description}
            </p>
            <div style={{ transform: 'scale(1.1)' }}>
                {action}
            </div>
        </motion.div>
    );
}

// ── Stat Card ─────────────────────────────────────────────

interface StatCardProps {
    label: string;
    value: string | number;
    color?: string;
    icon?: ReactNode;
    trend?: { value: string; positive: boolean };
    tooltip?: string;
    shimmerDelay?: number;
}

export function StatCard({ label, value, color = 'var(--primary)', icon, trend, tooltip, shimmerDelay = 0 }: StatCardProps) {
    const isNumeric = typeof value === 'number' || (typeof value === 'string' && !isNaN(parseFloat(value.replace(/[^0-9.-]/g, ''))));
    const numericValue = typeof value === 'number' ? value : parseFloat(String(value).replace(/[^0-9.-]/g, ''));
    const prefix = typeof value === 'string' && value.includes('₹') ? '₹' : '';

    const [pulse, setPulse] = useState(false);
    const [sweep, setSweep] = useState(false);

    useEffect(() => {
        setPulse(true);
        setSweep(true);
        const timer = setTimeout(() => setPulse(false), 700);
        const sweepTimer = setTimeout(() => setSweep(false), 600);
        return () => {
            clearTimeout(timer);
            clearTimeout(sweepTimer);
        };
    }, [value]);

    return (
        <motion.div
            whileHover={{ y: -4, boxShadow: 'var(--shadow-lg)' }}
            className={`stat-card glass-card pulse-glow shimmer-sweep`}
            style={{ animationDelay: `${shimmerDelay}ms` } as any}
        >
            {sweep && <div className="glow-sweep" />}

            {/* Sparkline Background */}
            <div className="sparkline-bg">
                <svg width="100%" height="100%" viewBox="0 0 100 40" preserveAspectRatio="none">
                    <motion.path
                        d="M0 35 Q 20 15, 40 25 T 80 10 L 100 20 L 100 40 L 0 40 Z"
                        fill={color}
                        initial={{ opacity: 0, pathLength: 0 }}
                        animate={{ opacity: 0.1, pathLength: 1 }}
                        transition={{ duration: 2, ease: "easeInOut" }}
                    />
                </svg>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', position: 'relative', zIndex: 1 }}>
                <div>
                    <div className="stat-label" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        {label}
                        {tooltip && (
                            <div className="tooltip-trigger" style={{ cursor: 'help' }}>
                                <Info size={12} style={{ opacity: 0.5 }} />
                                <div className="tooltip-content" style={{ minWidth: '200px', whiteSpace: 'normal', lineHeight: '1.4' }}>
                                    <div style={{ color: 'var(--primary)', fontWeight: 800, marginBottom: '4px', fontSize: '10px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>AI Reasoning</div>
                                    {tooltip}
                                </div>
                            </div>
                        )}
                    </div>
                    <div className={`stat-value ${pulse ? 'value-pulse' : ''}`} style={{
                        background: `linear-gradient(135deg, var(--text-primary), ${color})`,
                        WebkitBackgroundClip: 'text',
                        WebkitTextFillColor: 'transparent',
                    }}>
                        {isNumeric ? (
                            <motion.span
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                            >
                                {prefix}
                                <CountUp value={numericValue} />
                            </motion.span>
                        ) : value}
                    </div>
                    {trend && (
                        <div style={{
                            fontSize: '12px', fontWeight: 600, marginTop: '8px',
                            color: trend.positive ? 'var(--success)' : 'var(--error)',
                            display: 'flex', alignItems: 'center', gap: '4px'
                        }}>
                            {trend.positive ? '+' : ''}{trend.value} from last month
                        </div>
                    )}
                </div>
                <div style={{
                    padding: '12px', borderRadius: '12px', background: 'var(--bg-hover)',
                    color: color, display: 'flex', alignItems: 'center', justifyContent: 'center'
                }}>
                    {icon || <Info size={20} />}
                </div>
            </div>
        </motion.div >
    );
}

function CountUp({ value }: { value: number }) {
    const [displayValue, setDisplayValue] = useState(0);

    useEffect(() => {
        let start = 0;
        const end = value;
        const duration = 900;
        const startTime = performance.now();

        const animate = (now: number) => {
            const progress = Math.min((now - startTime) / duration, 1);
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const current = Math.floor(start + (end - start) * easeOut);

            setDisplayValue(current);

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }, [value]);

    return <>{displayValue.toLocaleString()}</>;
}

// ── Loading Spinner ───────────────────────────────────────

export function Loading({ text = 'Preparing intelligence...' }: { text?: string }) {
    return (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '100px 40px', gap: '20px' }}>
            <div style={{ position: 'relative' }}>
                <Loader2 className="anim-spin" size={48} style={{ color: 'var(--primary)' }} />
                <div style={{
                    position: 'absolute', inset: -8, borderRadius: '50%',
                    border: '2px solid var(--primary)', opacity: 0.2, animation: 'pulse 2s infinite'
                }} />
            </div>
            <span style={{ color: 'var(--text-muted)', fontSize: '15px', fontWeight: 500, letterSpacing: '0.5px' }}>
                {text}
            </span>
        </div>
    );
}

// ── Pagination ────────────────────────────────────────────

export function Pagination({ page, totalPages, onPageChange }: { page: number, totalPages: number, onPageChange: (p: number) => void }) {
    if (totalPages <= 1) return null;

    return (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '12px', marginTop: '32px' }}>
            <button
                className="btn btn-secondary btn-sm"
                disabled={page <= 1}
                onClick={() => onPageChange(page - 1)}
                style={{ borderRadius: '12px' }}
            >
                Previous
            </button>
            <div style={{
                display: 'flex', gap: '4px', background: 'var(--bg-secondary)',
                padding: '4px', borderRadius: '14px', border: '1px solid var(--border)'
            }}>
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    const p = i + 1;
                    return (
                        <button
                            key={p}
                            onClick={() => onPageChange(p)}
                            style={{
                                width: '32px', height: '32px', borderRadius: '10px',
                                border: 'none', background: page === p ? 'var(--primary)' : 'transparent',
                                color: page === p ? 'white' : 'var(--text-muted)',
                                fontWeight: 700, fontSize: '13px', cursor: 'pointer',
                                transition: 'all 0.2s'
                            }}
                        >
                            {p}
                        </button>
                    );
                })}
            </div>
            <button
                className="btn btn-secondary btn-sm"
                disabled={page >= totalPages}
                onClick={() => onPageChange(page + 1)}
                style={{ borderRadius: '12px' }}
            >
                Next
            </button>
        </div>
    );
}

