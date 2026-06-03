import { useEffect, useState } from 'react'
import { getHealth } from '../api'

export default function HealthBadge() {
  const [health, setHealth] = useState(null)

  useEffect(() => {
    const tick = () => getHealth().then(setHealth).catch(() => setHealth(null))
    tick()
    const t = setInterval(tick, 10000)
    return () => clearInterval(t)
  }, [])

  const ok = health?.printer_reachable
  const label = health
    ? ok
      ? `Printer ${health.printer_host} ready`
      : `Printer ${health.printer_host || 'unset'} unreachable`
    : 'Checking printer…'

  return (
    <div className="flex items-center gap-2 text-sm">
      <span className={`inline-block w-2.5 h-2.5 rounded-full ${ok ? 'bg-emerald-400' : 'bg-red-400'}`} />
      <span className="text-gray-400">{label}</span>
    </div>
  )
}
