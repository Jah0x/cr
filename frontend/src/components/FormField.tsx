import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from 'react'

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label?: ReactNode
  className?: string
}

type SelectProps = SelectHTMLAttributes<HTMLSelectElement> & {
  label?: ReactNode
  className?: string
}

type CheckboxProps = InputHTMLAttributes<HTMLInputElement> & {
  label?: ReactNode
  className?: string
}

const getClassName = (base: string, extra?: string) => {
  return [base, extra].filter(Boolean).join(' ')
}

export function Input({ label, className, ...props }: InputProps) {
  if (label) {
    return (
      <label className={getClassName('form-field', className)}>
        <span>{label}</span>
        <input {...props} />
      </label>
    )
  }

  return <input {...props} className={className} />
}

export function Select({ label, className, children, ...props }: SelectProps) {
  if (label) {
    return (
      <label className={getClassName('form-field', className)}>
        <span>{label}</span>
        <select {...props}>{children}</select>
      </label>
    )
  }

  return (
    <select {...props} className={className}>
      {children}
    </select>
  )
}

export function Checkbox({ label, className, ...props }: CheckboxProps) {
  return (
    <label className={getClassName('form-inline', className)}>
      <input type="checkbox" {...props} />
      {label ? <span>{label}</span> : null}
    </label>
  )
}
