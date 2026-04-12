import { create } from 'zustand'
import { createAuthSlice, type AuthState } from './slices/authSlice'
import { createNotificationSlice, type NotificationState } from './slices/notificationSlice'
import { createUiSlice, type UiState } from './slices/uiSlice'

type StoreState = AuthState & NotificationState & UiState

export const useStore = create<StoreState>((set) => ({
  ...createAuthSlice(set as (fn: (s: AuthState) => Partial<AuthState>) => void),
  ...createNotificationSlice(set as (fn: (s: NotificationState) => Partial<NotificationState>) => void),
  ...createUiSlice(set as (fn: (s: UiState) => Partial<UiState>) => void),
}))
