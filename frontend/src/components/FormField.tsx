import type { InputHTMLAttributes } from 'react'

interface FormFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
}

/** Campo de formulario con su etiqueta. Acepta cualquier atributo de un <input>. */
export function FormField({ label, id, ...inputProps }: FormFieldProps) {
  return (
    <div>
      <label htmlFor={id} className="block text-sm font-medium text-slate-700">
        {label}
      </label>
      <input
        id={id}
        className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 focus:border-amber-500 focus:ring-2 focus:ring-amber-200 focus:outline-none"
        {...inputProps}
      />
    </div>
  )
}
