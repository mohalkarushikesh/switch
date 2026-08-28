// Minimal hash router. Hash-based (not history-based) on purpose: the app is
// served as static files from FastAPI at /app, so a deep path like /app/ledger
// would 404 on reload — #/ledger always resolves to the same index.html.
// No router dependency; the whole surface is "which of N views is showing".
import { useCallback, useEffect, useState } from 'react'

const readHash = () => window.location.hash.replace(/^#\/?/, '').trim()

/**
 * @param {string[]} valid   allowed route ids; anything else falls back
 * @param {string}   fallback route used when the hash is empty or unknown
 * @returns {[string, (id: string) => void]} current route and a navigate fn
 */
export function useHashRoute(valid, fallback) {
  const resolve = useCallback(() => {
    const id = readHash()
    return valid.includes(id) ? id : fallback
  }, [valid, fallback])

  const [route, setRoute] = useState(resolve)

  useEffect(() => {
    const onChange = () => setRoute(resolve())
    window.addEventListener('hashchange', onChange)
    onChange() // resolve once on mount, in case the hash changed before listening
    return () => window.removeEventListener('hashchange', onChange)
  }, [resolve])

  // Writing the hash fires hashchange, which drives the state update above, so
  // the URL stays the single source of truth (back/forward buttons just work).
  const navigate = useCallback((id) => {
    window.location.hash = `#/${id}`
  }, [])

  return [route, navigate]
}
