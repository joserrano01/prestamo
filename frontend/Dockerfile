# Etapa de construcción
FROM node:18-alpine AS builder

WORKDIR /app

# Copiar archivos de configuración de dependencias
COPY package*.json ./
COPY tsconfig*.json ./
COPY vite.config.ts ./
COPY tailwind.config.js ./
COPY postcss.config.js ./

# Instalar dependencias (incluyendo dev dependencies para build)
RUN npm ci

# Copiar código fuente
COPY src/ ./src/
COPY index.html ./

# Crear directorio public si no existe
RUN mkdir -p ./public

# Construir la aplicación
RUN npm run build

# Etapa de producción
FROM nginx:alpine

# Instalar herramientas de red
RUN apk add --no-cache curl wget nmap traceroute bind-tools iputils

# Copiar configuración personalizada de nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar archivos construidos
COPY --from=builder /app/dist /usr/share/nginx/html

# Exponer puerto
EXPOSE 80

# Comando por defecto
CMD ["nginx", "-g", "daemon off;"]
