// src/services/Onboarding.jsx
import apiClient from './apiClient'; // Uses the apiClient with the token refresh interceptor

const API_BASE = '/web/onboarding';

export async function getOnboardingProgress(tempSessionId = null) {
  const params = tempSessionId ? { temp_session_id: tempSessionId } : {};
  const { data } = await apiClient.get(`${API_BASE}/progress/`, { params });
  return data;
}

export async function saveOnboardingStep(step, stepData, autosave = false) {
  const { data } = await apiClient.post(`${API_BASE}/progress/`, {
    step,
    data: stepData,
    autosave,
  });
  return data;
}

export async function finalizeOnboarding(submissionData) {
  const { data } = await apiClient.post(`${API_BASE}/finalize/`, submissionData);
  return data;
}
