/** "1234.50" → "1.234,50 €". Trabaja con el texto: el dinero nunca pasa por un número decimal. */
export function formatEuros(amount: string): string {
  const [integer, decimals] = amount.split('.')
  const withThousands = integer.replace(/\B(?=(\d{3})+(?!\d))/g, '.')
  return `${withThousands},${decimals} €`
}

/** "2026-10-05" → "05/10/2026". Sin usar Date, para evitar cambios por la zona horaria. */
export function formatDate(date: string): string {
  const [year, month, day] = date.split('-')
  return `${day}/${month}/${year}`
}
