import { createContext, useContext, useState, useEffect, useRef, useCallback } from 'react';
import client from '../api/client';
import { useAuth } from './AuthContext';

const REFRESH_INTERVAL = 60 * 60 * 1000; // 1 hour — matches backend Redis TTL

const RatesContext = createContext({ rates: {}, loading: true });

export function RatesProvider({ children }) {
  const { user } = useAuth();
  const [rates, setRates] = useState({});
  const [loading, setLoading] = useState(true);
  const lastFetchedAt = useRef(0);

  const fetchRates = useCallback(async () => {
    try {
      const res = await client.get('/rates/current');
      const map = {};
      for (const r of res.data) {
        if (r.base_ccy === 'UAH' && r.ccy) {
          map[r.ccy] = (parseFloat(r.buy) + parseFloat(r.sale)) / 2;
        }
      }
      setRates(map);
      lastFetchedAt.current = Date.now();
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial fetch when user logs in
  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }
    setLoading(true);
    fetchRates();
  }, [user?.id, fetchRates]);

  // Refresh on tab visibility change, but no more than once per hour
  useEffect(() => {
    if (!user) return;

    const handleVisibilityChange = () => {
      if (document.visibilityState !== 'visible') return;
      if (Date.now() - lastFetchedAt.current >= REFRESH_INTERVAL) {
        fetchRates();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [user, fetchRates]);

  return (
    <RatesContext.Provider value={{ rates, loading }}>
      {children}
    </RatesContext.Provider>
  );
}

export const useRates = () => useContext(RatesContext);
