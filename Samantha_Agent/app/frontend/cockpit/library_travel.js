(function (root) {
  "use strict";

  function create({document, modal, list, readerTitle, attachmentUrl, openImage, beforeBack, onBack, add, selectCategory}) {
    const get = id => document.getElementById(id);
    const scroller = modal.querySelector(".modal");
    const tools = get("libraryReaderTools");
    const picker = get("libraryTravelCategory");
    const gallery = get("libraryTravelPhotos");
    const search = get("librarySearchInput");
    const searchLabel = search.closest("label").querySelector(".library-field-label");
    const title = get("libraryTitle");
    const saved = {title: title.textContent, placeholder: search.placeholder, label: searchLabel.textContent};
    let active = false, scroll = 0, selectedId = "";
    for (const tab of modal.querySelectorAll("[data-library-category]")) {
      const option = document.createElement("option");
      option.value = tab.dataset.libraryReadState ? "to_read" : tab.dataset.libraryCategory;
      option.textContent = tab.textContent;
      picker.appendChild(option);
    }
    const news = document.createElement("option");
    news.value = "science_news"; news.textContent = "Vědecké novinky"; picker.appendChild(news);
    picker.addEventListener("change", async () => {
      const value = picker.value;
      // Existing category loading retains the editor's discard confirmation.
      const accepted = await selectCategory(value === "to_read" || value === "science_news" ? "all" : value, value === "to_read" ? "to_read" : "");
      if (accepted && value === "science_news") get("scienceNewsLibraryBtn").click();
      picker.value = "travel_places";
    });
    modal.querySelectorAll("[data-travel-add]").forEach(button => button.addEventListener("click", () => {
      get("libraryTravelAddMenu").open = false; add(button.dataset.travelAdd);
    }));
    get("libraryTravelBack").addEventListener("click", () => {
      if (!beforeBack()) return;
      onBack(); modal.classList.remove("travel-detail", "travel-editing");
      tools.open = false;
      const row = Array.from(list.children).find(node => node.dataset.articleId === selectedId);
      if (row) row.focus({preventScroll: true});
      scroller.scrollTop = scroll;
    });

    function configure(category) {
      active = category === "travel_places";
      modal.classList.toggle("travel-mode", active);
      modal.classList.remove("travel-detail", "travel-editing");
      get("libraryTravelAddMenu").open = false;
      tools.open = !active; tools.inert = false; gallery.replaceChildren();
      if (active) get("scienceNewsSection").classList.add("hidden");
      title.textContent = active ? "Cestování / místa" : saved.title;
      search.placeholder = active ? "Hledat místo nebo poznámku" : saved.placeholder;
      searchLabel.textContent = active ? "Hledat místo" : saved.label;
      picker.value = "travel_places";
      get("libraryEditTitleInput").placeholder = active ? "Název místa" : "Název článku";
      get("libraryEditTitleInput").closest("label").querySelector(".library-field-label").textContent = active ? "Název místa" : "Název článku";
      get("libraryEditTextInput").closest("label").querySelector(".library-field-label").textContent = active ? "Poznámky k místu" : "Text článku";
      get("libraryAttachmentSectionTitle").textContent = active ? "Fotografie a dokumenty místa" : "Přílohy";
      get("libraryTextTitleInput").placeholder = active ? "Název místa" : "Název znalostní karty";
      get("libraryTextBodyInput").placeholder = active ? "Co tě zaujalo a co si chceš poznamenat" : "Vlož text receptu, poznámky nebo výstřižku";
      tools.querySelector(".library-action-group-label").textContent = active ? "Místo" : "Článek";
    }

    function card(item, open) {
      const row = document.createElement("button");
      row.type = "button"; row.className = "library-item travel-card"; row.dataset.articleId = item.id;
      const preview = item.preview_image;
      if (preview && preview.attachment_id) {
        const image = document.createElement("img");
        image.className = "travel-card-image"; image.alt = ""; image.loading = "lazy";
        image.src = attachmentUrl(item.id, preview.attachment_id, preview.variant || "thumb");
        image.addEventListener("error", () => image.remove()); row.appendChild(image);
      }
      const content = document.createElement("span"); content.className = "travel-card-content";
      const heading = document.createElement("span"); heading.className = "library-title";
      heading.textContent = item.one_line_title || item.title || "Místo bez názvu"; content.appendChild(heading);
      if (item.preview_text || item.snippet) {
        const excerpt = document.createElement("span"); excerpt.className = "travel-card-excerpt";
        excerpt.textContent = item.preview_text || item.snippet; content.appendChild(excerpt);
      }
      if (item.read_state === "to_read") {
        const badge = document.createElement("span"); badge.className = "library-read-badge";
        badge.textContent = "K přečtení"; content.appendChild(badge);
      }
      row.appendChild(content); row.addEventListener("click", open); return row;
    }

    function beginItem(id) {
      if (!active) return;
      if (!modal.classList.contains("travel-detail")) scroll = scroller.scrollTop;
      selectedId = id; modal.classList.add("travel-detail");
      modal.classList.remove("travel-editing"); tools.open = false; tools.inert = true; gallery.replaceChildren();
      scroller.scrollTop = 0;
      readerTitle.tabIndex = -1; readerTitle.focus({preventScroll: true});
    }

    function photos(articleId, attachments) {
      gallery.replaceChildren();
      if (!active) return;
      tools.inert = !articleId;
      for (const attachment of attachments || []) {
        const isImage = String(attachment.mime_type || "").startsWith("image/");
        if (!(attachment.has_readable || attachment.has_original || attachment.has_thumb)) continue;
        const variant = attachment.has_readable ? "readable" : attachment.has_original ? "original" : "thumb";
        const url = attachmentUrl(articleId, attachment.id, variant);
        const label = attachment.label && attachment.label !== "Ručně psaný recept" ? attachment.label : "Fotografie místa";
        const link = document.createElement("a"); link.href = url;
        if (isImage) {
          const image = document.createElement("img"); image.src = url; image.alt = label; image.loading = "lazy";
          image.addEventListener("error", () => link.remove()); link.appendChild(image);
          link.addEventListener("click", event => { event.preventDefault(); openImage(url, label, link); });
        } else {
          link.textContent = attachment.label || "Otevřít dokument"; link.target = "_blank"; link.rel = "noopener";
        }
        gallery.appendChild(link);
      }
    }
    return {configure, card, beginItem, photos, active: () => active,
      restoreListPosition: () => { scroller.scrollTop = scroll; },
      editing: value => modal.classList.toggle("travel-editing", Boolean(value))};
  }
  root.LibraryTravel = {create};
  if (typeof module !== "undefined" && module.exports) module.exports = root.LibraryTravel;
})(typeof window === "undefined" ? globalThis : window);
