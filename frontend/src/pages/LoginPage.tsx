import React from 'react';
import { LoginFormWithBranch } from '../components/LoginFormWithBranch';

export const LoginPage = React.memo(() => {
  return (
    <div className="min-h-screen bg-gray-50">
      <LoginFormWithBranch />
    </div>
  );
});

LoginPage.displayName = 'LoginPage';
