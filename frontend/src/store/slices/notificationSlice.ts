export interface Notification {
  id: string
  type: 'success' | 'error' | 'info' | 'warning'
  message: string
}

export interface NotificationState {
  notifications: Notification[]
  addNotification: (n: Omit<Notification, 'id'>) => void
  removeNotification: (id: string) => void
}

export const createNotificationSlice = (
  set: (fn: (s: NotificationState) => Partial<NotificationState>) => void,
): NotificationState => ({
  notifications: [],
  addNotification: (n) =>
    set((s) => ({
      notifications: [...s.notifications, { ...n, id: crypto.randomUUID() }],
    })),
  removeNotification: (id) =>
    set((s) => ({ notifications: s.notifications.filter((n) => n.id !== id) })),
})
