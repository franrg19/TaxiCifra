import type { ButtonHTMLAttributes } from 'react'

const VARIANTS = {
  primary: 'bg-amber-400 hover:bg-amber-500',
  secondary: 'border border-slate-300 bg-white hover:bg-slate-100',
  danger: 'bg-red-600 text-white hover:bg-red-700',
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: keyof typeof VARIANTS
}

/** Botón con el estilo de la aplicación. Por defecto no envía formularios. */
export function Button({
  variant = 'primary',
  className = '',
  type = 'button',
  ...buttonProps
}: ButtonProps) {
  return (
    <button
      type={type}
      className={`rounded-md px-4 py-2 font-semibold disabled:opacity-50 ${VARIANTS[variant]} ${className}`}
      {...buttonProps}
    />
  )
}
