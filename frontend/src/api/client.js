import axios from 'axios';

const getCsrfToken = () => {
  const match = document.cookie.match(/csrf_access_token=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : '';
};

const client = axios.create({
  baseURL: '/api',
  withCredentials: true,
});

// Attach CSRF token to every state-changing request
client.interceptors.request.use((config) => {
  if (['post', 'put', 'delete', 'patch'].includes(config.method)) {
    config.headers['X-CSRF-TOKEN'] = getCsrfToken();
  }
  return config;
});

// Auto-refresh on 401 and replay the original request
let isRefreshing = false;
let pendingQueue = [];

const drainQueue = (error) => {
  pendingQueue.forEach(({ resolve, reject }) =>
    error ? reject(error) : resolve()
  );
  pendingQueue = [];
};

client.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config;

    if (error.response?.status === 401 && !original._retry && !original._skipRefresh) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          pendingQueue.push({ resolve, reject });
        })
          .then(() => client(original))
          .catch((err) => Promise.reject(err));
      }

      original._retry = true;
      isRefreshing = true;

      try {
        await client.post('/auth/refresh');
        drainQueue(null);
        return client(original);
      } catch (refreshError) {
        drainQueue(refreshError);
        const publicPaths = ['/login', '/register'];
        if (!publicPaths.some((p) => window.location.pathname.startsWith(p))) {
          window.location.href = '/login';
        }
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default client;
