(() => {
  "use strict";
  function createDocumentScanner(doc, fetcher, openProcessor) {
    const el = id => doc.getElementById(id);
    const status = el("scanStatus"), save = el("scanSave"), pagesEl = el("scanPages");
    const state = {pages: [], pdf: null, pdfUrl: "", id: "", busy: false, committed: false};
    function identifier() {
      const bytes = new Uint8Array(16);
      crypto.getRandomValues(bytes);
      return Array.from(bytes, b => b.toString(16).padStart(2, "0")).join("");
    }
    function render() {
      pagesEl.replaceChildren();
      state.pages.forEach((page, index) => {
        const li = doc.createElement("li"), img = doc.createElement("img");
        img.src = page.url; img.alt = `Strana ${index + 1}`; li.append(img);
        const label = doc.createElement("p"); label.textContent = `Strana ${index + 1}`; li.append(label);
        [["Nahoru", -1], ["Dolů", 1], ["Odebrat", 0]].forEach(([text, step]) => {
          const button = doc.createElement("button"); button.type = "button"; button.textContent = text;
          button.disabled = state.busy || state.committed || (step !== 0 && (index + step < 0 || index + step >= state.pages.length));
          button.onclick = () => {
            if (step === 0) URL.revokeObjectURL(state.pages.splice(index, 1)[0].url);
            else [state.pages[index], state.pages[index + step]] = [state.pages[index + step], state.pages[index]];
            render();
          };
          li.append(button);
        });
        pagesEl.append(li);
      });
      ["scanCamera", "scanFiles", "scanPdf", "scanReset", "scanTitle"].forEach(id => {
        el(id).disabled = state.busy || (state.committed && id !== "scanReset");
      });
      save.disabled = state.busy || state.committed || (!state.pdf && !state.pages.length);
      el("scanPdfPreview").hidden = !state.pdf;
      el("scanPdfFullPreview").hidden = !state.pdf;
      el("scanPdfFullPreview").href = state.pdfUrl;
      if (state.pdfUrl) el("scanPdfPreview").src = state.pdfUrl;
    }
    function reset() {
      state.pages.forEach(page => URL.revokeObjectURL(page.url));
      if (state.pdfUrl) URL.revokeObjectURL(state.pdfUrl);
      Object.assign(state, {pages: [], pdf: null, pdfUrl: "", id: identifier(), committed: false});
      el("scanPdfPreview").removeAttribute("src"); el("scanTitle").value = "";
      status.textContent = "Přidej stránky nebo naskenované PDF."; render();
    }
    async function photo(file) {
      const url = URL.createObjectURL(file), img = new Image();
      try {
        await new Promise((resolve, reject) => {img.onload = resolve; img.onerror = reject; img.src = url;});
        const scale = Math.min(1, 1800 / Math.max(img.naturalWidth, img.naturalHeight));
        const canvas = doc.createElement("canvas");
        canvas.width = Math.round(img.naturalWidth * scale); canvas.height = Math.round(img.naturalHeight * scale);
        canvas.getContext("2d").drawImage(img, 0, 0, canvas.width, canvas.height);
        const data = canvas.toDataURL("image/jpeg", 0.9);
        const bytes = Uint8Array.from(atob(data.split(",")[1]), character => character.charCodeAt(0));
        const blob = new Blob([bytes], {type: "image/jpeg"});
        return {data: data.split(",")[1], url: URL.createObjectURL(blob)};
      } finally {URL.revokeObjectURL(url);}
    }
    async function addPhotos(files) {
      if (!files.length) return;
      if (state.pdf || state.pages.length + files.length > 30) {
        status.textContent = "Pro další dokument vyber Nový sken. Jeden sken může mít až 30 stran."; return;
      }
      state.busy = true; render();
      try {
        for (const file of files) state.pages.push(await photo(file));
        status.textContent = `Připraveno ${state.pages.length} stran. Zkontroluj čitelnost a pořadí.`;
      } catch (_) {status.textContent = "Fotografii se nepodařilo načíst. Zkus ji přidat znovu.";}
      finally {state.busy = false; render();}
    }
    async function saved() {
      const response = await fetcher("/api/documents/scans"), data = await response.json();
      if (!response.ok || !data.ok) throw new Error(data.message || "Seznam skenů není dostupný.");
      el("scanSaved").replaceChildren();
      data.items.forEach(item => {
        const row = doc.createElement("div"), title = doc.createElement("p");
        title.textContent = `${item.title} · ${item.pages} stran`; row.append(title);
        const link = doc.createElement("a");
        link.textContent = "Otevřít PDF"; link.href = `/api/documents/scans/pdf?scan_id=${encodeURIComponent(item.scan_id)}`;
        link.target = "_blank"; link.rel = "noopener"; row.append(link);
        const button = doc.createElement("button");
        button.type = "button"; button.textContent = "Zpracovat ve ScanDocu";
        button.onclick = () => openProcessor(item.scan_id, button); row.append(button);
        el("scanSaved").append(row);
      });
    }
    el("documentScanBtn").onclick = () => {
      el("documentScanner").open = true;
      el("documentScanner").scrollIntoView({block: "start", behavior: "smooth"});
      saved().catch(err => {status.textContent = err.message;});
    };
    [["scanCamera", "scanCameraInput"], ["scanFiles", "scanFilesInput"], ["scanPdf", "scanPdfInput"]].forEach(([button, input]) => {
      el(button).onclick = () => el(input).click();
    });
    ["scanCameraInput", "scanFilesInput"].forEach(id => {
      el(id).onchange = async event => {await addPhotos(Array.from(event.target.files)); event.target.value = "";};
    });
    el("scanPdfInput").onchange = event => {
      const file = event.target.files[0]; event.target.value = "";
      if (!file) return;
      if (state.pages.length || state.pdf) {status.textContent = "Nejdřív vyber Nový sken."; return;}
      if (file.size > 24 * 1024 * 1024) {status.textContent = "PDF musí mít nejvýše 24 MB."; return;}
      state.pdf = file; state.pdfUrl = URL.createObjectURL(file);
      if (!el("scanTitle").value) el("scanTitle").value = file.name.replace(/\.pdf$/i, "").slice(0, 160);
      status.textContent = "Zkontroluj všechny stránky PDF a potvrď uložení."; render();
    };
    save.onclick = async () => {
      const title = el("scanTitle").value.trim();
      if (!title) {status.textContent = "Doplň název dokumentu."; el("scanTitle").focus(); return;}
      state.busy = true; render(); status.textContent = "Ukládám dokument…";
      try {
        let response;
        if (state.pdf) {
          const params = new URLSearchParams({scan_id: state.id, title});
          response = await fetcher(`/api/documents/scans/pdf?${params}`, {
            method: "POST", headers: {"Content-Type": "application/pdf", "X-Confirm-Save": "yes"}, body: state.pdf});
        } else {
          const body = JSON.stringify({scan_id: state.id, title, pages: state.pages.map(p => p.data), confirmed: true});
          if (new Blob([body]).size > 9 * 1024 * 1024) throw new Error("Fotografie jsou příliš velké. Rozděl dokument nebo vyber menší fotografie.");
          response = await fetcher("/api/documents/scans", {method: "POST", headers: {"Content-Type": "application/json"}, body});
        }
        const data = await response.json();
        if (!response.ok || !data.ok) throw new Error(data.message || "Uložení není potvrzené.");
        state.committed = true;
        status.textContent = `Uloženo · ${data.scan.pages} stran. Dokument můžeš zpracovat ve ScanDocu.`;
        try {await saved();} catch (_) {status.textContent += " Seznam obnovíš tlačítkem Naskenovat dokument.";}
      } catch (err) {
        status.textContent = `${err.message} Zkus uložit znovu se stejným názvem. Ověřený přenos nevytvoří další kopii.`;
      } finally {state.busy = false; render();}
    };
    el("scanReset").onclick = reset;
    reset();
    return {state, reset, saved};
  }
  globalThis.createDocumentScanner = createDocumentScanner;
})();
