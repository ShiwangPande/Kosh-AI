'use client';

import { useOnboarding } from '@/app/providers/onboarding-provider';
import { motion, AnimatePresence } from 'framer-motion';
import { X, CheckCircle, Upload, Lightbulb, Zap, ArrowRight } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function OnboardingTour() {
    const { step, advance, skip, completed, skipped } = useOnboarding();
    const router = useRouter();

    // Auto-navigation or focus based on step
    useEffect(() => {
        if (step === 'UPLOAD_INVOICE') {
            router.push('/dashboard/invoices');
        } else if (step === 'FIRST_RECOMMENDATION') {
            router.push('/dashboard/recommendations');
        }
    }, [step, router]);

    if (skipped) return null;
    if (completed && step !== 'COMPLETED') return null;

    const overlayVariants = {
        hidden: { opacity: 0 },
        visible: { opacity: 1, transition: { duration: 0.3 } },
        exit: { opacity: 0 }
    };

    const cardVariants = {
        hidden: { opacity: 0, y: 20, scale: 0.95 },
        visible: { opacity: 1, y: 0, scale: 1, transition: { type: 'spring' as const, stiffness: 300, damping: 25 } },
        exit: { opacity: 0, scale: 0.95, transition: { duration: 0.2 } }
    };

    // Component for reusable card
    const TourCard = ({ title, children, onNext, nextLabel = 'Next', showSkip = true }: any) => (
        <motion.div
            className="tour-card glass-card"
            variants={cardVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            style={{
                position: 'fixed',
                bottom: '40px',
                right: '40px',
                width: '360px',
                padding: '24px',
                borderRadius: '24px',
                background: 'rgba(20, 20, 30, 0.8)', // Dark/Glass
                backdropFilter: 'blur(16px)',
                border: '1px solid rgba(255, 255, 255, 0.1)',
                boxShadow: '0 20px 50px rgba(0, 0, 0, 0.3)',
                zIndex: 1000,
                color: 'white'
            }}
        >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 700, background: 'linear-gradient(to right, #fff, #aaa)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                    {title}
                </h3>
                {showSkip && (
                    <button
                        onClick={skip}
                        style={{ background: 'transparent', border: 'none', color: '#aaa', cursor: 'pointer', padding: '4px' }}
                    >
                        <X size={16} />
                    </button>
                )}
            </div>

            <div style={{ marginBottom: '24px', color: '#ccc', fontSize: '14px', lineHeight: '1.6' }}>
                {children}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
                <button
                    onClick={onNext}
                    style={{
                        background: 'linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%)',
                        color: 'white',
                        border: 'none',
                        padding: '10px 20px',
                        borderRadius: '12px',
                        fontWeight: 600,
                        fontSize: '14px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        boxShadow: '0 4px 15px rgba(var(--primary-rgb), 0.3)'
                    }}
                >
                    {nextLabel} <ArrowRight size={16} />
                </button>
            </div>
        </motion.div>
    );

    // Render Steps
    return (
        <AnimatePresence mode="wait">
            {step === 'WELCOME' && (
                <motion.div
                    key="welcome"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    style={{
                        position: 'fixed', inset: 0, zIndex: 1000,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(8px)'
                    }}
                >
                    <motion.div
                        variants={cardVariants}
                        initial="hidden"
                        animate="visible"
                        exit="exit"
                        style={{
                            maxWidth: '500px', width: '90%', padding: '40px',
                            borderRadius: '32px',
                            background: 'rgba(20, 20, 25, 0.9)',
                            border: '1px solid rgba(255,255,255,0.1)',
                            textAlign: 'center',
                            position: 'relative',
                            overflow: 'hidden'
                        }}
                    >
                        <div style={{
                            position: 'absolute', top: '-50px', left: '50%', transform: 'translateX(-50%)',
                            width: '200px', height: '200px', background: 'var(--primary)', opacity: 0.2, filter: 'blur(80px)', borderRadius: '50%'
                        }} />

                        <div style={{ marginBottom: '24px', display: 'inline-flex', padding: '16px', background: 'rgba(255,255,255,0.05)', borderRadius: '24px' }}>
                            <Zap size={48} style={{ color: 'var(--primary)' }} />
                        </div>

                        <h2 style={{ fontSize: '32px', fontWeight: 800, marginBottom: '16px', color: 'white' }}>
                            Welcome to Kosh AI
                        </h2>
                        <p style={{ fontSize: '16px', color: '#aaa', marginBottom: '32px', lineHeight: '1.6' }}>
                            We help you find hidden savings in your procurement. Let's get you to your first insight in under 2 minutes.
                        </p>

                        <button
                            onClick={advance}
                            style={{
                                width: '100%',
                                padding: '16px',
                                borderRadius: '16px',
                                background: 'var(--primary)',
                                color: 'white',
                                border: 'none',
                                fontSize: '16px',
                                fontWeight: 700,
                                cursor: 'pointer',
                                transition: 'transform 0.2s',
                            }}
                            onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.02)'}
                            onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1)'}
                        >
                            Start the Tour
                        </button>
                    </motion.div>
                </motion.div>
            )}

            {step === 'UPLOAD_INVOICE' && (
                <TourCard
                    key="upload"
                    title="Unlock Insights"
                    onNext={advance}
                    nextLabel="I'll do it later"
                >
                    <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                        <div style={{ padding: '10px', background: 'rgba(255,255,255,0.1)', borderRadius: '12px' }}>
                            <Upload size={24} className="text-primary" />
                        </div>
                        <p>Upload your first invoice. We'll extract line items and find savings instantly.</p>
                    </div>
                </TourCard>
            )}

            {step === 'INSIGHT_REVEAL' && (
                <TourCard
                    key="insight"
                    title="Analysis Complete"
                    onNext={advance}
                    nextLabel="See Recommendations"
                >
                    <p>We've analyzed your invoice. 3 potential savings found.</p>
                </TourCard>
            )}

            {step === 'FIRST_RECOMMENDATION' && (
                <TourCard
                    key="recommendation"
                    title="Smart Recommendation"
                    onNext={advance}
                    nextLabel="Show Me How"
                >
                    <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                        <div style={{ padding: '10px', background: 'rgba(255,255,255,0.1)', borderRadius: '12px' }}>
                            <Lightbulb size={24} className="text-yellow-400" />
                        </div>
                        <p>This item can be bought for 15% less from Supplier B.</p>
                    </div>
                </TourCard>
            )}

            {step === 'ACTION_DEMO' && (
                <TourCard
                    key="action"
                    title="Take Action"
                    onNext={advance}
                    nextLabel="Finish"
                >
                    <p>Click 'Accept' to add this to your next order list automatically.</p>
                </TourCard>
            )}

            {step === 'COMPLETED' && (
                <motion.div
                    key="success"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    style={{
                        position: 'fixed', inset: 0, zIndex: 1000,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(8px)'
                    }}
                >
                    <motion.div
                        initial={{ scale: 0.5, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        style={{ textAlign: 'center', color: 'white' }}
                    >
                        <CheckCircle size={80} style={{ color: '#4ade80', marginBottom: '24px' }} />
                        <h2 style={{ fontSize: '32px', fontWeight: 800 }}>You're all set!</h2>
                        <button onClick={skip} style={{ marginTop: '24px', padding: '12px 32px', borderRadius: '12px', background: 'white', color: 'black', border: 'none', fontWeight: 700, cursor: 'pointer' }}>
                            Go to Dashboard
                        </button>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
