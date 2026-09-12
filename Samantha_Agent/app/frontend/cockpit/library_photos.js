"use strict";

const LibraryPhotos = (() => {
  const MAX_INPUT = 32 * 1024 * 1024;
  const MAX_OUTPUT = 1024 * 1024;
  const cache = new WeakMap();
  let preparationTail = Promise.resolve();

  function validate(file) {
    if (!file || !file.size) throw new Error("Vyber neprázdnou fotografii.");
    if (file.size > MAX_INPUT) throw new Error("Fotografie je větší než 32 MiB. Vyber menší rozlišení.");
    if (!/^image\/(jpeg|png|webp|heic|heif)$/i.test(file.type || "") && !/\.(jpe?g|png|webp|heic|heif)$/i.test(file.name || "")) {
      throw new Error("Podporované fotografie jsou JPG, PNG, WEBP a HEIC/HEIF.");
    }
  }

  function inWorker(file) {
    return new Promise((resolve) => {
      let worker;
      let timer;
      const finish = (result) => {
        clearTimeout(timer);
        if (worker) worker.terminate();
        resolve(result);
      };
      try {
        worker = new Worker("/api/library/image-worker.js");
        worker.onmessage = (event) => finish(event.data);
        worker.onerror = () => finish({fallback: true});
        timer = setTimeout(() => finish({fallback: true}), 45000);
        worker.postMessage(file);
      } catch (_error) {
        finish({fallback: true});
      }
    });
  }

  function prepare(file) {
    if (cache.has(file)) return cache.get(file);
    const job = preparationTail.then(async () => {
      validate(file);
      const result = await inWorker(file);
      if (result.error) throw new Error(result.error);
      let blob = result.blob;
      if (result.fallback) {
        const response = await fetch("/api/library/image-prepare", {
          method: "POST", headers: {"Content-Type": file.type || "application/octet-stream"}, body: file,
        });
        if (!response.ok || !String(response.headers.get("Content-Type")).startsWith("image/jpeg")) {
          const data = await response.json().catch(() => ({}));
          throw new Error(data.message || "Fotografii se nepodařilo připravit na Macu.");
        }
        blob = await response.blob();
      }
      if (!blob || blob.type !== "image/jpeg" || !blob.size || blob.size > MAX_OUTPUT) {
        throw new Error("Připravená fotografie nesplňuje limit 1 MiB.");
      }
      return {blob, filename: (file.name || "fotografie").replace(/\.[^.]*$/, "") + ".jpg"};
    });
    preparationTail = job.catch(() => {});
    cache.set(file, job);
    job.catch(() => cache.delete(file));
    return job;
  }

  function requestId() {
    const bytes = new Uint8Array(16);
    crypto.getRandomValues(bytes);
    return Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
  }

  class Queue {
    constructor({preparePhoto = prepare, upload, changed = () => {}, attached = () => {}}) {
      this.tasks = [];
      this.preparePhoto = preparePhoto;
      this.upload = upload;
      this.changed = changed;
      this.attached = attached;
      this.uploadTail = Promise.resolve();
    }
    add(file, group, hint = null) {
      const task = {id: requestId(), file, name: file.name || "Fotografie", group, hint, target: null, state: "preparing", prepared: null, preview: "", error: "", sending: false};
      this.tasks.push(task);
      this.startPreparation(task);
      return task;
    }
    pending(group) {
      return this.tasks.filter((task) => task.group === group && !task.target && task.state !== "removed");
    }
    startPreparation(task) {
      task.state = "preparing";
      task.error = "";
      this.changed();
      task.preparation = this.preparePhoto(task.file).then((prepared) => {
        if (task.state === "removed") return;
        task.prepared = prepared;
        task.preview = URL.createObjectURL(prepared.blob);
        task.state = "ready";
        this.changed();
        if (task.target) this.send(task);
      }).catch((error) => {
        if (task.state === "removed") return;
        task.state = "error";
        task.error = error.message || "Příprava fotografie selhala.";
        this.changed();
      });
    }
    bind(tasks, target) {
      if (!target || !target.id) throw new Error("Chybí karta pro připojení fotografií.");
      for (const task of tasks) {
        if (task.target || task.state === "removed") continue;
        task.target = Object.freeze({...target});
        if (task.state === "ready") this.send(task);
      }
      this.changed();
    }
    send(task) {
      if (task.sending || !task.target || !task.prepared || task.state === "attached" || task.state === "removed") return;
      task.sending = true;
      task.state = "queued";
      this.changed();
      this.uploadTail = this.uploadTail.then(async () => {
        if (task.state === "removed") return;
        task.state = "uploading";
        this.changed();
        try {
          const result = await this.upload(task);
          if (!result || !result.ok) throw new Error(result && result.message || "Připojení fotografie selhalo.");
          task.state = "attached";
          task.file = null;
          task.prepared = null;
          task.preparation = null;
          // A view refresh failure must never turn an acknowledged save into a retry.
          try { this.attached(result, task.target); } catch (_error) { /* Refresh on next card open. */ }
        } catch (error) {
          task.state = "error";
          task.error = error.message || "Přenos selhal. Můžeš zopakovat jen tuto fotografii.";
        } finally {
          task.sending = false;
          this.changed();
        }
      });
    }
    retry(task) {
      if (task.state !== "error") return;
      task.error = "";
      if (task.prepared) {
        task.state = "ready";
        if (task.target) this.send(task);
        else this.changed();
      } else this.startPreparation(task);
    }
    remove(task) {
      if (task.sending) return;
      task.state = "removed";
      task.file = null;
      task.prepared = null;
      task.preparation = null;
      if (task.preview) URL.revokeObjectURL(task.preview);
      this.tasks = this.tasks.filter((entry) => entry !== task);
      this.changed();
    }
    unfinished() {
      return this.tasks.some((task) => !["attached", "removed"].includes(task.state));
    }
  }
  return {prepare, validate, Queue, MAX_INPUT, MAX_OUTPUT};
})();
