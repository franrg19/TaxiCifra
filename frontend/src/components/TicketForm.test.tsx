import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { ApiError } from '../api/client'
import type { Ticket, Vehicle } from '../types/api'
import { TicketForm } from './TicketForm'

/** Ticket tal como llega del OCR: pendiente de revisión y con los importes en texto. */
function makeTicket(changes: Partial<Ticket> = {}): Ticket {
  return {
    id: 1,
    status: 'pending_review',
    created_at: '2026-11-07T10:00:00Z',
    vehicle_id: null,
    date: '2026-11-05',
    vendor: 'Gasolinera Sur',
    category: 'combustible',
    net_amount: '41.32',
    vat: '8.68',
    total: '50.00',
    ...changes,
  }
}

const VEHICLE: Vehicle = {
  id: 7,
  plate: '1234ABC',
  brand: 'Toyota',
  model: 'Prius',
  created_at: '2026-10-01T10:00:00Z',
}

function renderForm(ticket: Ticket, vehicles: Vehicle[] = []) {
  const onSave = vi.fn(() => Promise.resolve())
  const onConfirm = vi.fn(() => Promise.resolve())
  render(
    <TicketForm
      ticket={ticket}
      vehicles={vehicles}
      onSave={onSave}
      onConfirm={onConfirm}
    />,
  )
  return { onSave, onConfirm }
}

describe('TicketForm', () => {
  it('muestra lo que ha leído el OCR, con coma decimal', () => {
    renderForm(makeTicket())

    expect(screen.getByLabelText('Establecimiento')).toHaveValue(
      'Gasolinera Sur',
    )
    expect(screen.getByLabelText('Categoría')).toHaveValue('combustible')
    expect(screen.getByLabelText('Base imponible (€)')).toHaveValue('41,32')
    expect(screen.getByLabelText('IVA (€)')).toHaveValue('8,68')
    expect(screen.getByLabelText('Total (€)')).toHaveValue('50,00')
  })

  it('envía las correcciones del usuario en el formato de la API', async () => {
    const user = userEvent.setup()
    const { onConfirm } = renderForm(makeTicket({ vendor: null, vat: null }))

    await user.type(screen.getByLabelText('Establecimiento'), '  Repsol  ')
    await user.type(screen.getByLabelText('IVA (€)'), '8,68')
    await user.clear(screen.getByLabelText('Base imponible (€)'))
    await user.click(
      screen.getByRole('button', { name: 'Guardar y confirmar' }),
    )

    expect(onConfirm).toHaveBeenCalledWith({
      date: '2026-11-05',
      vendor: 'Repsol',
      category: 'combustible',
      net_amount: null,
      vat: '8.68',
      total: '50.00',
      vehicle_id: null,
    })
    expect(await screen.findByRole('status')).toHaveTextContent(
      'Cambios guardados.',
    )
  })

  it('propone el vehículo si el usuario solo tiene uno', () => {
    renderForm(makeTicket(), [VEHICLE])

    expect(screen.getByLabelText('Vehículo')).toHaveValue('7')
  })

  it('no propone vehículo en un ticket ya confirmado', () => {
    renderForm(makeTicket({ status: 'confirmed' }), [VEHICLE])

    expect(screen.getByLabelText('Vehículo')).toHaveValue('')
  })

  it('muestra el error de la API si no se puede confirmar', async () => {
    const user = userEvent.setup()
    const { onConfirm } = renderForm(makeTicket())
    onConfirm.mockRejectedValueOnce(
      new ApiError(422, {
        detail: 'La base imponible más el IVA no coincide con el total',
        code: 'amounts_mismatch',
      }),
    )

    await user.click(
      screen.getByRole('button', { name: 'Guardar y confirmar' }),
    )

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'La base imponible más el IVA no coincide con el total',
    )
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  it('no guarda si un importe tiene un formato incorrecto', async () => {
    const user = userEvent.setup()
    const { onSave } = renderForm(makeTicket())

    await user.clear(screen.getByLabelText('Total (€)'))
    await user.type(screen.getByLabelText('Total (€)'), '50,123')
    await user.click(
      screen.getByRole('button', { name: 'Guardar sin confirmar' }),
    )

    expect(onSave).not.toHaveBeenCalled()
  })
})
