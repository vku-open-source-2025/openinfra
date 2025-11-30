import axios, {
    type AxiosInstance,
    type AxiosError,
    type InternalAxiosRequestConfig,
} from "axios";
import { useAuthStore } from "../stores";
import type { AxiosResponse } from "axios";

// Create main API instance
export const httpClient: AxiosInstance = axios.create({
    baseURL: import.meta.env.VITE_BASE_API_URL || "/api/v1",
    timeout: 30000,
    headers: {
        "Content-Type": "application/json",
    },
});

// Create leaderboard API instance
export const leaderboardApi: AxiosInstance = axios.create({
    baseURL:
        import.meta.env.VITE_LEADERBOARD_URL ||
        "https://contribapi.openinfra.space/api",
    timeout: 30000,
    headers: {
        "Content-Type": "application/json",
    },
});

// Request interceptor for adding auth token
const requestInterceptor = (config: InternalAxiosRequestConfig) => {
    const token = useAuthStore.getState().accessToken;

    if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
};

// Request error interceptor
const requestErrorInterceptor = (error: AxiosError) => {
    console.error("Request Error:", error);
    return Promise.reject(error);
};

// Response interceptor for handling errors
const responseInterceptor = (response: AxiosResponse) => {
    return response;
};

// Response error interceptor
const responseErrorInterceptor = (error: AxiosError) => {
    if (error.response) {
        const { status } = error.response;

        switch (status) {
            case 401:
                // Unauthorized - clear auth and redirect to login
                useAuthStore.getState().logout();

                // Only redirect if not already on a public page
                if (window.location.pathname.includes("/admin")) {
                    window.location.href = "/";
                }
                break;

            case 403:
                console.error("Access forbidden");
                break;

            case 404:
                console.error("Resource not found");
                break;

            case 500:
                console.error("Server error");
                break;

            default:
                console.error(`Error ${status}:`, error.message);
        }
    } else if (error.request) {
        // Request was made but no response received
        console.error("Network Error:", error.message);
    } else {
        // Something happened in setting up the request
        console.error("Request Setup Error:", error.message);
    }

    return Promise.reject(error);
};

// Apply interceptors to main API
httpClient.interceptors.request.use(
    requestInterceptor,
    requestErrorInterceptor
);
httpClient.interceptors.response.use(
    responseInterceptor,
    responseErrorInterceptor
);

// Apply interceptors to leaderboard API (if needed)
leaderboardApi.interceptors.request.use(
    requestInterceptor,
    requestErrorInterceptor
);
leaderboardApi.interceptors.response.use(
    responseInterceptor,
    responseErrorInterceptor
);

export default httpClient;
