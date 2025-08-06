export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'manager' | 'employee';
  sucursal: string;
  isActive: boolean;
  createdAt: Date;
  lastLogin?: Date;
}

export interface Sucursal {
  id: string;
  value: string;
  label: string;
  address: string;
  phone: string;
  manager: string;
}

export interface Cliente {
  id: string;
  nombre: string;
  apellido: string;
  email: string;
  telefono: string;
  direccion: string;
  rfc?: string;
  curp?: string;
  fechaNacimiento: Date;
  ingresosMensuales: number;
  ocupacion: string;
  estadoCivil: 'soltero' | 'casado' | 'divorciado' | 'viudo';
  creditScore?: number;
  createdAt: Date;
  updatedAt: Date;
}

export interface Prestamo {
  id: string;
  clienteId: string;
  cliente?: Cliente;
  monto: number;
  plazo: number; // en meses
  tasaInteres: number;
  fechaInicio: Date;
  fechaVencimiento: Date;
  estado: 'pendiente' | 'aprobado' | 'rechazado' | 'activo' | 'pagado' | 'vencido';
  montoTotal: number;
  montoPagado: number;
  montoRestante: number;
  cuotaMensual: number;
  sucursalId: string;
  sucursal?: Sucursal;
  usuarioId: string; // quien procesó el préstamo
  usuario?: User;
  garantia?: string;
  proposito: string;
  documentos: Documento[];
  pagos: Pago[];
  createdAt: Date;
  updatedAt: Date;
}

export interface Pago {
  id: string;
  prestamoId: string;
  prestamo?: Prestamo;
  monto: number;
  fechaPago: Date;
  fechaVencimiento: Date;
  estado: 'pendiente' | 'pagado' | 'vencido';
  metodoPago: 'efectivo' | 'transferencia' | 'cheque' | 'tarjeta';
  referencia?: string;
  notas?: string;
  usuarioId: string; // quien registró el pago
  usuario?: User;
  createdAt: Date;
}

export interface Documento {
  id: string;
  prestamoId?: string;
  clienteId?: string;
  tipo: 'identificacion' | 'comprobante_ingresos' | 'comprobante_domicilio' | 'aval' | 'otro';
  nombre: string;
  url: string;
  tamaño: number;
  mimeType: string;
  uploadedBy: string;
  createdAt: Date;
}

export interface DashboardStats {
  prestamosActivos: number;
  totalPrestado: number;
  clientesActivos: number;
  tasaRecuperacion: number;
  prestamosPendientes: number;
  pagosVencidos: number;
  ingresosMes: number;
  crecimientoMensual: number;
}

export interface ActivityLog {
  id: string;
  tipo: 'prestamo_creado' | 'prestamo_aprobado' | 'pago_recibido' | 'cliente_registrado' | 'documento_subido';
  descripcion: string;
  usuarioId: string;
  usuario?: User;
  entidadId: string; // ID del préstamo, cliente, etc.
  entidadTipo: 'prestamo' | 'cliente' | 'pago' | 'documento';
  metadata?: Record<string, any>;
  createdAt: Date;
}

export interface LoginCredentials {
  email: string;
  password: string;
  sucursal: string;
  rememberMe: boolean;
}

export interface AuthResponse {
  user: User;
  token: string;
  refreshToken: string;
  expiresAt: Date;
}
