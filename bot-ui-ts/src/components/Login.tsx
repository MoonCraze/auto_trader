import React, { useState } from 'react';
import { useWallet } from '../context/WalletContext';

const Login: React.FC = () => {
  const { register, login } = useWallet();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showLoginForm, setShowLoginForm] = useState(false);
  const [loginWallet, setLoginWallet] = useState('');

  const handleRegister = async () => {
    setIsLoading(true);
    setError(null);
    try {
      await register();
    } catch (err) {
      setError('Failed to create wallet. Please try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!loginWallet.trim()) {
      setError('Please enter a wallet address');
      return;
    }
    
    setIsLoading(true);
    setError(null);
    try {
      await login(loginWallet.trim());
    } catch (err) {
      setError('Invalid wallet address. Please check and try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Auto Trader Bot</h1>
          <p className="text-gray-400">Connect your synthetic wallet to start trading</p>
        </div>

        {/* Main Card */}
        <div className="bg-slate-800 rounded-xl shadow-2xl p-8 border border-slate-700">
          {!showLoginForm ? (
            <>
              {/* Register Section */}
              <div className="mb-6">
                <h2 className="text-xl font-semibold text-white mb-4">Create New Wallet</h2>
                {/* <p className="text-gray-400 text-sm mb-4">
                  Generate a synthetic wallet with a random SOL balance between 10-20 SOL
                </p> */}
                <button
                  onClick={handleRegister}
                  disabled={isLoading}
                  className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                      <span>Creating Wallet...</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                      <span>Create Wallet</span>
                    </>
                  )}
                </button>
              </div>

              {/* Divider */}
              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-slate-600"></div>
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-2 bg-slate-800 text-gray-400">OR</span>
                </div>
              </div>

              {/* Login Toggle */}
              <button
                onClick={() => setShowLoginForm(true)}
                className="w-full bg-slate-700 hover:bg-slate-600 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200"
              >
                Login with Existing Wallet
              </button>
            </>
          ) : (
            <>
              {/* Login Form */}
              <div className="mb-4">
                <button
                  onClick={() => setShowLoginForm(false)}
                  className="text-gray-400 hover:text-white mb-4 flex items-center gap-2"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                  Back
                </button>
                <h2 className="text-xl font-semibold text-white mb-4">Login to Wallet</h2>
              </div>
              
              <form onSubmit={handleLogin}>
                <div className="mb-4">
                  <label className="block text-gray-400 text-sm mb-2">
                    Wallet Address
                  </label>
                  <input
                    type="text"
                    value={loginWallet}
                    onChange={(e) => setLoginWallet(e.target.value)}
                    placeholder="Enter your wallet address"
                    className="w-full bg-slate-700 text-white border border-slate-600 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    disabled={isLoading}
                  />
                </div>
                
                <button
                  type="submit"
                  disabled={isLoading || !loginWallet.trim()}
                  className="w-full bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                      <span>Logging In...</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
                      </svg>
                      <span>Login</span>
                    </>
                  )}
                </button>
              </form>
            </>
          )}

          {/* Error Message */}
          {error && (
            <div className="mt-4 bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-3 rounded-lg text-sm">
              {error}
            </div>
          )}
        </div>

        {/* Footer */}
        {/* <p className="text-center text-gray-500 text-sm mt-6">
          Synthetic wallets are for demonstration purposes only
        </p> */}
      </div>
    </div>
  );
};

export default Login;
