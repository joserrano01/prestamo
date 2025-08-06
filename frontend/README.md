# Sistema de Préstamos - Frontend

Sistema web para la gestión de préstamos empresariales desarrollado con React, TypeScript y Tailwind CSS.

## 🚀 Características

- **Autenticación segura** con verificación 2FA
- **Dashboard interactivo** con métricas en tiempo real
- **Gestión de préstamos** completa
- **Administración de clientes**
- **Sistema de reportes**
- **Interfaz responsive** y moderna
- **Multi-sucursal** con selección de ubicación

## 🛠️ Tecnologías

- **React 18** - Biblioteca de interfaz de usuario
- **TypeScript** - Tipado estático
- **Vite** - Herramienta de construcción rápida
- **Tailwind CSS** - Framework de CSS utilitario
- **Radix UI** - Componentes accesibles
- **Lucide React** - Iconos modernos
- **React Router** - Enrutamiento del lado del cliente

## 📦 Instalación

1. Instalar dependencias:
```bash
npm install
```

2. Iniciar el servidor de desarrollo:
```bash
npm run dev
```

3. Abrir [http://localhost:3000](http://localhost:3000) en el navegador

## 🏗️ Scripts Disponibles

- `npm run dev` - Inicia el servidor de desarrollo
- `npm run build` - Construye la aplicación para producción
- `npm run preview` - Previsualiza la construcción de producción
- `npm run lint` - Ejecuta el linter
- `npm run type-check` - Verifica los tipos TypeScript

## 📁 Estructura del Proyecto

```
src/
├── components/          # Componentes reutilizables
│   ├── ui/             # Componentes de UI base
│   └── LoginForm.tsx   # Formulario de login
├── pages/              # Páginas de la aplicación
│   ├── LoginPage.tsx   # Página de inicio de sesión
│   └── DashboardPage.tsx # Dashboard principal
├── types/              # Definiciones de tipos TypeScript
├── lib/                # Utilidades y configuraciones
├── hooks/              # Hooks personalizados
├── App.tsx             # Componente principal
├── main.tsx            # Punto de entrada
└── globals.css         # Estilos globales
```

## 🔐 Funcionalidades de Autenticación

### Login
- Selección de sucursal
- Validación de email y contraseña
- Opción "Recordarme"
- Recuperación de contraseña

### Verificación 2FA
- Código de 6 dígitos
- Reenvío de código
- Validación en tiempo real

## 📊 Dashboard

El dashboard incluye:

- **Métricas principales**: Préstamos activos, total prestado, clientes activos, tasa de recuperación
- **Acciones rápidas**: Crear préstamo, gestionar clientes, ver reportes
- **Actividad reciente**: Últimas transacciones y eventos del sistema
- **Navegación intuitiva**: Header con menú principal y herramientas

## 🎨 Diseño

- **Tema verde corporativo** para el sector financiero
- **Interfaz limpia y profesional**
- **Componentes accesibles** con Radix UI
- **Responsive design** para todos los dispositivos
- **Animaciones sutiles** para mejor UX

## 🔧 Configuración

### Tailwind CSS
El proyecto incluye configuración personalizada de Tailwind con:
- Variables CSS para temas
- Componentes personalizados
- Animaciones
- Responsive breakpoints

### TypeScript
Configuración estricta con:
- Verificación de tipos
- Path mapping (@/* para src/*)
- Linting automático

## 🚀 Despliegue

Para construir para producción:

```bash
npm run build
```

Los archivos se generarán en el directorio `dist/`.

## 📝 Próximas Funcionalidades

- [ ] Gestión completa de préstamos
- [ ] Sistema de clientes avanzado
- [ ] Reportes y analytics
- [ ] Notificaciones en tiempo real
- [ ] Integración con backend
- [ ] Sistema de roles y permisos
- [ ] Exportación de datos
- [ ] Modo oscuro

## 🤝 Contribución

1. Fork del proyecto
2. Crear rama de feature (`git checkout -b feature/AmazingFeature`)
3. Commit de cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

## 📄 Licencia

Este proyecto es privado y confidencial.

---

Desarrollado con ❤️ para FinancePro
