import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface OnboardingState {
  toneId: string | null;
  tpoList: string[];
  styleMoods: string[];
  budgetMin: number;
  budgetMax: number;
  setTone: (toneId: string) => void;
  setTpoList: (tpoList: string[]) => void;
  setStyleMoods: (moods: string[]) => void;
  setBudget: (min: number, max: number) => void;
  reset: () => void;
}

export const useOnboardingStore = create<OnboardingState>()(
  persist(
    (set) => ({
      toneId: null,
      tpoList: [],
      styleMoods: [],
      budgetMin: 0,
      budgetMax: 300000,
      setTone: (toneId) => set({ toneId }),
      setTpoList: (tpoList) => set({ tpoList }),
      setStyleMoods: (moods) => set({ styleMoods: moods }),
      setBudget: (min, max) => set({ budgetMin: min, budgetMax: max }),
      reset: () => set({ toneId: null, tpoList: [], styleMoods: [], budgetMin: 0, budgetMax: 300000 }),
    }),
    { name: 'colorfit-onboarding' }
  )
);
