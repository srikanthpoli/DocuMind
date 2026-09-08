import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { API_CONFIG } from '../config/api.config';

export interface UploadResponse {
  message: string;
  files: string[];
  chunks_indexed: number;
}

export interface DocumentListResponse {
  files: string[];
  count: number;
}

@Injectable({ providedIn: 'root' })
export class DocumentService {
  private readonly http = inject(HttpClient);

  listDocuments(): Observable<DocumentListResponse> {
    return this.http.get<DocumentListResponse>(
      `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.documents}`
    );
  }

  uploadPdf(file: File): Observable<UploadResponse> {
    const formData = new FormData();
    formData.append('files', file);
    return this.http.post<UploadResponse>(
      `${API_CONFIG.baseUrl}${API_CONFIG.endpoints.upload}`,
      formData
    );
  }
}
