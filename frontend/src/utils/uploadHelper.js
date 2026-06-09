export class UploadManager {
  constructor() {
    this.uploadingCount = 0;
    this.callbacks = [];
  }

  isUploading() {
    return this.uploadingCount > 0;
  }

  onUploadStateChange(callback) {
    this.callbacks.push(callback);
  }

  offUploadStateChange(callback) {
    this.callbacks = this.callbacks.filter(cb => cb !== callback);
  }

  notifyChange() {
    this.callbacks.forEach(cb => cb(this.isUploading()));
  }

  async uploadFile(url, formData, onProgress) {
    this.uploadingCount++;
    this.notifyChange();

    try {
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
        signal: AbortController.signal
      });

      if (onProgress) {
        const reader = response.body.getReader();
        const contentLength = parseInt(response.headers.get('Content-Length') || '0');
        let receivedLength = 0;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          receivedLength += value.length;
          if (contentLength > 0) {
            const progress = Math.round((receivedLength / contentLength) * 100);
            onProgress(progress);
          }
        }
      }

      return await response.json();
    } finally {
      this.uploadingCount--;
      this.notifyChange();
    }
  }

  async uploadFiles(url, files, fieldName = 'images', onProgress) {
    this.uploadingCount += files.length;
    this.notifyChange();

    try {
      const results = [];
      let totalProgress = 0;
      const totalFiles = files.length;

      for (let i = 0; i < files.length; i++) {
        const formData = new FormData();
        formData.append(fieldName, files[i]);

        const response = await fetch(url, {
          method: 'POST',
          body: formData
        });

        const result = await response.json();
        results.push(result);

        totalProgress = ((i + 1) / totalFiles) * 100;
        if (onProgress) {
          onProgress(Math.round(totalProgress));
        }
      }

      return results;
    } finally {
      this.uploadingCount -= files.length;
      this.notifyChange();
    }
  }
}

export const uploadManager = new UploadManager();

export async function uploadImage(file, url, onProgress) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(url, {
    method: 'POST',
    body: formData
  });

  return await response.json();
}

export function createFilePreview(file) {
  if (!file || !file.type.startsWith('image/')) {
    return null;
  }

  try {
    if (typeof URL !== 'undefined' && URL.createObjectURL) {
      return URL.createObjectURL(file);
    }
  } catch (e) {
    console.error('Failed to create object URL:', e);
  }
  return null;
}

export function revokeFilePreview(url) {
  if (url && url.startsWith('blob:')) {
    try {
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error('Failed to revoke object URL:', e);
    }
  }
}