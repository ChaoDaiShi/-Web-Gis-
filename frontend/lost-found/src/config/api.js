const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:5000/api';

export default {
  API_BASE,
  endpoints: {
    profile: `${API_BASE}/profile`,
    myPublish: `${API_BASE}/my/publish`,
    myClaim: `${API_BASE}/my/claim`,
    login: `${API_BASE}/auth/login`,
    register: `${API_BASE}/auth/register`,
    logout: `${API_BASE}/auth/logout`,
  }
};
