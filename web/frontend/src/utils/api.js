/**
 * Centralized API configuration utility
 * Provides consistent API base URL handling across all frontend components
 */

/**
 * Get the correct API base URL for the current environment
 * @returns {string} The API base URL
 */
export const getApiBase = () => {
  // In Replit environment, construct proper backend URL
  if (window.location.hostname.includes('replit.dev')) {
    // Build backend URL using current hostname but port 8000
    const currentUrl = new URL(window.location.href)
    return `${currentUrl.protocol}//${currentUrl.hostname}:8000`
  }
  
  // For local development
  return 'http://localhost:8000'
}

/**
 * Enhanced fetch wrapper with error handling and retry logic
 * @param {string} endpoint - API endpoint (without base URL)
 * @param {object} options - Fetch options
 * @returns {Promise<Response>} Fetch response
 */
export const apiFetch = async (endpoint, options = {}) => {
  const apiBase = getApiBase()
  const url = `${apiBase}${endpoint}`
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    },
    ...options
  }
  
  try {
    const response = await fetch(url, defaultOptions)
    
    // Check if response is ok
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    return response
  } catch (error) {
    console.error(`API call failed: ${url}`, error)
    throw error
  }
}

/**
 * Enhanced fetch wrapper that returns JSON directly
 * @param {string} endpoint - API endpoint (without base URL)
 * @param {object} options - Fetch options
 * @returns {Promise<object>} JSON response
 */
export const apiRequest = async (endpoint, options = {}) => {
  const response = await apiFetch(endpoint, options)
  return await response.json()
}

/**
 * Utility functions for common API patterns
 */
export const api = {
  // GET request
  get: (endpoint) => apiRequest(endpoint),
  
  // POST request
  post: (endpoint, data) => apiRequest(endpoint, {
    method: 'POST',
    body: JSON.stringify(data)
  }),
  
  // PUT request
  put: (endpoint, data) => apiRequest(endpoint, {
    method: 'PUT',
    body: JSON.stringify(data)
  }),
  
  // DELETE request
  delete: (endpoint) => apiRequest(endpoint, {
    method: 'DELETE'
  }),
  
  // POST with FormData (for file uploads)
  postFormData: (endpoint, formData) => apiFetch(endpoint, {
    method: 'POST',
    body: formData,
    headers: {} // Let browser set Content-Type for FormData
  }),
  
  // GET with query parameters
  getWithParams: (endpoint, params) => {
    const url = new URL(`${getApiBase()}${endpoint}`)
    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        url.searchParams.append(key, value)
      }
    })
    return fetch(url.toString()).then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return response.json()
    })
  }
}

export default { getApiBase, apiFetch, apiRequest, api }