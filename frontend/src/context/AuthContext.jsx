import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import client from '../api/client';

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    client.get('/auth/me', { _skipRefresh: true })
      .then((res) => setUser(res.data))
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  const login = useCallback(async (email, password) => {
    const res = await client.post('/auth/login', { email, password });
    setUser(res.data);
    return res.data;
  }, []);

  const register = useCallback(async (email, password) => {
    const res = await client.post('/auth/register', { email, password });
    setUser(res.data);
    return res.data;
  }, []);

  const logout = useCallback(async () => {
    await client.post('/auth/logout').catch(() => {});
    setUser(null);
  }, []);

  const updateUser = useCallback(async (data) => {
    const res = await client.put('/auth/profile', data);
    setUser(res.data);
    return res.data;
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
