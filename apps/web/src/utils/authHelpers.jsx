// src/utils/authHelpers.js

import axios from 'axios';
import { BASE_URL, REFRESH_TOKEN_NAME, TOKEN_NAME } from './constants';

// Utility function to get a token from localStorage
export const getTokenFromLocalStorage = (tokenName) => {
  return localStorage.getItem(tokenName);
};

// Function to refresh the access token using the refresh token from localStorage
export const refreshAccessToken = async () => {
  try {
    const refreshToken = getTokenFromLocalStorage(REFRESH_TOKEN_NAME);
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await axios.post(
      `${BASE_URL}/token/refresh/`,
      { refresh_token: refreshToken },
      { withCredentials: true }
    );

    const { access } = response.data;
    if (access) {
      localStorage.setItem(TOKEN_NAME, access);
      return access;
    }
    return null;
  } catch (error) {
    return null;
  }
};

// Login function (stores user & tokens in localStorage)
export const loginUser = async (credentials) => {
  try {
    const response = await axios.post(`${BASE_URL}/users/login/`, credentials, { withCredentials: true });
    const { access, refresh, user } = response.data;

    // Save tokens and user info in localStorage
    localStorage.setItem(TOKEN_NAME, access);
    localStorage.setItem(REFRESH_TOKEN_NAME, refresh);
    localStorage.setItem('user', JSON.stringify(user));

    return { success: true, user };
  } catch (error) {
    return { success: false, error: error.response?.data || { message: 'Unexpected error occurred' } };
  }
};

// Logout function (clears user & tokens from localStorage)
export const logoutUser = async () => {
  try {
    const accessToken = getTokenFromLocalStorage(TOKEN_NAME);
    if (accessToken) {
      await axios.post(
        `${BASE_URL}/users/logout/`,
        {},
        {
          headers: { Authorization: `Bearer ${accessToken}` },
          withCredentials: true,
        }
      );
    }

    localStorage.removeItem('user');
    localStorage.removeItem(TOKEN_NAME);
    localStorage.removeItem(REFRESH_TOKEN_NAME);
  } catch (error) {
  }
};
