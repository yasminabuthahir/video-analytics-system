import axios from "axios";

const getBase = () => localStorage.getItem("backend_url") || "http://localhost:8000";

const api = axios.create();

api.interceptors.request.use((config) => {
  config.baseURL = getBase();
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export default api;