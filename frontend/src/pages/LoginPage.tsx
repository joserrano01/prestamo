import React from 'react';
import { LoginFormWithBranch } from '../components/LoginFormWithBranch';

export const LoginPage = React.memo(() => {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-100 p-4">
      <div className="w-full max-w-6xl bg-white rounded-2xl shadow-xl overflow-hidden flex flex-col md:flex-row border border-gray-200">
        {/* Left side - Form */}
        <div className="w-full md:w-1/2 p-8 md:p-12">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-r from-emerald-500 to-blue-600 rounded-2xl mb-6 shadow-lg">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
              </svg>
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-emerald-600 to-blue-600 bg-clip-text text-transparent mb-3">FinancePro</h1>
            <p className="text-slate-600 text-lg">Sistema de Gestión de Préstamos</p>
            <p className="text-slate-500 mt-1">Inicia sesión para continuar</p>
          </div>
          <LoginFormWithBranch />
        </div>
        
        {/* Right side - Professional Financial Service Image */}
        <div className="hidden md:block md:w-1/2 bg-gradient-to-br from-slate-700 to-slate-800 relative">
          <div className="flex flex-col justify-center items-center p-12 text-center h-full">
            <div className="relative z-10 max-w-sm">
              <h2 className="text-3xl font-bold mb-6 text-white drop-shadow-lg leading-tight">
                Soluciones Financieras Personalizadas
              </h2>
              <p className="text-slate-200 mb-8 text-lg leading-relaxed">
                Brindamos atención especializada y confiable para tus necesidades de préstamos
              </p>
              
              {/* Professional service illustration */}
              <div className="relative h-64 w-full max-w-sm mx-auto mb-8 rounded-lg overflow-hidden shadow-lg">
                <img 
                  src="https://images.unsplash.com/photo-1560472354-b33ff0c44a43?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80"
                  alt="Asesor financiero atendiendo cliente"
                  className="w-full h-full object-cover"
                />
              </div>

              {/* Features */}
              <div className="grid grid-cols-2 gap-4 text-left">
                <div className="flex items-center text-slate-200">
                  <div className="w-2 h-2 bg-emerald-400 rounded-full mr-3"></div>
                  <span className="text-sm">Asesoría Experta</span>
                </div>
                <div className="flex items-center text-slate-200">
                  <div className="w-2 h-2 bg-blue-400 rounded-full mr-3"></div>
                  <span className="text-sm">Proceso Rápido</span>
                </div>
                <div className="flex items-center text-slate-200">
                  <div className="w-2 h-2 bg-slate-400 rounded-full mr-3"></div>
                  <span className="text-sm">Tasas Competitivas</span>
                </div>
                <div className="flex items-center text-slate-200">
                  <div className="w-2 h-2 bg-slate-300 rounded-full mr-3"></div>
                  <span className="text-sm">Soporte 24/7</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
});

LoginPage.displayName = 'LoginPage';
