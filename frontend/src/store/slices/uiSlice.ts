export interface UiState {
  sidebarOpen: boolean
  setSidebarOpen: (val: boolean) => void
  toggleSidebar: () => void
}

export const createUiSlice = (set: (fn: (s: UiState) => Partial<UiState>) => void): UiState => ({
  sidebarOpen: true,
  setSidebarOpen: (val) => set(() => ({ sidebarOpen: val })),
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
})
