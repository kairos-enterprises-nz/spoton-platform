// src/utils/constants.jsx
export const BASE_URL = import.meta.env.VITE_BASE_URL;
export const TOKEN_NAME = 'access_token'; 
export const REFRESH_TOKEN_NAME = 'refresh_token';

export const getTokenFromLocalStorage = () => {
  return localStorage.getItem(TOKEN_NAME);  // Use the TOKEN_NAME constant
};
