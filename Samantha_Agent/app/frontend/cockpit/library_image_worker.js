"use strict";

// A fixed same-origin worker keeps decoding and resizing off the form's UI thread.
self.onmessage = async ({data: file}) => {
  let bitmap;
  try {
    if (typeof createImageBitmap !== "function" || typeof OffscreenCanvas !== "function") {
      self.postMessage({fallback: true});
      return;
    }
    bitmap = await createImageBitmap(file, {imageOrientation: "from-image"});
    if (bitmap.width * bitmap.height > 64000000) {
      self.postMessage({error: "Fotografie má více než 64 milionů bodů. Vyber menší rozlišení."});
      return;
    }
    const scale = Math.min(1, 2400 / Math.max(bitmap.width, bitmap.height));
    let width = Math.max(1, Math.round(bitmap.width * scale));
    let height = Math.max(1, Math.round(bitmap.height * scale));
    for (let attempt = 0; attempt < 12; attempt += 1) {
      const canvas = new OffscreenCanvas(width, height);
      const context = canvas.getContext("2d", {alpha: false});
      context.fillStyle = "white";
      context.fillRect(0, 0, width, height);
      context.drawImage(bitmap, 0, 0, width, height);
      for (const quality of [.90, .84, .78, .72]) {
        const blob = await canvas.convertToBlob({type: "image/jpeg", quality});
        if (blob.size <= 1024 * 1024) {
          self.postMessage({blob});
          return;
        }
      }
      width = Math.max(1, Math.round(width * .8));
      height = Math.max(1, Math.round(height * .8));
    }
    self.postMessage({error: "Fotografii se nepodařilo zmenšit na 1 MiB."});
  } catch (_error) {
    // HEIC and browser-specific decoders use the existing Mac/Pillow capability.
    self.postMessage({fallback: true});
  } finally {
    if (bitmap) bitmap.close();
  }
};
