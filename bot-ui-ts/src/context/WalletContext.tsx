import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import type { User, AuthState } from '../types';

interface WalletContextType extends AuthState {
  login: (walletAddress: string) => Promise<void>;
  register: () => Promise<void>;
  logout: () => void;
  wsConnection: WebSocket | null;
  isWsConnected: boolean;
}

const WalletContext = createContext<WalletContextType | undefined>(undefined);

export const useWallet = () => {
  const context = useContext(WalletContext);
  if (!context) {
    throw new Error('useWallet must be used within WalletProvider');
  }
  return context;
};

interface WalletProviderProps {
  children: ReactNode;
}

const API_BASE = 'http://localhost:8000';
const WS_URL = 'ws://localhost:8765';

export const WalletProvider: React.FC<WalletProviderProps> = ({ children }) => {
  const [authState, setAuthState] = useState<AuthState>({
    isAuthenticated: false,
    user: null,
    walletAddress: null,
  });
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null);
  const [isWsConnected, setIsWsConnected] = useState(false);

  // Load saved wallet from localStorage on mount
  useEffect(() => {
    const savedWallet = localStorage.getItem('wallet_address');
    if (savedWallet) {
      fetchUserData(savedWallet).then(user => {
        if (user) {
          setAuthState({
            isAuthenticated: true,
            user,
            walletAddress: savedWallet,
          });
          connectWebSocket(savedWallet);
        }
      });
    }
  }, []);

  const fetchUserData = async (walletAddress: string): Promise<User | null> => {
    try {
      const response = await fetch(`${API_BASE}/api/user/${walletAddress}`);
      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
      console.error('Failed to fetch user data:', error);
    }
    return null;
  };

  const connectWebSocket = (walletAddress: string) => {
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => {
      console.log('WebSocket connected, sending AUTH...');
      ws.send(JSON.stringify({
        type: 'AUTH',
        wallet_address: walletAddress,
      }));
      setIsWsConnected(true);
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'AUTH_SUCCESS') {
        console.log('✅ WebSocket authenticated successfully');
      } else if (message.type === 'ERROR') {
        console.error('WebSocket error:', message.message);
        ws.close();
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsWsConnected(false);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsWsConnected(false);
      // Attempt reconnection after delay
      setTimeout(() => {
        if (authState.walletAddress) {
          connectWebSocket(authState.walletAddress);
        }
      }, 5000);
    };

    setWsConnection(ws);
  };

  const login = async (walletAddress: string) => {
    try {
      const user = await fetchUserData(walletAddress);
      if (user) {
        setAuthState({
          isAuthenticated: true,
          user,
          walletAddress,
        });
        localStorage.setItem('wallet_address', walletAddress);
        connectWebSocket(walletAddress);
      } else {
        throw new Error('Invalid wallet address');
      }
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  };

  const register = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/register`, {
        method: 'POST',
      });
      
      if (response.ok) {
        const data = await response.json();
        const user: User = {
          wallet_address: data.wallet_address,
          initial_sol_balance: data.initial_sol_balance,
          created_at: data.created_at,
        };
        
        setAuthState({
          isAuthenticated: true,
          user,
          walletAddress: data.wallet_address,
        });
        localStorage.setItem('wallet_address', data.wallet_address);
        connectWebSocket(data.wallet_address);
      } else {
        throw new Error('Registration failed');
      }
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  };

  const logout = () => {
    if (wsConnection) {
      wsConnection.close();
    }
    setAuthState({
      isAuthenticated: false,
      user: null,
      walletAddress: null,
    });
    setWsConnection(null);
    setIsWsConnected(false);
    localStorage.removeItem('wallet_address');
  };

  return (
    <WalletContext.Provider
      value={{
        ...authState,
        login,
        register,
        logout,
        wsConnection,
        isWsConnected,
      }}
    >
      {children}
    </WalletContext.Provider>
  );
};
