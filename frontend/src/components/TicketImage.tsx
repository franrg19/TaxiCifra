import { useEffect, useState } from 'react'
import { ApiError } from '../api/client'
import { getTicketImage } from '../api/tickets'

/** Resultado de la descarga: la foto o el texto que se muestra en su lugar. */
type ImageState = { url: string } | { message: string } | null

/**
 * Foto del ticket. Se descarga con fetch porque la API exige el token, y un <img src>
 * no puede enviarlo: los bytes se guardan en un Blob y se le da una URL temporal.
 */
export function TicketImage({ ticketId }: { ticketId: number }) {
  const [image, setImage] = useState<ImageState>(null)

  useEffect(() => {
    let cancelled = false
    let url: string | null = null

    getTicketImage(ticketId)
      .then((blob) => {
        if (!cancelled) {
          url = URL.createObjectURL(blob)
          setImage({ url })
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const noImage = err instanceof ApiError && err.status === 404
          setImage({
            message: noImage
              ? 'Este ticket no tiene foto.'
              : 'No se ha podido cargar la foto.',
          })
        }
      })

    // Libera la memoria de la foto al salir de la pantalla
    return () => {
      cancelled = true
      if (url) {
        URL.revokeObjectURL(url)
      }
    }
  }, [ticketId])

  if (image === null) {
    return <p className="text-slate-600">Cargando foto…</p>
  }
  if ('message' in image) {
    return <p className="text-slate-600">{image.message}</p>
  }
  return (
    <img
      src={image.url}
      alt="Foto del ticket"
      className="w-full rounded-md border border-slate-200"
    />
  )
}
