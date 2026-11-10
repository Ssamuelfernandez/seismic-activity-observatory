import { useEffect, useState } from 'react';

/**
 * Qué hace:
 *     Devuelve un reloj que se actualiza cada cierto tiempo.
 * Recibe:
 *     everyMs: intervalo en ms.
 * Devuelve:
 *     La hora actual en ms.
 * Por qué existe:
 *     Permite mostrar «hace N min» sin esperar nuevos datos (G7).
 */
export function useNow(everyMs: number): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), everyMs);
    return () => clearInterval(id);
  }, [everyMs]);
  return now;
}
