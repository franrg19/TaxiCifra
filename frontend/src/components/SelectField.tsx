import type { SelectHTMLAttributes } from 'react'

interface SelectFieldProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string
}

/** Desplegable con su etiqueta. Las opciones se pasan como hijos. */
export function SelectField({ label, id, ...selectProps }: SelectFieldProps) {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium text-slate-700">
        {label}
      </label>
      <select
        id={id}
        className="mt-1 w-full rounded-md border border-slate-300 bg-white px-3 py-2 focus:border-amber-500 focus:ring-2 focus:ring-amber-200 focus:outline-none"
        {...selectProps}
      />
    </div>
  )
}
