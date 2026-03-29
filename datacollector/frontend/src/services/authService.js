import axios from 'axios';
import { API_URL } from '../config';

const AuthService = {
    login: async (username, password) => {
        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        const response = await axios.post(`${API_URL}/api/auth/login`, {
            username,
            password
        });

        if (response.data.access_token) {
            localStorage.setItem('access_token', response.data.access_token);
            localStorage.setItem('refresh_token', response.data.refresh_token);
        }
        return response.data;
    },

    logout: () => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
    },

    getCurrentUser: () => {
        const token = localStorage.getItem('access_token');
        return token ? { username: 'admin' } : null; // Simple check
    },

    isAuthenticated: () => {
        return !!localStorage.getItem('access_token');
    }
};

export default AuthService;
