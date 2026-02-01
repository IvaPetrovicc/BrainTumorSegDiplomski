import axios from 'axios'

// Allow overriding via env; default to direct FastAPI dev server.
const baseURL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export const api = axios.create({
  baseURL,
})
