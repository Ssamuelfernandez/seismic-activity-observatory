import { useEffect, useState, useSyncExternalStore } from 'react';

/** Por debajo de este ancho (px) se usa el diseño móvil; por encima, el de escritorio. */
export const MOBILE_MAX_WIDTH = 1023;
const QUERY = `(max-width: ${MOBILE_MAX_WIDTH}px)`;

/**
 * Qué hace:
 *     Detecta si la pantalla es estrecha (< 1024 px).
 * Recibe:
 *     Nada.
 * Devuelve:
 *     true si se debe pintar el diseño móvil.
 * Por qué existe:
 *     Elige entre el diseño de escritorio y el móvil (G17).
 */
export function useIsMobile(): boolean {
  return useSyncExternalStore(
    (notify) => {
      const mq = window.matchMedia(QUERY);
      mq.addEventListener('change', notify);
      return () => mq.removeEventListener('change', notify);
    },
    () => window.matchMedia(QUERY).matches,
    () => false,
  );
}

/**
 * Qué hace:
 *     Sigue el tamaño de la ventana.
 * Recibe:
 *     Nada.
 * Devuelve:
 *     Ancho y alto actuales.
 * Por qué existe:
 *     Los componentes ajustan su tamaño al girar o redimensionar (G17).
 */
export function useViewport(): { width: number; height: number } {
  const [size, setSize] = useState({ width: window.innerWidth, height: window.innerHeight });
  useEffect(() => {
    const onResize = () => setSize({ width: window.innerWidth, height: window.innerHeight });
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);
  return size;
}
