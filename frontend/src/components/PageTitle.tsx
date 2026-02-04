import type { ReactNode } from 'react'

type PageTitleProps = {
  title: ReactNode
  subtitle?: ReactNode
  actions?: ReactNode
  className?: string
}

const getClassName = (base: string, extra?: string) => {
  return [base, extra].filter(Boolean).join(' ')
}

export default function PageTitle({ title, subtitle, actions, className }: PageTitleProps) {
  return (
    <div className={getClassName('page-header', className)}>
      {actions ? (
        <div className="page-header-row">
          <div>
            <h2 className="page-title">{title}</h2>
            {subtitle ? <p className="page-subtitle">{subtitle}</p> : null}
          </div>
          {actions}
        </div>
      ) : (
        <>
          <h2 className="page-title">{title}</h2>
          {subtitle ? <p className="page-subtitle">{subtitle}</p> : null}
        </>
      )}
    </div>
  )
}
