export const API_CONFIG = {
  baseUrl: 'http://127.0.0.1:8000',
  endpoints: {
    upload: '/upload',
    documents: '/documents',
    chat: '/chat',
    health: '/health',
    sessions: '/sessions'
  }
} as const;
