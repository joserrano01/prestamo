import React, { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { useNavigate } from 'react-router-dom';
import { useSucursales } from '../hooks/useSucursales';
import AuthService from '../services/authService';


// --- Optimized Icon Components with React.memo ---
const BranchIcon = React.memo<{ className?: string }>(({ className = "h-5 w-5" }) => (
  <svg xmlns="http://www.w3.org/2000/svg" className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
  </svg>
));
BranchIcon.displayName = 'BranchIcon';

const UserIcon = React.memo<{ className?: string }>(({ className = "h-5 w-5" }) => (
  <svg xmlns="http://www.w3.org/2000/svg" className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
  </svg>
));
UserIcon.displayName = 'UserIcon';

const LockIcon = React.memo<{ className?: string }>(({ className = "h-5 w-5" }) => (
  <svg xmlns="http://www.w3.org/2000/svg" className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
  </svg>
));
LockIcon.displayName = 'LockIcon';

const EyeIcon = React.memo<{ className?: string }>(({ className = "h-5 w-5" }) => (
  <svg xmlns="http://www.w3.org/2000/svg" className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    <path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
  </svg>
));
EyeIcon.displayName = 'EyeIcon';

const EyeOffIcon = React.memo<{ className?: string }>(({ className = "h-5 w-5" }) => (
  <svg xmlns="http://www.w3.org/2000/svg" className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
  </svg>
));
EyeOffIcon.displayName = 'EyeOffIcon';

const AlertTriangleIcon = React.memo<{ className?: string }>(({ className = "h-5 w-5 text-red-500" }) => (
  <svg xmlns="http://www.w3.org/2000/svg" className={className} viewBox="0 0 20 20" fill="currentColor">
    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.21 3.03-1.742 3.03H4.42c-1.532 0-2.492-1.696-1.742-3.03l5.58-9.92zM10 13a1 1 0 110-2 1 1 0 010 2zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
  </svg>
));
AlertTriangleIcon.displayName = 'AlertTriangleIcon';

const CheckIcon = React.memo<{ className?: string }>(({ className = "h-5 w-5" }) => (
  <svg xmlns="http://www.w3.org/2000/svg" className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
  </svg>
));
CheckIcon.displayName = 'CheckIcon';

const ShieldIcon = React.memo<{ className?: string }>(({ className = "h-12 w-12" }) => (
  <svg xmlns="http://www.w3.org/2000/svg" className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
  </svg>
));
ShieldIcon.displayName = 'ShieldIcon';

interface LoginFormData {
  identifier: string;
  password: string;
  sucursal_id: string;
}

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: {
    id: number;
    email: string;
    nombre: string;
    sucursal_id: string;
  };
}

const LoadingSpinner = ({ size = "h-5 w-5" }) => (
  <div className={`animate-spin rounded-full ${size} border-2 border-white border-t-transparent`}></div>
);

export const LoginFormWithBranch = React.memo(() => {
  // Lazy initialization para cargar datos recordados usando AuthService seguro
  const [identifier, setIdentifier] = useState(() => {
    try {
      const preferences = AuthService.getUserPreferences();
      return preferences.remember && preferences.identifier ? preferences.identifier : '';
    } catch (error) {
      console.warn('Error loading identifier:', error);
    }
    return '';
  });

  const [sucursalId, setSucursalId] = useState(() => {
    try {
      const preferences = AuthService.getUserPreferences();
      return preferences.remember && preferences.sucursalId ? preferences.sucursalId : '';
    } catch (error) {
      console.warn('Error loading sucursal:', error);
    }
    return '';
  });

  const [rememberMe, setRememberMe] = useState(() => {
    try {
      const preferences = AuthService.getUserPreferences();
      return preferences.remember;
    } catch (error) {
      return false;
    }
  });

  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  
  const navigate = useNavigate();
  const { sucursales, loading: sucursalesLoading, error: sucursalesError } = useSucursales();

  // Memoized form validation
  const isFormValid = useMemo(() => {
    return identifier.trim() !== '' && 
           password.trim() !== '' && 
           sucursalId !== '';
  }, [identifier, password, sucursalId]);

  // Simplified validation - only on blur to prevent constant re-renders
  const validateField = useCallback((name: string, value: string) => {
    setFieldErrors(prev => {
      const newErrors = { ...prev };
      delete newErrors[name];
      
      switch (name) {
        case 'identifier':
          if (!value.trim()) {
            newErrors.identifier = 'El identificador es requerido';
          } else if (value.length < 3) {
            newErrors.identifier = 'El identificador debe tener al menos 3 caracteres';
          }
          break;
        case 'password':
          if (!value.trim()) {
            newErrors.password = 'La contraseña es requerida';
          } else if (value.length < 6) {
            newErrors.password = 'La contraseña debe tener al menos 6 caracteres';
          }
          break;
        case 'sucursal_id':
          if (!value) {
            newErrors.sucursal_id = 'Debe seleccionar una sucursal';
          }
          break;
      }
      
      return newErrors;
    });
  }, []);

  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    
    // Update individual state
    if (name === 'identifier') setIdentifier(value);
    else if (name === 'password') setPassword(value);
    else if (name === 'sucursal_id') setSucursalId(value);
    
    setGeneralError(null);
  }, []);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();

    // Prevent concurrent requests and double submission
    if (isLoading || !isFormValid) return;

    setIsLoading(true);
    setGeneralError(null);
    
    try {
      // Prepare login payload
      const loginPayload = {
        identifier: identifier.trim(),
        password: password.trim(),
        sucursal_id: sucursalId
      };

      const response = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(loginPayload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Error ${response.status}: ${response.statusText}`);
      }

      const loginResult: LoginResponse = await response.json();

      // Store tokens using secure AuthService
      try {
        // Almacenar tokens de forma segura usando sessionStorage
        AuthService.storeTokens(loginResult);

        // Almacenar preferencias del usuario (datos no sensibles) en localStorage
        AuthService.storeUserPreferences(rememberMe, identifier.trim(), sucursalId);
        
        console.log('✅ Login exitoso - Tokens almacenados de forma segura');
      } catch (storageError) {
        console.error('❌ Error storing login data:', storageError);
        throw new Error('Error al almacenar credenciales de autenticación');
      }

      // Navigate to dashboard
      navigate('/dashboard', { replace: true });
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error de conexión';
      setGeneralError(errorMessage);
      
      // Clear password field on error for security
      setPassword('');
      
    } finally {
      setIsLoading(false);
    }
  }, [identifier, password, sucursalId, rememberMe, isLoading, isFormValid, navigate]);

  // Removed selectedSucursal to prevent re-renders

  return (
    <div className="w-full">
      {sucursalesError && (
        <div className="mb-6 p-4 bg-red-50/90 backdrop-blur-sm rounded-lg border border-red-200">
          <div className="flex items-center">
            <AlertTriangleIcon className="h-5 w-5 text-red-500 mr-3" />
            <div>
              <h3 className="text-sm font-medium text-red-800">
                Error al cargar las sucursales
              </h3>
              <p className="text-sm text-red-700 mt-1">{sucursalesError}</p>
            </div>
          </div>
                    placeholder="Ingresa tu contraseña"
                    required
                    autoComplete="current-password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-500 hover:text-green-600 transition-colors focus:outline-none focus:text-green-600"
                    tabIndex={-1}
                  >
                    {showPassword ? 
                      <EyeOffIcon className="h-5 w-5" /> : 
                      <EyeIcon className="h-5 w-5" />
                    }
                  </button>
                </div>
                {fieldErrors.password && (
                  <div className="flex items-center space-x-2 text-red-600 animate-fade-in">
                    <AlertTriangleIcon className="h-4 w-4" />
                    <p className="text-sm font-medium">{fieldErrors.password}</p>
                  </div>
                )}
              </div>

              {/* Options */}
              <div className="flex items-center justify-between pt-2">
                <label className="flex items-center group cursor-pointer">
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      className="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded transition-all duration-200 group-hover:border-green-400"
                    />
                    {rememberMe && (
                      <CheckIcon className="h-3 w-3 text-green-600 absolute top-0.5 left-0.5 pointer-events-none" />
                    )}
                  </div>
                  <span className="ml-3 text-sm text-gray-700 group-hover:text-gray-900 transition-colors font-medium">
                    Recordarme
                  </span>
                </label>
                <button
                  type="button"
                  className="text-sm text-green-600 hover:text-green-700 font-medium transition-colors focus:outline-none focus:underline"
                  onClick={() => alert('Función de recuperación de contraseña próximamente')}
                >
                  ¿Olvidaste tu contraseña?
                </button>
              </div>

              {/* Submit button */}
              <div className="pt-8">
                <button
                  type="submit"
                  disabled={!isFormValid || isLoading || sucursalesLoading}
                  className={`group relative w-full py-4 px-6 border border-transparent rounded-xl text-white font-semibold text-base focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 transition-all duration-200 transform ${
                    isFormValid && !isLoading && !sucursalesLoading
                      ? 'bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 hover:scale-[1.02] hover:shadow-lg active:scale-[0.98]'
                      : 'bg-gray-400 cursor-not-allowed opacity-60'
                  }`}
                >
                  <span className="absolute left-0 inset-y-0 flex items-center pl-4">
                    {isLoading ? (
                      <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                    ) : (
                      <ShieldIcon className="h-5 w-5 text-white/80 group-hover:text-white transition-colors" />
                    )}
                  </span>
                  <span className="ml-6">
                    {isLoading ? (
                      'Verificando credenciales...'
                    ) : (
                      'Iniciar Sesión Segura'
                    )}
                  </span>
                </button>
              </div>
            </div>
          </form>

          </div>
        </div>
      </div>
    </div>
  );
});

LoginFormWithBranch.displayName = 'LoginFormWithBranch';