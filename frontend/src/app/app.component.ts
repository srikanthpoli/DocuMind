import { Component, ViewEncapsulation } from '@angular/core';

import { ChatbotComponent } from './components/chatbot/chatbot.component';
import { UploadComponent } from './components/upload/upload.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [ChatbotComponent, UploadComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
  encapsulation: ViewEncapsulation.None
})
export class AppComponent {
  sessionId = this.getSessionId();

  startNewSession(): void {
    this.sessionId = this.createSessionId();
    sessionStorage.setItem('documind-session-id', this.sessionId);
  }

  private getSessionId(): string {
    const storageKey = 'documind-session-id';
    const existingId = sessionStorage.getItem(storageKey);
    if (existingId) {
      return existingId;
    }

    const newId = this.createSessionId();
    sessionStorage.setItem(storageKey, newId);
    return newId;
  }

  private createSessionId(): string {
    return crypto.randomUUID();
  }
}
