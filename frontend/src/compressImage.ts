// Suficiente para leer un ticket: las fotos de móvil tienen el doble o más
const MAX_SIDE = 2000
const JPEG_QUALITY = 0.85

/**
 * Reduce una foto antes de subirla. Las de galería suelen pasar del límite de 5 MB y
 * reducirlas acelera la subida y la lectura. Si el navegador no puede abrir el fichero,
 * se devuelve tal cual: el backend decidirá si lo acepta.
 */
export async function compressImage(file: File): Promise<File> {
  const url = URL.createObjectURL(file)
  try {
    const image = new Image()
    image.src = url
    await image.decode()

    const scale = Math.min(
      1,
      MAX_SIDE / Math.max(image.naturalWidth, image.naturalHeight),
    )
    const canvas = document.createElement('canvas')
    canvas.width = Math.round(image.naturalWidth * scale)
    canvas.height = Math.round(image.naturalHeight * scale)

    const context = canvas.getContext('2d')
    if (!context) {
      return file
    }
    // Fondo blanco: JPEG no admite transparencia
    context.fillStyle = '#ffffff'
    context.fillRect(0, 0, canvas.width, canvas.height)
    context.drawImage(image, 0, 0, canvas.width, canvas.height)

    const blob = await new Promise<Blob | null>((resolve) =>
      canvas.toBlob(resolve, 'image/jpeg', JPEG_QUALITY),
    )
    return blob ? new File([blob], 'ticket.jpg', { type: 'image/jpeg' }) : file
  } catch {
    return file
  } finally {
    URL.revokeObjectURL(url)
  }
}
