import type { HTMLAttributes, ReactNode } from 'react'

type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  children: ReactNode
  variant?: 'default' | 'role'
}

export default function Badge({ children, variant = 'default', className, ...props }: BadgeProps) {
  const variantClass = variant === 'role' ? 'badge--role' : undefined
  const combinedClassName = ['badge', variantClass, className].filter(Boolean).join(' ')
  return (
    <span className={combinedClassName} {...props}>
      {children}
    </span>
  )
}
