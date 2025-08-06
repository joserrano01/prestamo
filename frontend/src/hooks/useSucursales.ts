import { useState, useEffect } from 'react';

export interface Sucursal {
  id: string;
  codigo: string;
  nombre: string;
  direccion?: string;
  telefono?: string;
  manager?: string;
  is_active?: boolean;
}

export function useSucursales() {
  const [sucursales, setSucursales] = useState<Sucursal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Flag para ignorar respuestas obsoletas (patrón recomendado por React)
    let ignore = false;

    const fetchSucursales = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch('/api/v1/sucursales/');

        if (!response.ok) {
          throw new Error(`Error ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        
        // Solo actualizar el estado si la respuesta no es obsoleta
        if (!ignore) {
          // Normalizar datos agregando is_active si no existe
          const normalizedData = data.map((sucursal: any) => ({
            ...sucursal,
            is_active: sucursal.is_active ?? true
          }));

          setSucursales(normalizedData);
          setError(null);
        }

      } catch (err) {
        // Solo manejar errores si la respuesta no es obsoleta
        if (!ignore) {
          const errorMessage = err instanceof Error ? err.message : 'Error desconocido';
          console.error('Error fetching sucursales:', errorMessage);
          
          setError(errorMessage);
          setSucursales([]);
        }
      } finally {
        // Solo actualizar loading si la respuesta no es obsoleta
        if (!ignore) {
          setLoading(false);
        }
      }
    };

    fetchSucursales();

    // Cleanup function - marcar respuestas como obsoletas
    return () => {
      ignore = true;
    };
  }, []); // Array de dependencias vacío - solo ejecutar una vez

  return { sucursales, loading, error };
}
