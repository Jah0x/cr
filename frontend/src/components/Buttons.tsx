import type { ButtonHTMLAttributes, ReactNode } from 'react'

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger'

type BaseButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant
  children: ReactNode
}

const getClassName = (variant: ButtonVariant) => {
  if (variant === 'primary') return undefined
  return variant
}

export function Button({ variant = 'primary', className, ...props }: BaseButtonProps) {
  const variantClass = getClassName(variant)
  const combinedClassName = [variantClass, className].filter(Boolean).join(' ') || undefined

  return <button {...props} className={combinedClassName} />
}

export function PrimaryButton(props: BaseButtonProps) {
  return <Button {...props} variant="primary" />
}

export function SecondaryButton(props: BaseButtonProps) {
  return <Button {...props} variant="secondary" />
}
