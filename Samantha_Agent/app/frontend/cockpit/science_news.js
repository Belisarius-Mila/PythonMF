(function (root) {
  "use strict";
  const labels = {save: "Uložit zprávu", follow: "Sledovat", dismiss: "Nezařazovat"};
  function element(doc, tag, text, className) {
    const node = doc.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (className) node.className = className;
    return node;
  }
  function safeURL(value) {
    try {
      const url = new URL(value);
      return url.protocol === "https:" && !url.username && !url.password ? url.href : null;
    } catch (_) { return null; }
  }
  function create({document: doc, fetch: fetcher, storage, openWindow, elements, openLibrary, uuid}) {
    let sequence = 0, current = null;
    const working = new Set();
    async function api(path, payload) {
      const response = await fetcher(path, payload === undefined ? undefined : {
        method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (!response.ok || data.ok !== true) throw new Error(data.message || "Výsledek nelze ověřit.");
      return data;
    }
    function message(text) { elements.status.textContent = text; }
    function indicator(data) {
      const pending = data.pending_count > 0;
      elements.entry.classList.toggle("science-pending", pending);
      elements.entry.classList.toggle("science-empty", !pending);
      elements.entry.classList.remove("science-unknown");
      elements.entry.setAttribute("aria-label", pending ? `ScienceNews: ${data.pending_count} nevyřízených zpráv` : "ScienceNews: vše vyřízeno");
    }
    function operation(id, action) {
      const key = `science-news-operation:${id}`;
      const previous = storage.getItem(key);
      if (previous) {
        const record = JSON.parse(previous);
        if (record.action !== action) throw new Error("Nejprve ověř předchozí volbu této zprávy stejným tlačítkem.");
        return record.request_id;
      }
      const request_id = uuid();
      // A durable identity MUST exist before POST, also on HTTP iPhone origins.
      storage.setItem(key, JSON.stringify({action, request_id}));
      return request_id;
    }
    async function decide(item, action, buttons) {
      if (working.has(item.id)) return;
      working.add(item.id);
      buttons.forEach(button => { button.disabled = true; });
      try {
        await api("/api/science-news/decision", {item_id: item.id, action, request_id: operation(item.id, action)});
        storage.removeItem(`science-news-operation:${item.id}`);
        await refresh();
      } catch (error) {
        message(`${error.message} Zpráva zůstává k ověření; stejnou volbu můžeš ověřit znovu.`);
      } finally {
        working.delete(item.id);
        buttons.forEach(button => { button.disabled = false; });
      }
    }
    async function translate(item) {
      // Synchronous navigation preserves the iOS user gesture. Same-origin page
      // polls a read-only endpoint; it NEVER restarts the translation on reload.
      const popup = openWindow(`/science-news/translation?id=${encodeURIComponent(item.id)}`, "_blank", "noopener");
      void popup;
      try {
        await api("/api/science-news/translate", {item_id: item.id});
        message("Překlad se zobrazí v samostatném okně.");
      } catch (error) { message(error.message); }
    }
    function render(data) {
      elements.list.replaceChildren();
      for (const item of data.items) {
        const card = element(doc, "article", undefined, "science-news-card");
        card.appendChild(element(doc, "h3", item.title));
        card.appendChild(element(doc, "p", `${item.area} · ${new Date(item.published_at).toLocaleDateString("cs-CZ")}`, "project-meta"));
        card.appendChild(element(doc, "p", item.abstract_cs));
        card.appendChild(element(doc, "p", `Význam: ${item.significance_cs}`));
        card.appendChild(element(doc, "p", `Co zatím nevíme: ${item.uncertainty_cs}`));
        const source = safeURL(item.source_url);
        if (source) {
          const link = element(doc, "a", "Otevřít původní zprávu");
          link.href = source; link.target = "_blank"; link.rel = "noopener noreferrer";
          card.appendChild(link);
        }
        const actions = element(doc, "div", undefined, "science-news-actions");
        const translation = element(doc, "button", "Přeložit celou zprávu", "secondary");
        translation.type = "button";
        translation.addEventListener("click", () => translate(item));
        actions.appendChild(translation);
        const buttons = [];
        for (const [action, label] of Object.entries(labels)) {
          const button = element(doc, "button", label, action === "save" ? "primary" : "secondary");
          button.type = "button"; buttons.push(button);
          button.addEventListener("click", () => decide(item, action, buttons));
          actions.appendChild(button);
        }
        card.appendChild(actions); elements.list.appendChild(card);
      }
      elements.follows.replaceChildren();
      for (const follow of data.follows.filter(i => i.active)) {
        const row = element(doc, "div", undefined, "science-news-follow");
        row.appendChild(element(doc, "span", follow.title));
        const stop = element(doc, "button", "Přestat sledovat", "secondary");
        stop.type = "button";
        stop.addEventListener("click", async () => {
          stop.disabled = true;
          try { await api("/api/science-news/unfollow", {topic_id: follow.topic_id}); await refresh(); }
          catch (error) { message(error.message); }
          finally { stop.disabled = false; }
        });
        row.appendChild(stop); elements.follows.appendChild(row);
      }
      const last = data.issues[data.issues.length - 1];
      let text = data.pending_count ? `${data.pending_count} zpráv k vyřízení.` : "Všechny zprávy máš vyřízené.";
      if (!data.activated) text += " Automatický zpravodaj zatím není aktivovaný.";
      if (last) {
        text += ` Poslední vydání: ${new Date(last.available_at).toLocaleString("cs-CZ")}.`;
        if (last.source_health.some(i => i.state !== "ok")) text += " Některé zdroje nebyly dostupné; výběr je neúplný.";
      }
      message(text);
    }
    async function refresh() {
      const token = ++sequence;
      try {
        const data = await api("/api/science-news");
        if (token !== sequence) return;
        current = data; indicator(data); render(data);
      } catch (error) {
        if (token !== sequence) return;
        elements.entry.classList.add("science-unknown");
        elements.entry.setAttribute("aria-label", "ScienceNews: stav neověřený");
        // Keep prior cards and pulse. Failure is not an empty inbox.
        message(error.message);
      }
    }
    function show() {
      openLibrary();
      elements.section.classList.remove("hidden");
      elements.section.scrollIntoView({block: "start"});
      refresh();
    }
    elements.entry.addEventListener("click", show);
    elements.tab.addEventListener("click", show);
    return Object.freeze({refresh, show, get current() { return current; }});
  }
  root.SamanthaScienceNews = Object.freeze({create, safeURL});
  if (typeof document !== "undefined") document.addEventListener("DOMContentLoaded", () => {
    const get = id => document.getElementById(id);
    if (!get("scienceNewsBtn")) return;
    const api = create({document, fetch: window.fetch.bind(window),
      storage: {getItem: key => window.localStorage.getItem(key),
        setItem: (key, value) => window.localStorage.setItem(key, value),
        removeItem: key => window.localStorage.removeItem(key)}, openWindow: window.open.bind(window),
      uuid: () => {
        if (!window.crypto || !window.crypto.getRandomValues) throw new Error("Prohlížeč nepodporuje bezpečnou identitu požadavku.");
        return "sn_" + [...window.crypto.getRandomValues(new Uint8Array(24))].map(i => i.toString(16).padStart(2, "0")).join("");
      },
      openLibrary: () => get("libraryBtn").click(),
      elements: {entry: get("scienceNewsBtn"), tab: get("scienceNewsLibraryBtn"), section: get("scienceNewsSection"),
        status: get("scienceNewsStatus"), list: get("scienceNewsList"), follows: get("scienceNewsFollows")}});
    for (const button of document.querySelectorAll(".library-tab")) {
      button.addEventListener("click", () => get("scienceNewsSection").classList.add("hidden"));
    }
    api.refresh();
    window.setInterval(api.refresh, 60000);
    document.addEventListener("visibilitychange", () => { if (!document.hidden) api.refresh(); });
  });
})(typeof window === "undefined" ? globalThis : window);
