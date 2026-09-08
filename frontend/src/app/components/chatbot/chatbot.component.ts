import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, EventEmitter, inject, Input, OnChanges, Output, SimpleChanges } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ChatService } from '../../services/chat.service';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

@Component({
  selector: 'app-chatbot',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chatbot.component.html',
  styleUrl: './chatbot.component.css'
})
export class ChatbotComponent implements OnChanges {
  @Input({ required: true }) sessionId = '';
  @Output() newSessionRequested = new EventEmitter<void>();

  private readonly chatService = inject(ChatService);

  messages: ChatMessage[] = [];
  message = '';
  chatState: 'idle' | 'sending' | 'error' = 'idle';
  errorMessage = '';

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['sessionId'] && !changes['sessionId'].firstChange) {
      this.messages = [];
      this.message = '';
      this.chatState = 'idle';
      this.errorMessage = '';
    }
  }

  startNewSession(): void {
    this.newSessionRequested.emit();
  }

  endSession(): void {
    if (this.chatState === 'sending') {
      return;
    }

    this.chatState = 'sending';
    this.errorMessage = '';
    this.chatService.endSession(this.sessionId).subscribe({
      next: () => {
        this.newSessionRequested.emit();
      },
      error: () => {
        this.chatState = 'error';
        this.errorMessage = 'The session could not be ended. Please try again.';
      }
    });
  }

  sendMessage(): void {
    const text = this.message.trim();
    if (!text || this.chatState === 'sending') {
      return;
    }

    this.messages = [...this.messages, { role: 'user', content: text }];
    this.message = '';
    this.chatState = 'sending';
    this.errorMessage = '';

    this.chatService.ask(this.sessionId, text).subscribe({
      next: (response) => {
        this.messages = [...this.messages, { role: 'assistant', content: response.answer }];
        this.chatState = 'idle';
      },
      error: (error: HttpErrorResponse) => {
        this.chatState = 'error';
        this.errorMessage = error.error?.detail
          ?? 'Chat is unavailable. Check your xAI key and backend connection.';
      }
    });
  }

  onMessageKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }
}
