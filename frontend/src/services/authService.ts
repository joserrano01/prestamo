/**
 * Servicio de Autenticación Seguro
 * Maneja tokens de forma segura con mejores prácticas de seguridad
 */

interface LoginResult {
  access_token: string;
  refresh_token: string;
  user: any;
}

interface AuthTokens {
  accessToken: string;
  refreshToken: string;
}

class AuthService {
  private static readonly ACCESS_TOKEN_KEY = 'auth_access_token';
  private static readonly REFRESH_TOKEN_KEY = 'auth_refresh_token';
  private static readonly USER_KEY = 'auth_user';
  
  // Configuración de seguridad
  private static readonly TOKEN_EXPIRY_BUFFER = 5 * 60 * 1000; // 5 minutos en ms
  
  /**
   * Almacena tokens de forma más segura
   * NOTA: En producción, considerar usar httpOnly cookies
   */
  static storeTokens(loginResult: LoginResult): void {
    try {
      // Usar sessionStorage en lugar de localStorage para mayor seguridad
      // Los datos se eliminan al cerrar la pestaña/navegador
      sessionStorage.setItem(this.ACCESS_TOKEN_KEY, loginResult.access_token);
      sessionStorage.setItem(this.REFRESH_TOKEN_KEY, loginResult.refresh_token);
      sessionStorage.setItem(this.USER_KEY, JSON.stringify(loginResult.user));
      
      // Establecer tiempo de expiración automática
      this.setTokenExpiry();
      
      console.log('✅ Tokens almacenados de forma segura');
    } catch (error) {
      console.error('❌ Error al almacenar tokens:', error);
      throw new Error('Error al almacenar credenciales de autenticación');
    }
  }

  /**
   * Obtiene el token de acceso
   */
  static getAccessToken(): string | null {
    try {
      const token = sessionStorage.getItem(this.ACCESS_TOKEN_KEY);
      
      // Verificar si el token ha expirado
      if (token && this.isTokenExpired()) {
        this.clearTokens();
        return null;
      }
      
      return token;
    } catch (error) {
      console.error('❌ Error al obtener token de acceso:', error);
      return null;
    }
  }

  /**
   * Obtiene el token de refresh
   */
  static getRefreshToken(): string | null {
    try {
      return sessionStorage.getItem(this.REFRESH_TOKEN_KEY);
    } catch (error) {
      console.error('❌ Error al obtener token de refresh:', error);
      return null;
    }
  }

  /**
   * Obtiene la información del usuario
   */
  static getUser(): any | null {
    try {
      const userStr = sessionStorage.getItem(this.USER_KEY);
      return userStr ? JSON.parse(userStr) : null;
    } catch (error) {
      console.error('❌ Error al obtener información del usuario:', error);
      return null;
    }
  }

  /**
   * Verifica si el usuario está autenticado
   */
  static isAuthenticated(): boolean {
    const token = this.getAccessToken();
    return token !== null && !this.isTokenExpired();
  }

  /**
   * Limpia todos los tokens y datos de autenticación
   */
  static clearTokens(): void {
    try {
      sessionStorage.removeItem(this.ACCESS_TOKEN_KEY);
      sessionStorage.removeItem(this.REFRESH_TOKEN_KEY);
      sessionStorage.removeItem(this.USER_KEY);
      sessionStorage.removeItem('token_expiry');
      
      console.log('✅ Tokens eliminados de forma segura');
    } catch (error) {
      console.error('❌ Error al limpiar tokens:', error);
    }
  }

  /**
   * Establece tiempo de expiración del token
   */
  private static setTokenExpiry(): void {
    try {
      // Establecer expiración en 30 minutos (configurable)
      const expiryTime = Date.now() + (30 * 60 * 1000);
      sessionStorage.setItem('token_expiry', expiryTime.toString());
    } catch (error) {
      console.error('❌ Error al establecer expiración del token:', error);
    }
  }

  /**
   * Verifica si el token ha expirado
   */
  private static isTokenExpired(): boolean {
    try {
      const expiryStr = sessionStorage.getItem('token_expiry');
      if (!expiryStr) return true;
      
      const expiryTime = parseInt(expiryStr);
      return Date.now() > (expiryTime - this.TOKEN_EXPIRY_BUFFER);
    } catch (error) {
      console.error('❌ Error al verificar expiración del token:', error);
      return true;
    }
  }

  /**
   * Manejo seguro de "Recordar usuario" usando localStorage solo para datos no sensibles
   */
  static storeUserPreferences(remember: boolean, identifier?: string, sucursalId?: string): void {
    try {
      if (remember && identifier && sucursalId) {
        // Solo almacenar datos no sensibles en localStorage
        localStorage.setItem('remember_user', 'true');
        localStorage.setItem('last_identifier', identifier.trim());
        localStorage.setItem('last_sucursal', sucursalId);
      } else {
        localStorage.removeItem('remember_user');
        localStorage.removeItem('last_identifier');
        localStorage.removeItem('last_sucursal');
      }
    } catch (error) {
      console.error('❌ Error al almacenar preferencias del usuario:', error);
    }
  }

  /**
   * Obtiene las preferencias del usuario
   */
  static getUserPreferences(): { remember: boolean; identifier?: string; sucursalId?: string } {
    try {
      const remember = localStorage.getItem('remember_user') === 'true';
      const identifier = localStorage.getItem('last_identifier');
      const sucursalId = localStorage.getItem('last_sucursal');
      
      return {
        remember,
        identifier: identifier || undefined,
        sucursalId: sucursalId || undefined
      };
    } catch (error) {
      console.error('❌ Error al obtener preferencias del usuario:', error);
      return { remember: false };
    }
  }

  /**
   * Obtiene headers de autorización para requests
   */
  static getAuthHeaders(): Record<string, string> {
    const token = this.getAccessToken();
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  }
}

export default AuthService;
