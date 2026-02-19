'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks';
import { usePathname, useRouter } from 'next/navigation';
import { toast } from 'react-hot-toast';
import OnboardingTour from '@/components/onboarding-tour';

interface OnboardingState {
    step: string;
    completed: boolean;
    skipped: boolean;
    completed_at: string | null;
    isLoading: boolean;
}

interface OnboardingContextType extends OnboardingState {
    refreshState: () => Promise<void>;
    advance: () => Promise<void>;
    completeStep: (step: string) => Promise<void>;
    skip: () => Promise<void>;
    reset: () => Promise<void>;
}

const OnboardingContext = createContext<OnboardingContextType | undefined>(undefined);

export function OnboardingTourProvider({ children }: { children: React.ReactNode }) {
    const { user } = useAuth();
    const [state, setState] = useState<OnboardingState>({
        step: 'WELCOME',
        completed: false,
        skipped: false,
        completed_at: null,
        isLoading: true
    });
    const pathname = usePathname();
    const router = useRouter();

    const fetchState = async () => {
        if (!user) return;
        try {
            const data = await api.getOnboardingState();
            setState({ ...data, isLoading: false });
        } catch (error: any) {
            console.error('Failed to fetch onboarding state', error);
            setState(prev => ({ ...prev, isLoading: false }));
            // Don't toast on initial fetch fail to avoid spam if just not logged in/network blip
        }
    };

    useEffect(() => {
        if (user) {
            fetchState();
        }
    }, [user]);

    const advance = async () => {
        try {
            const data = await api.advanceOnboardingStep();
            setState({ ...data, isLoading: false });
        } catch (error: any) {
            console.error('Failed to advance step', error);
            toast.error('Failed to advance tour: ' + (error.message || 'Unknown error'));
        }
    };

    const completeStep = async (step: string) => {
        try {
            const data = await api.completeOnboardingStep(step);
            setState({ ...data, isLoading: false });
        } catch (error: any) {
            console.error('Failed to complete step', step, error);
            toast.error('Failed to complete step: ' + (error.message || 'Unknown error'));
        }
    };

    const skip = async () => {
        try {
            const data = await api.skipOnboarding();
            setState({ ...data, isLoading: false });
        } catch (error: any) {
            console.error('Failed to skip onboarding', error);
            toast.error('Failed to skip tour: ' + (error.message || 'Unknown error'));
        }
    };

    const reset = async () => {
        try {
            const data = await api.resetOnboarding();
            setState({ ...data, isLoading: false });
        } catch (error: any) {
            console.error('Failed to reset onboarding', error);
            toast.error('Failed to reset tour: ' + (error.message || 'Unknown error'));
        }
    };

    return (
        <OnboardingContext.Provider value={{
            ...state,
            refreshState: fetchState,
            advance,
            completeStep,
            skip,
            reset
        }}>
            {children}
            {!state.isLoading && user && !state.completed && !state.skipped && (
                <OnboardingTour />
            )}
        </OnboardingContext.Provider>
    );
}

export const useOnboarding = () => {
    const context = useContext(OnboardingContext);
    if (!context) {
        throw new Error('useOnboarding must be used within OnboardingTourProvider');
    }
    return context;
};
