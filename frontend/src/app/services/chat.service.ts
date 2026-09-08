import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { API_CONFIG } from '../config/api.config';

export interface ChatResponse {
  answer: string;
}

@Injectable({ providedIn: 'root' })
export class ChatService {
  private readonly http = inject(HttpClient);

  ask(sessionId: string, message: string): Observable<ChatResponse> {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('message', message);
    return this.http.post<ChatResponse>(
      `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.chat}`,
      formData
    );
  }

  endSession(sessionId: string): Observable<{ session_id: string; cleared: boolean }> {
    return this.http.delete<{ session_id: string; cleared: boolean }>(
      `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.sessions}/${encodeURIComponent(sessionId)}`
    );
  }
}
