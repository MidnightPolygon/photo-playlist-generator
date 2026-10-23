import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  protected readonly title = signal('frontend');

  selectedFileName = '';
  photoPreviewUrl = '';
  selectedPhoto: File | null = null;

  
onPhotoSelected(event: Event): void {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];

  if (file) {
    // Release the previous preview URL
    if (this.photoPreviewUrl) {
      URL.revokeObjectURL(this.photoPreviewUrl);
    }

    this.selectedPhoto = file;
    this.selectedFileName = file.name;
    this.photoPreviewUrl = URL.createObjectURL(file);

    console.log('Selected photograph:', file.name);
  }
}

removePhoto(input: HTMLInputElement): void {
  // Release the temporary preview URL
  if (this.photoPreviewUrl) {
    URL.revokeObjectURL(this.photoPreviewUrl);
  }

  // Clear the selected photograph
  this.selectedPhoto = null;
  this.selectedFileName = '';
  this.photoPreviewUrl = '';

  // Reset the browser's file input
  input.value = '';

  console.log('Photograph removed');
}

}