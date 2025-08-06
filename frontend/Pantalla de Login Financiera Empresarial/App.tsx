import { LoginForm } from "./components/LoginForm";

export default function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center p-4">
      {/* Patrón de fondo sutil */}
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGcgZmlsbD0ibm9uZSIgZmlsbC1ydWxlPSJldmVub2RkIj4KPGcgZmlsbD0iIzAwMDAwMCIgZmlsbC1vcGFjaXR5PSIwLjAyIj4KPGNpcmNsZSBjeD0iNSIgY3k9IjUiIHI9IjUiLz4KPC9nPgo8L2c+Cjwvc3ZnPg==')] opacity-20"></div>
      
      <div className="relative w-full max-w-md">
        {/* Logo/Branding corporativo discreto */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center space-x-3 mb-2">
            <div className="h-8 w-8 bg-green-600 rounded-lg flex items-center justify-center">
              <div className="h-5 w-5 bg-white rounded opacity-90"></div>
            </div>
            <h1 className="text-xl text-gray-800 tracking-wide">FinancePro</h1>
          </div>
          <p className="text-sm text-gray-500">Plataforma Empresarial</p>
        </div>
        
        {/* Formulario de login */}
        <LoginForm />
        
        {/* Footer discreto */}
        <div className="text-center mt-8">
          <p className="text-xs text-gray-400">
            © 2025 FinancePro. Todos los derechos reservados.
          </p>
          <div className="flex justify-center space-x-4 mt-2">
            <button className="text-xs text-gray-400 hover:text-gray-600">
              Términos de uso
            </button>
            <span className="text-xs text-gray-300">•</span>
            <button className="text-xs text-gray-400 hover:text-gray-600">
              Política de privacidad
            </button>
          </div>
        </div>
      </div>
      
      {/* Elementos decorativos sutiles */}
      <div className="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-32 h-32 bg-green-100 rounded-full opacity-20 blur-3xl"></div>
        <div className="absolute bottom-20 right-20 w-40 h-40 bg-green-200 rounded-full opacity-15 blur-3xl"></div>
      </div>
    </div>
  );
}