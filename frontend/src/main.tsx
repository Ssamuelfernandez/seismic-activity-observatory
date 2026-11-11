import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { App } from './App';
import { ConfigGate } from './components/ConfigGate';
import './index.css';

// Sin reintentos automáticos: un error de la API se muestra tal cual, no se maquilla.
const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } } });

// Punto de entrada: solo monta la aplicación (la lógica vive en otros módulos).
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <ConfigGate>
        <App />
      </ConfigGate>
    </QueryClientProvider>
  </StrictMode>,
);
