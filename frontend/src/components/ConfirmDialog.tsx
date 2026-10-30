import { Button } from './Button'

interface ConfirmDialogProps {
  title: string
  message: string
  confirmLabel: string
  busy: boolean
  onConfirm: () => void
  onCancel: () => void
}

/** Ventana que pide confirmación antes de una acción que no se puede deshacer. */
export function ConfirmDialog({
  title,
  message,
  confirmLabel,
  busy,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-slate-900/50 p-4">
      <div
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
        className="w-full max-w-md rounded-lg bg-white p-6 shadow-lg"
      >
        <h2 id="confirm-title" className="text-lg font-semibold">
          {title}
        </h2>
        <p className="mt-2 text-slate-600">{message}</p>
        <div className="mt-6 flex justify-end gap-2">
          <Button variant="secondary" disabled={busy} onClick={onCancel}>
            Cancelar
          </Button>
          <Button variant="danger" disabled={busy} onClick={onConfirm}>
            {confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  )
}
