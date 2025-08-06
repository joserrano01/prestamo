import { useState, useEffect } from 'react';

export interface Sucursal {
  id: string;
  codigo: string;
  nombre: string;
  direccion?: string;
  telefono?: string;
  manager?: string;
  is_active: boolean;
}

export function useSucursales() {
  console.log('🏢 useSucursales hook called at', new Date().toLocaleTimeString());
  
  const [sucursales, setSucursales] = useState<Sucursal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    console.log('🏢 useSucursales useEffect triggered');
    const fetchSucursales = async () => {
      try {
        console.log('🔄 Starting fetch request to /api/v1/sucursales/');
        setLoading(true);
        setError(null);
        
        const response = await fetch('/api/v1/sucursales/');
        console.log('📡 Response received:', response.status, response.statusText);
        
        if (!response.ok) {
          throw new Error(`Error ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('✅ Data received:', data);
        console.log('📊 Number of sucursales:', data.length);
        setSucursales(data);
        console.log('🎯 Sucursales set in state');
      } catch (err) {
        console.error('❌ Error fetching sucursales:', err);
        setError(err instanceof Error ? err.message : 'Error desconocido');
        console.log('🔄 Using fallback data');
        // Fallback con datos de ejemplo para desarrollo
        const fallbackData = [
          {
            id: '1',
            codigo: 'SUC001',
            nombre: 'Sucursal Central',
            direccion: 'Av. Principal 123',
            manager: 'Juan Pérez',
            is_active: true
          },
          {
            id: '2',
            codigo: 'SUC002',
            nombre: 'Sucursal Norte',
            direccion: 'Calle Norte 456',
            manager: 'María García',
            is_active: true
          },
          {
            id: '3',
            codigo: 'SUC003',
            nombre: 'Sucursal Sur',
            direccion: 'Av. Sur 789',
            manager: 'Carlos López',
            is_active: true
          }
        ];
        setSucursales(fallbackData);
        console.log('🎯 Fallback data set:', fallbackData.length, 'sucursales');
      } finally {
        setLoading(false);
        console.log('✅ Loading set to false');
      }
    };

    fetchSucursales();
  }, []);

  return { sucursales, loading, error };
}
