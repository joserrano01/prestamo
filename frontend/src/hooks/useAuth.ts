/**
 * Hook de Autenticación Seguro
 * Proporciona funcionalidades de autenticación con mejores prácticas de seguridad
 */

import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import AuthService from '../services/authService';

interface User {
  id: string;
  username: string;
  email?: string;
  sucursal_id?: string;
  // Agregar otros campos según sea necesario
}

interface UseAuthReturn {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<boolean>;
}

interface LoginCredentials {
  identifier: string;
  password: string;
  sucursal_id: string;
  remember_me?: boolean;
}

export const useAuth = (): UseAuthReturn => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const navigate = useNavigate();

  // Verificar autenticación al cargar
  useEffect(() => {
    const checkAuth = () => {
      try {
        if (AuthService.isAuthenticated()) {
          const userData = AuthService.getUser();
          setUser(userData);
        } else {
          setUser(null);
        }
      } catch (error) {
        console.error('❌ Error checking authentication:', error);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuth();
  }, []);

  // Función de login
  const login = useCallback(async (credentials: LoginCredentials): Promise<void> => {
    setIsLoading(true);
    
    try {
      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          identifier: credentials.identifier.trim(),
          password: credentials.password,
          sucursal_id: credentials.sucursal_id,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Error de autenticación');
      }

      const loginResult = await response.json();

      // Almacenar tokens de forma segura
      AuthService.storeTokens(loginResult);
      
      // Almacenar preferencias del usuario
      AuthService.storeUserPreferences(
        credentials.remember_me || false,
        credentials.identifier.trim(),
        credentials.sucursal_id
      );

      setUser(loginResult.user);
      
      console.log('✅ Login exitoso');
    } catch (error) {
      console.error('❌ Error en login:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Función de logout
  const logout = useCallback(() => {
    try {
      AuthService.clearTokens();
      setUser(null);
      navigate('/login', { replace: true });
      console.log('✅ Logout exitoso');
    } catch (error) {
      console.error('❌ Error en logout:', error);
    }
  }, [navigate]);

  // Función para refrescar token
  const refreshToken = useCallback(async (): Promise<boolean> => {
    try {
      const refreshToken = AuthService.getRefreshToken();
      
      if (!refreshToken) {
        return false;
      }

      const response = await fetch('/api/v1/auth/refresh', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${refreshToken}`,
        },
      });

      if (!response.ok) {
        return false;
      }

      const result = await response.json();
      
      // Actualizar tokens
      AuthService.storeTokens(result);
      
      console.log('✅ Token refrescado exitosamente');
      return true;
    } catch (error) {
      console.error('❌ Error refrescando token:', error);
      return false;
    }
  }, []);

  // Auto-refresh token antes de que expire
  useEffect(() => {
    if (!user) return;

    const interval = setInterval(async () => {
      if (AuthService.isAuthenticated()) {
        const success = await refreshToken();
        if (!success) {
          logout();
        }
      }
    }, 25 * 60 * 1000); // Refrescar cada 25 minutos

    return () => clearInterval(interval);
  }, [user, refreshToken, logout]);

  return {
    user,
    isAuthenticated: !!user && AuthService.isAuthenticated(),
    isLoading,
    login,
    logout,
    refreshToken,
  };
};

export default useAuth;
