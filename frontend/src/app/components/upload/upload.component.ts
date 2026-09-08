import { CommonModule } from '@angular/common';
import { Component, inject, OnInit } from '@angular/core';

import { DocumentService } from '../../services/document.service';

@Component({
  selector: 'app-upload',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './upload.component.html',
  styleUrl: './upload.component.css'
})
export class UploadComponent implements OnInit {
  private readonly documentService = inject(DocumentService);

  selectedFile: File | null = null;
  uploadedFiles: string[] = [];
  uploadState: 'idle' | 'uploading' | 'success' | 'error' = 'idle';
  statusMessage = 'Ready for your first document';
  errorMessage = '';

  ngOnInit(): void {
    this.documentService.listDocuments().subscribe({
      next: (response) => {
        this.uploadedFiles = response.files;
        if (response.count > 0) {
          this.statusMessage = `${response.count} document${response.count === 1 ? '' : 's'} ready for questions`;
        }
      },
      error: () => {
        this.errorMessage = 'Could not load existing documents. Check that the API is running.';
      }
    });
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] ?? null;
    this.errorMessage = '';

    if (file && file.type !== 'application/pdf') {
      this.selectedFile = null;
      this.errorMessage = 'Please choose a PDF file.';
      return;
    }

    this.selectedFile = file;
  }

  uploadDocument(): void {
    if (!this.selectedFile || this.uploadState === 'uploading') {
      return;
    }

    this.uploadState = 'uploading';
    this.errorMessage = '';
    this.statusMessage = 'Reading and indexing your PDF...';

    this.documentService.uploadPdf(this.selectedFile).subscribe({
      next: (response) => {
        this.uploadedFiles = [...new Set([...this.uploadedFiles, ...response.files])];
        this.uploadState = 'success';
        this.statusMessage = `${response.chunks_indexed} chunks ready for questions`;
        this.selectedFile = null;
      },
      error: () => {
        this.uploadState = 'error';
        this.statusMessage = 'Upload failed';
        this.errorMessage = 'The backend could not index this PDF. Check that the API is running.';
      }
    });
  }
}
