/**
 * Pantalla raíz provisional del panel.
 *
 * Qué hace:
 *     Muestra un título; el mapa, la ficha y la leyenda llegan en tareas posteriores.
 * Devuelve:
 *     El elemento raíz de la aplicación.
 * Por qué existe:
 *     Permite que `npm run build` y `npm run dev` funcionen desde T001 (G0).
 */
export function App() {
  return <h1 className="p-4 text-xl">Observatorio sísmico</h1>;
}
