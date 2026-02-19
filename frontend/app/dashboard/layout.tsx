'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/hooks';
import { motion, AnimatePresence } from 'framer-motion';
import {
    LayoutDashboard,
    FileText,
    Factory,
    Lightbulb,
    Settings,
    LogOut,
    Hexagon,
    Loader2,
    UserCircle,
    ShoppingCart,
    ChevronLeft,
    Menu
} from 'lucide-react';
import ThemeToggle from '@/components/theme-toggle';
import { OnboardingTourProvider } from '@/app/providers/onboarding-provider';

const navItems = [
    { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { href: '/dashboard/invoices', label: 'Invoices', icon: FileText },
    { href: '/dashboard/orders', label: 'Orders', icon: ShoppingCart },
    { href: '/dashboard/suppliers', label: 'Suppliers', icon: Factory },
    { href: '/dashboard/recommendations', label: 'Recommendations', icon: Lightbulb },
    { href: '/dashboard/admin', label: 'Admin', icon: Settings, adminOnly: true },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    const { user, loading, logout, isAdmin } = useAuth();
    const router = useRouter();
    const pathname = usePathname();
    const [isCollapsed, setIsCollapsed] = useState(false);

    useEffect(() => {
        if (!loading && !user) {
            router.push('/login');
        }
    }, [loading, user, router]);

    if (loading) {
        return (
            <div className="auth-container">
                <div style={{ position: 'relative' }}>
                    <Loader2 className="anim-spin" size={48} style={{ color: 'var(--primary)' }} />
                    <div style={{
                        position: 'absolute', inset: -10, borderRadius: '50%',
                        border: '2px solid var(--primary)', opacity: 0.1, animation: 'pulse 2s infinite'
                    }} />
                </div>
            </div>
        );
    }

    if (!user) return null;

    return (
        <OnboardingTourProvider>
            <div className="page-container">
                <motion.aside
                    initial={false}
                    animate={{ width: isCollapsed ? '80px' : '280px' }}
                    className="sidebar glass-card"
                    style={{
                        borderRight: '1px solid var(--border)',
                        borderRadius: 0,
                        zIndex: 50,
                        padding: isCollapsed ? '24px 12px' : '24px 20px'
                    }}
                >
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: isCollapsed ? 'center' : 'space-between',
                        marginBottom: '40px'
                    }}>
                        {!isCollapsed && (
                            <div className="sidebar-logo" style={{ display: 'flex', alignItems: 'center', gap: '12px', margin: 0 }}>
                                <div style={{
                                    padding: '8px', borderRadius: '10px', background: 'var(--primary-glow)',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center'
                                }}>
                                    <Hexagon size={20} style={{ color: 'var(--primary)' }} />
                                </div>
                                <span style={{ fontWeight: 900, fontSize: '20px', letterSpacing: '-0.5px' }}>Kosh AI</span>
                            </div>
                        )}
                        {isCollapsed && (
                            <div style={{
                                padding: '8px', borderRadius: '10px', background: 'var(--primary-glow)',
                                display: 'flex', alignItems: 'center', justifyContent: 'center'
                            }}>
                                <Hexagon size={24} style={{ color: 'var(--primary)' }} />
                            </div>
                        )}
                    </div>

                    <nav className="sidebar-nav" style={{ gap: '6px' }}>
                        {navItems
                            .filter((item) => !item.adminOnly || isAdmin)
                            .map((item) => {
                                const Icon = item.icon;
                                const isActive = pathname === item.href;
                                return (
                                    <Link
                                        key={item.href}
                                        href={item.href}
                                        className={`nav-link ${isActive ? 'active' : ''}`}
                                        style={{
                                            justifyContent: isCollapsed ? 'center' : 'flex-start',
                                            height: '46px',
                                            position: 'relative',
                                            overflow: 'hidden'
                                        }}
                                    >
                                        {isActive && (
                                            <motion.div
                                                layoutId="nav-glow"
                                                className="absolute inset-0 bg-primary-bg"
                                                style={{
                                                    position: 'absolute', inset: 0,
                                                    background: 'var(--primary-glow)', zIndex: -1
                                                }}
                                            />
                                        )}
                                        <Icon size={20} style={{
                                            minWidth: '20px',
                                            filter: isActive ? 'drop-shadow(0 0 8px var(--primary))' : 'none',
                                            color: isActive ? 'var(--primary)' : 'inherit'
                                        }} />
                                        {!isCollapsed && (
                                            <motion.span
                                                initial={{ opacity: 0, x: -10 }}
                                                animate={{ opacity: 1, x: 0 }}
                                            >
                                                {item.label}
                                            </motion.span>
                                        )}
                                    </Link>
                                );
                            })}
                    </nav>

                    <div style={{ borderTop: '1px solid var(--border)', paddingTop: '24px', marginTop: 'auto' }}>
                        {!isCollapsed && (
                            <div style={{ padding: '0 8px 16px' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px' }}>
                                    <div style={{
                                        width: '32px', height: '32px', borderRadius: '50%',
                                        background: 'var(--bg-hover)', display: 'flex', alignItems: 'center', justifyContent: 'center'
                                    }}>
                                        <UserCircle size={20} style={{ color: 'var(--primary)' }} />
                                    </div>
                                    <div style={{ overflow: 'hidden' }}>
                                        <div style={{ fontSize: '14px', fontWeight: 800, color: 'var(--text-primary)', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                                            {user.business_name || 'Merchant'}
                                        </div>
                                        <div style={{ fontSize: '11px', color: 'var(--text-muted)', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                                            {user.email}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                            <ThemeToggle style={{
                                width: '100%', justifyContent: isCollapsed ? 'center' : 'flex-start',
                                padding: '10px 12px', borderRadius: '12px'
                            }} />
                            <button
                                className="btn btn-secondary btn-sm"
                                onClick={logout}
                                style={{
                                    width: '100%',
                                    justifyContent: isCollapsed ? 'center' : 'flex-start',
                                    padding: '10px 12px',
                                    background: 'transparent',
                                    border: 'none',
                                    color: 'var(--error)',
                                    borderRadius: '12px'
                                }}
                            >
                                <LogOut size={18} /> {!isCollapsed && 'Sign Out'}
                            </button>
                        </div>

                        <button
                            onClick={() => setIsCollapsed(!isCollapsed)}
                            className="btn btn-secondary"
                            style={{
                                width: '100%', marginTop: '16px', borderRadius: '12px',
                                justifyContent: 'center', height: '36px', padding: 0
                            }}
                        >
                            {isCollapsed ? <Menu size={16} /> : <ChevronLeft size={16} />}
                        </button>
                    </div>
                </motion.aside>
                <main className="main-content" style={{ overflowY: 'auto', flex: 1 }}>
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={pathname}
                            initial={{ opacity: 0, y: 15 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -15 }}
                            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                            style={{ maxWidth: '1400px', margin: '0 auto', width: '100%' }}
                        >
                            {children}
                        </motion.div>
                    </AnimatePresence>
                </main>
            </div>
        </OnboardingTourProvider>
    );
}
