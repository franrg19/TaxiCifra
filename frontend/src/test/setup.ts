import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// Cada test empieza con la página vacía
afterEach(() => {
  cleanup()
})
