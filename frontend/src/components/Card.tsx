import type { ReactNode } from 'react'

type CardProps = {
  title?: ReactNode
  subtitle?: ReactNode
  headerAction?: ReactNode
  children: ReactNode
  className?: string
}

const getClassName = (base: string, extra?: string) => {
  return [base, extra].filter(Boolean).join(' ')
}

export default function Card({ title, subtitle, headerAction, children, className }: CardProps) {
  const hasHeader = title || subtitle || headerAction
  const headerClassName = headerAction ? 'card-header card-header--with-action' : 'card-header'

  return (
    <section className={getClassName('card', className)}>
      {hasHeader ? (
        <div className={headerClassName}>
          <div>
            {title ? <h3>{title}</h3> : null}
            {subtitle ? <p className="page-subtitle">{subtitle}</p> : null}
          </div>
          {headerAction ? <div>{headerAction}</div> : null}
        </div>
      ) : null}
      <div className="card-body">{children}</div>
    </section>
  )
}
