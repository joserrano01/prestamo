import { useState } from "react";
import { useNavigate } from 'react-router-dom';
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { Checkbox } from "./ui/checkbox";
import {
  InputOTP,
  InputOTPGroup,
  InputOTPSlot,
} from "./ui/input-otp";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import {
  Eye,
  EyeOff,
  Shield,
  ArrowLeft,
  Building2,
} from "lucide-react";

// Lista de sucursales disponibles
const sucursales = [
  {
    value: "central",
    label: "Oficina Central - Ciudad de México",
  },
  { value: "guadalajara", label: "Sucursal Guadalajara" },
  { value: "monterrey", label: "Sucursal Monterrey" },
  { value: "puebla", label: "Sucursal Puebla" },
  { value: "tijuana", label: "Sucursal Tijuana" },
  { value: "merida", label: "Sucursal Mérida" },
  { value: "cancun", label: "Sucursal Cancún" },
  { value: "leon", label: "Sucursal León" },
];

export function LoginForm() {
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [showTwoFA, setShowTwoFA] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [sucursal, setSucursal] = useState("");
  const [otpValue, setOtpValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    // Simular validación de credenciales
    setTimeout(() => {
      if (email && password && sucursal) {
        setShowTwoFA(true);
      }
      setIsLoading(false);
    }, 1500);
  };

  const handleTwoFAVerification = async (
    e: React.FormEvent,
  ) => {
    e.preventDefault();
    setIsLoading(true);

    // Simular verificación 2FA
    setTimeout(() => {
      console.log(
        "Login exitoso con 2FA - Sucursal:",
        sucursal,
      );
      // Redirigir al dashboard
      navigate('/dashboard');
      setIsLoading(false);
    }, 2000);
  };

  const resetToLogin = () => {
    setShowTwoFA(false);
    setOtpValue("");
  };

  if (showTwoFA) {
    return (
      <Card className="w-full max-w-md bg-white border-0 shadow-lg">
        <CardHeader className="text-center pb-2">
          <div className="flex items-center justify-center mb-4">
            <div className="h-12 w-12 bg-green-600 rounded-full flex items-center justify-center">
              <Shield className="h-6 w-6 text-white" />
            </div>
          </div>
          <CardTitle className="text-xl text-gray-900">
            Verificación de Seguridad
          </CardTitle>
          <CardDescription className="text-gray-600">
            Ingresa el código de 6 dígitos enviado a tu
            dispositivo de autenticación
          </CardDescription>
          {sucursal && (
            <div className="flex items-center justify-center mt-2 text-sm text-gray-500">
              <Building2 className="h-4 w-4 mr-1" />
              {
                sucursales.find((s) => s.value === sucursal)
                  ?.label
              }
            </div>
          )}
        </CardHeader>
        <CardContent className="space-y-6">
          <form onSubmit={handleTwoFAVerification}>
            <div className="space-y-4">
              <div className="flex justify-center">
                <InputOTP
                  maxLength={6}
                  value={otpValue}
                  onChange={setOtpValue}
                  className="gap-2"
                >
                  <InputOTPGroup>
                    <InputOTPSlot
                      index={0}
                      className="w-12 h-12 text-lg"
                    />
                    <InputOTPSlot
                      index={1}
                      className="w-12 h-12 text-lg"
                    />
                    <InputOTPSlot
                      index={2}
                      className="w-12 h-12 text-lg"
                    />
                    <InputOTPSlot
                      index={3}
                      className="w-12 h-12 text-lg"
                    />
                    <InputOTPSlot
                      index={4}
                      className="w-12 h-12 text-lg"
                    />
                    <InputOTPSlot
                      index={5}
                      className="w-12 h-12 text-lg"
                    />
                  </InputOTPGroup>
                </InputOTP>
              </div>

              <div className="text-center text-sm text-gray-500">
                ¿No recibiste el código?{" "}
                <button
                  type="button"
                  className="text-green-600 hover:text-green-700 underline"
                >
                  Reenviar código
                </button>
              </div>

              <Button
                type="submit"
                className="w-full bg-green-600 hover:bg-green-700 text-white py-3"
                disabled={isLoading || otpValue.length !== 6}
              >
                {isLoading
                  ? "Verificando..."
                  : "Verificar código"}
              </Button>

              <Button
                type="button"
                variant="outline"
                className="w-full"
                onClick={resetToLogin}
                disabled={isLoading}
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Volver al login
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full max-w-md bg-white border-0 shadow-lg">
      <CardHeader className="text-center pb-6">
        <CardTitle className="text-2xl text-gray-900">
          Iniciar Sesión
        </CardTitle>
        <CardDescription className="text-gray-600">
          Accede a tu cuenta empresarial
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleLogin} className="space-y-4">
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="sucursal" className="text-gray-700">
                Sucursal
              </Label>
              <Select
                value={sucursal}
                onValueChange={setSucursal}
                required
              >
                <SelectTrigger className="h-11 bg-gray-50 border-gray-200 focus:border-green-500 focus:ring-green-500">
                  <div className="flex items-center">
                    <Building2 className="h-4 w-4 mr-2 text-gray-400" />
                    <SelectValue placeholder="Selecciona tu sucursal" />
                  </div>
                </SelectTrigger>
                <SelectContent>
                  {sucursales.map((sucursal) => (
                    <SelectItem
                      key={sucursal.value}
                      value={sucursal.value}
                    >
                      {sucursal.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="email" className="text-gray-700">
                Correo electrónico
              </Label>
              <Input
                id="email"
                type="email"
                placeholder="tu.email@empresa.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="h-11 bg-gray-50 border-gray-200 focus:border-green-500 focus:ring-green-500"
                required
              />
            </div>

            <div className="space-y-2">
              <Label
                htmlFor="password"
                className="text-gray-700"
              >
                Contraseña
              </Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="h-11 bg-gray-50 border-gray-200 focus:border-green-500 focus:ring-green-500 pr-10"
                  required
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="remember"
                  checked={rememberMe}
                  onCheckedChange={setRememberMe}
                  className="data-[state=checked]:bg-green-600 data-[state=checked]:border-green-600"
                />
                <Label
                  htmlFor="remember"
                  className="text-sm text-gray-600"
                >
                  Recordarme
                </Label>
              </div>
              <button
                type="button"
                className="text-sm text-green-600 hover:text-green-700 underline"
              >
                ¿Olvidaste tu contraseña?
              </button>
            </div>

            <Button
              type="submit"
              className="w-full bg-green-600 hover:bg-green-700 text-white py-3 text-base"
              disabled={
                isLoading || !email || !password || !sucursal
              }
            >
              {isLoading
                ? "Iniciando sesión..."
                : "Iniciar Sesión"}
            </Button>
          </div>
        </form>

        <div className="text-center mt-6">
          <p className="text-sm text-gray-500">
            ¿Necesitas ayuda?{" "}
            <button className="text-green-600 hover:text-green-700 underline">
              Contactar soporte
            </button>
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
