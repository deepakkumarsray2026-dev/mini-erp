interface Props {
  title: string
  description?: string
  actions?: React.ReactNode
}

export function PageHeader({ title, description, actions }: Props) {
  return (
    <div className="flex items-start justify-between mb-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 tracking-tight">{title}</h2>
        {description && <p className="mt-0.5 text-sm text-gray-500">{description}</p>}
      </div>
      {actions && <div className="flex items-center gap-2.5 flex-shrink-0">{actions}</div>}
    </div>
  )
}
