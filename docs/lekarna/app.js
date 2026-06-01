const lockScreen = document.querySelector("#lockScreen");
const cockpit = document.querySelector("#cockpit");
const passwordForm = document.querySelector("#passwordForm");
const passwordInput = document.querySelector("#passwordInput");
const drawer = document.querySelector("#drawer");
const closeDrawer = document.querySelector("#closeDrawer");
const drawerKicker = document.querySelector("#drawerKicker");
const drawerTitle = document.querySelector("#drawerTitle");
const drawerContent = document.querySelector("#drawerContent");
const helpAudio = document.querySelector("#helpAudio");

const defaultBoxData = {
  jana: {
    title: "Pils Jana",
    kicker: "Osobní krabička",
    text: "Tady bude seznam léků z krabičky Jana. V dalším kroku ho napojíme na šifrovaný export.",
    medicines: ["Milurit", "Prestarum Neo Combi", "Atoris", "Ursosan Forte"],
  },
  mila: {
    title: "Pils Mila",
    kicker: "Osobní krabička",
    text: "Tady bude seznam léků z krabičky Mila. Zatím je to klikací prototyp.",
    medicines: ["Ukázkový lék", "Položka k ověření"],
  },
  home: {
    title: "Pils Home Store",
    kicker: "Domácí zásoba",
    text: "Tady bude společný domácí seznam léků a přípravků.",
    medicines: ["Brufen", "Panadol Novum", "ACC Long", "Fenistil gel", "Imodium"],
  },
  supplements: {
    title: "Vitamíny a přírodní přípravky",
    kicker: "Koupelna - nová dóza",
    text: "Tady budou vitamíny, minerály a přírodní přípravky na spánek, nervy a podobné potíže.",
    medicines: ["KOZLIK KNEIPP", "SILYMARIN PREMIUM", "Naturevia Ostropestrec Forte"],
  },
};

const vitaminRecommendation = {
  title: "Doporučení pro Janu a Mílu",
  kicker: "Vitamíny a doplňky",
  image: "./assets/vit-doporuceni.png?v=vitamin-recommendation-20260521",
  alt: "Doporučení pro Janu a Mílu k užívání vitamínů a doplňků.",
};

let boxData = defaultBoxData;
let medicineData = {};
let privateDataLoadPromise = null;
let unlockPassword = "";

const symptomIntents = [
  {
    label: "Bolest hlavy / horečka",
    terms: ["hlava", "bolest hlavy", "migrena", "teplota", "horecka", "zimnice", "chripka"],
    names: ["Brufen", "Panadol Novum", "Paracetamol-CT", "Acylpyrin"],
    note: "U paracetamolu pozor na duplicitu v jiných přípravcích. U ibuprofenu/ASA pozor na žaludek, ředění krve a astma.",
  },
  {
    label: "Bolest zad, kloubů, svalů nebo zubů",
    terms: ["zada", "záda", "kloub", "klouby", "sval", "svaly", "zub", "zuby", "natazeny", "podvrtnuti"],
    names: ["Brufen", "Voltaren ActiGo Extra", "Diclofenac Duo", "Diclofenac Dr. Muller Pharma gel", "Nimesil", "Novalgin"],
    note: "Část položek je na předpis nebo má výrazné kontraindikace. Detail vždy ověřit v PIL/obalu.",
  },
  {
    label: "Kašel / zahlenění",
    terms: ["kasel", "kašel", "hlen", "hleny", "zahleneni", "zahleneni", "vykaslat", "prudušky", "prudusky"],
    names: ["Tussical 1,5 mg/ml sirup", "ACC Long", "Stoptussin IVAX"],
    note: "Tussical je na suchý dráždivý kašel, ACC hlavně na hustý hlen. Varianta Stoptussinu není plně ověřená, proto ověřit obal.",
  },
  {
    label: "Rýma, nachlazení, chřipka",
    terms: ["ryma", "rýma", "nachlazeni", "nachlazení", "ucpany nos", "nos", "chripka", "chřipka"],
    names: ["Tussical 1,5 mg/ml sirup", "Xylomax Neo 1 mg/ml nosní sprej", "Paralen Grip", "Panadol Novum", "Sterimar nosni hygiena", "Visine Yxin ED"],
    note: "Tussical je pro suchý kašel, Xylomax Neo krátkodobě uvolňuje ucpaný nos. Paralen Grip má více variant, nutné ověřit konkrétní složení na obalu.",
  },
  {
    label: "Bolest v krku / dutina ústní",
    terms: ["krk", "bolest v krku", "skrabe", "škrábe", "mandle", "pusa", "dutina ustni", "aft"],
    names: ["Jasimenth C N", "Vincentka", "Lugol spray"],
    note: "U těchto položek je více nejistot, proto ověřit obal a složení.",
  },
  {
    label: "Alergie / svědění / štípnutí",
    terms: ["alergie", "svedi", "svědí", "svedeni", "svědění", "stipnuti", "štípnutí", "koprivka", "kopřivka", "vyrazka", "vyrážka"],
    names: ["Fenistil gel", "CLARINESE"],
    note: "Clarinase/Clarinese je v evidenci nejistý název; ověřit obal. Při silné reakci nebo dušnosti řešit lékaře.",
  },
  {
    label: "Průjem / trávení",
    terms: ["prujem", "průjem", "streva", "střeva", "nadymani", "nadýmání", "traveni", "trávení", "zaludek", "žaludek", "bricho", "břicho", "krece", "křeče"],
    names: ["Imodium", "Carbo medicinalis", "LIVSANE Active Carbon 250", "Biopron Forte", "Pancreolan Forte", "Febichol"],
    note: "Při krvi ve stolici, horečce, dehydrataci nebo dlouhém průjmu řešit lékaře.",
  },
  {
    label: "Zácpa / těžké vyprazdňování",
    terms: ["zacpa", "zácpa", "vyprazdnovani", "vyprazdňování", "nejde na zachod", "stolice"],
    names: [],
    note: "V domácí evidenci zatím nemám jasný lék přímo na zácpu. Při silné bolesti břicha, zvracení nebo dlouhém trvání řešit lékaře/lékárnu.",
  },
  {
    label: "Palení záhy / reflux",
    terms: ["pali zaha", "pálí žáha", "pálení žáhy", "paleni zahy", "reflux", "kyselina", "prekyseleni", "překyselení"],
    names: ["Omeprazol Teva Pharma"],
    note: "Omeprazol je vhodné ověřit podle PIL; při varovných příznacích nebo dlouhodobých potížích řešit lékaře.",
  },
  {
    label: "Modrina / otok / podlitina",
    terms: ["modrina", "modřina", "otok", "otekle", "oteklé", "podlitina", "narazil", "naražené", "narazene"],
    names: ["Hirudoid", "Heparin AL", "Diclofenac Dr. Muller Pharma gel"],
    note: "Zevní přípravky nepoužívat na otevřené rány a ověřit obal.",
  },
  {
    label: "Kůže / svědění / drobné popálení",
    terms: ["kuze", "kůže", "pokozka", "pokožka", "popaleni", "popálení", "spaleni", "spálení", "slunce", "ekzem", "ekzém"],
    names: ["Fenistil gel", "Hirudoid"],
    note: "Jen na lehké kožní potíže podle obalu. Při rozsáhlém popálení, infekci, hnisu nebo zhoršování řešit lékaře.",
  },
  {
    label: "Rána / dezinfekce",
    terms: ["rana", "rána", "riznuti", "říznutí", "odrenina", "odřenina", "dezinfekce", "krvaci", "krvácí"],
    names: [],
    note: "V evidenci zatím nemám jasnou dezinfekci nebo obvazový materiál. Při hluboké, špinavé nebo špatně se hojící ráně řešit lékaře.",
  },
  {
    label: "Cestovní nevolnost",
    terms: ["cesta", "cestovani", "cestování", "nevolnost", "zvraceni", "zvracení", "auto", "letadlo", "lod"],
    names: ["Kinedryl"],
    note: "Kinedryl může tlumit pozornost. Opatrně při řízení a alkoholu.",
  },
  {
    label: "Oči",
    terms: ["oko", "oci", "oči", "ocni", "oční", "zarudle oko", "zarudle oci", "pali oko", "pálí oko"],
    names: ["Visine Yxin ED", "Occusept ophthalmologicum"],
    note: "Při bolesti oka, poruše vidění, úrazu nebo hnisu řešit lékaře.",
  },
  {
    label: "Ucho",
    terms: ["ucho", "usi", "uši", "maz", "ucpany ucho", "ucpane ucho", "boli ucho"],
    names: ["AkuStone usni sprej"],
    note: "Při bolesti, výtoku nebo podezření na prasklý bubínek nepoužívat bez lékaře.",
  },
  {
    label: "Uklidnění / spánek",
    terms: ["spanek", "spánek", "nespavost", "nemuzu spat", "nemůžu spát", "nervozita", "uklidnit", "uklidneni"],
    names: ["KOZLIK KNEIPP"],
    note: "Bylinný/doplňkový přípravek. Může tlumit pozornost; ověřit obal a nekombinovat lehkovážně s alkoholem nebo sedativy.",
  },
  {
    label: "Tlak / srdce",
    terms: ["tlak", "vysoky tlak", "vysoký tlak", "srdce", "tep", "bušení", "buseni"],
    names: ["Prestarum Neo Combi", "Godasal / Godacal"],
    note: "Tohle jsou osobní léky nebo léky podle lékaře. Web je může jen najít v evidenci, ne doporučit k užití.",
  },
];

const urgentTerms = [
  "bolest na hrudi",
  "dusnost",
  "dušnost",
  "nemuzu dychat",
  "nemůžu dýchat",
  "mrtveni",
  "mrtvění",
  "ochrnuti",
  "ochrnutí",
  "omdleni",
  "omdlení",
  "krev ve stolici",
  "zvracim krev",
  "zvracím krev",
  "vykaslavam krev",
  "vykašlávám krev",
  "silna alergie",
  "silná alergie",
  "otok jazyka",
  "otok obliceje",
];

passwordForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!passwordInput.value.trim()) {
    passwordInput.focus();
    return;
  }
  unlockPassword = passwordInput.value;
  unlock();
  passwordInput.value = "";
});

document.querySelectorAll("[data-action]").forEach((button) => {
  button.addEventListener("click", async () => {
    const action = button.dataset.action;
    if (action === "box") {
      await ensurePharmacyDataLoaded();
      openBox(button.dataset.target);
    }
    if (action === "symptoms") {
      await ensurePharmacyDataLoaded();
      openSymptoms();
    }
    if (action === "help") {
      playHelp();
    }
  });
});

closeDrawer.addEventListener("click", () => drawer.classList.remove("is-open"));

async function unlock() {
  lockScreen.classList.add("is-hidden");
  cockpit.classList.remove("is-hidden");
  showUnlockLoading();
  const loaded = await loadPrivatePharmacyData();
  if (loaded) {
    drawer.classList.remove("is-open");
  } else if (drawerTitle.textContent === "Otevírám data") {
    showUnlockMessage("Šifrovaná data se nenašla nebo nejsou dostupná. Zobrazí se demo režim.");
  }
}

function openDrawer() {
  drawer.classList.add("is-open");
}

function resetDrawerMode() {
  drawer.classList.remove("is-detail");
  drawer.classList.remove("is-recommendation");
}

function openBox(key) {
  resetDrawerMode();
  const box = boxData[key];
  if (!box) {
    drawerKicker.textContent = "Domácí lékárna";
    drawerTitle.textContent = "Položka se připravuje";
    drawerContent.innerHTML = "<p>Tahle část lékárny ještě není v datech připravená.</p>";
    openDrawer();
    return;
  }
  drawerKicker.textContent = box.kicker;
  drawerTitle.textContent = box.title;
  drawerContent.innerHTML = `
    <p>${box.text}</p>
    ${renderBoxExtraActions(key)}
    <div class="medicine-list">
      ${box.medicines.map((name) => `<button type="button" data-medicine="${escapeHtml(name)}">${escapeHtml(name)}</button>`).join("")}
    </div>
  `;
  drawerContent.querySelectorAll("[data-panel-action]").forEach((button) => {
    button.addEventListener("click", () => {
      if (button.dataset.panelAction === "vitamin-recommendation") {
        openVitaminRecommendation();
      }
    });
  });
  drawerContent.querySelectorAll("[data-medicine]").forEach((button) => {
    button.addEventListener("click", () => openMedicine(button.dataset.medicine));
  });
  openDrawer();
}

function renderBoxExtraActions(key) {
  if (key !== "supplements") return "";
  return `
    <div class="box-action-list">
      <button type="button" data-panel-action="vitamin-recommendation">
        ${escapeHtml(vitaminRecommendation.title)}
      </button>
    </div>
  `;
}

function openVitaminRecommendation() {
  drawer.classList.add("is-detail", "is-recommendation");
  drawerKicker.textContent = vitaminRecommendation.kicker;
  drawerTitle.textContent = vitaminRecommendation.title;
  drawerContent.innerHTML = `
    <figure class="recommendation-frame">
      <img src="${escapeHtml(vitaminRecommendation.image)}" alt="${escapeHtml(vitaminRecommendation.alt)}">
    </figure>
  `;
  openDrawer();
}

function openMedicine(name) {
  const medicine = medicineData[name] || {};
  drawer.classList.add("is-detail");
  drawerKicker.textContent = "Detail léku";
  drawerTitle.textContent = name;
  drawerContent.innerHTML = `
    <div class="medicine-detail-grid">
      <section class="photo-window" aria-label="Malé foto krabičky">
        <p class="window-label">Malé foto</p>
        ${renderMedicinePhoto(name, medicine)}
      </section>

      <section class="pil-window" aria-label="PIL Short">
        <div class="pil-scroll">
          <p class="window-label">PIL_Short</p>
          <p class="pil-lead">${escapeHtml(name)}</p>
          ${renderPilShort(medicine)}
        </div>
      </section>
    </div>
  `;
  openDrawer();
}

function renderMedicinePhoto(name, medicine) {
  if (!medicine.photo) {
    return `
      <div class="medicine-photo-empty">
        <p>Fotka zatím není v evidenci.</p>
        <span>${escapeHtml(name)}</span>
      </div>
      <p class="photo-caption">Tahle položka pochází ze staršího textového seznamu bez vlastní krabičky.</p>
    `;
  }
  return `
    <figure class="medicine-photo-frame">
      <img src="${escapeHtml(medicine.photo)}" alt="Foto krabičky ${escapeHtml(name)}">
      <figcaption>${escapeHtml(name)}</figcaption>
    </figure>
    <p class="photo-caption">Fotka je načtená z lokálního bezpečného exportu.</p>
  `;
}

async function loadPrivatePharmacyData() {
  if (privateDataLoadPromise) return privateDataLoadPromise;
  privateDataLoadPromise = (async () => {
    try {
      const encryptedResult = await loadEncryptedPharmacyData();
      if (encryptedResult.found) return encryptedResult.loaded;
      try {
        const response = await fetch("./private-data/lekarna.json", { cache: "no-store" });
        if (!response.ok) return false;
        const data = await response.json();
        if (!data || !data.boxes || !data.medicines) return false;
        boxData = prepareBoxData(data.boxes, data.medicines);
        medicineData = data.medicines;
        return true;
      } catch {
        boxData = defaultBoxData;
        medicineData = {};
        return false;
      }
    } finally {
      unlockPassword = "";
    }
  })();
  return privateDataLoadPromise;
}

async function ensurePharmacyDataLoaded() {
  if (!privateDataLoadPromise) {
    showUnlockLoading();
  }
  return loadPrivatePharmacyData();
}

async function loadEncryptedPharmacyData() {
  if (!unlockPassword) return { found: false, loaded: false };
  let response;
  try {
    response = await fetch("./encrypted-data/lekarna.enc.json", { cache: "no-store" });
  } catch {
    return { found: false, loaded: false };
  }
  if (!response.ok) return { found: false, loaded: false };
  try {
    const encrypted = await response.json();
    const data = await decryptPharmacyBundle(encrypted, unlockPassword);
    if (!data || !data.boxes || !data.medicines) return { found: true, loaded: false };
    boxData = prepareBoxData(data.boxes, data.medicines);
    medicineData = data.medicines;
    return { found: true, loaded: true };
  } catch {
    boxData = defaultBoxData;
    medicineData = {};
    showUnlockMessage("Heslo neotevřelo šifrovaná data. Zkuste stránku obnovit a zadat heslo znovu.");
    return { found: true, loaded: false };
  }
}

function prepareBoxData(rawBoxes, rawMedicines) {
  const boxes = {
    ...cloneBoxData(defaultBoxData),
    ...cloneBoxData(rawBoxes || {}),
  };
  const rawSupplementNames = boxes.supplements?.medicines || [];
  boxes.supplements = {
    ...defaultBoxData.supplements,
    ...(boxes.supplements || {}),
    medicines: [],
  };

  const sourceNames = [
    ...rawSupplementNames,
    ...Object.keys(rawMedicines || {}).filter((name) => isSupplementMedicine(name, rawMedicines[name])),
  ];
  const supplementNames = [...new Set(sourceNames)];
  if (!supplementNames.length) {
    supplementNames.push(...defaultBoxData.supplements.medicines);
  }
  boxes.supplements.medicines = supplementNames;

  if (boxes.home && Array.isArray(boxes.home.medicines)) {
    const supplementSet = new Set(supplementNames);
    boxes.home = {
      ...boxes.home,
      medicines: boxes.home.medicines.filter((name) => !supplementSet.has(name)),
    };
  }

  return boxes;
}

function cloneBoxData(value) {
  return JSON.parse(JSON.stringify(value));
}

function isSupplementMedicine(name, medicine) {
  const haystack = normalize([
    name,
    medicine?.category,
    medicine?.use,
    medicine?.pilShort,
  ].filter(Boolean).join(" "));
  const exclusionHaystack = normalize([
    name,
    medicine?.category,
    medicine?.use,
  ].filter(Boolean).join(" "));
  const includeTerms = [
    "vitamin",
    "mineral",
    "spanek",
    "nerv",
    "uklid",
    "kozlik",
    "ostropestrec",
    "silymarin",
    "vigant",
    "horcik",
    "magnesium",
    "zinek",
    "melatonin",
    "medunka",
    "levandul",
    "trezalka",
  ];
  const excludeTerms = ["antibiot", "redeni krve", "specialni lecba", "tlak srdce"];
  return includeTerms.some((term) => haystack.includes(term)) && !excludeTerms.some((term) => exclusionHaystack.includes(term));
}

async function decryptPharmacyBundle(encrypted, password) {
  const salt = base64ToBytes(encrypted.salt);
  const iv = base64ToBytes(encrypted.iv);
  const ciphertext = base64ToBytes(encrypted.ciphertext);
  const passwordKey = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(password),
    "PBKDF2",
    false,
    ["deriveKey"],
  );
  const key = await crypto.subtle.deriveKey(
    {
      name: "PBKDF2",
      salt,
      iterations: encrypted.iterations,
      hash: "SHA-256",
    },
    passwordKey,
    { name: "AES-GCM", length: 256 },
    false,
    ["decrypt"],
  );
  const plaintext = await crypto.subtle.decrypt({ name: "AES-GCM", iv }, key, ciphertext);
  return JSON.parse(new TextDecoder().decode(plaintext));
}

function base64ToBytes(value) {
  const binary = atob(value);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return bytes;
}

function showUnlockMessage(message) {
  drawerKicker.textContent = "Domácí lékárna";
  drawerTitle.textContent = "Demo režim";
  drawerContent.innerHTML = `<p>${escapeHtml(message)}</p>`;
  openDrawer();
}

function showUnlockLoading() {
  drawerKicker.textContent = "Domácí lékárna";
  drawerTitle.textContent = "Otevírám data";
  drawerContent.innerHTML = "<p>Načítám a odemykám šifrovanou lékárnu...</p>";
  openDrawer();
}

function renderPilShort(medicine) {
  if (medicine.pilShort) {
    return `
      <p>${escapeHtml(medicine.pilShort)}</p>
      <p class="pil-meta">${escapeHtml(formatMedicineMeta(medicine))}</p>
      <p class="pil-warning">Domácí evidence. Ověřit obal, expiraci a příbalovou informaci. Nepoužívat jako dávkování.</p>
    `;
  }
  return `
    <p><strong>Na co lék je:</strong> sem se načte krátký, věcný výtah z příbalové informace. Popíše hlavní účel léku bez toho, aby z něj dělal osobní doporučení.</p>
    <p><strong>Způsob používání:</strong> zde bude jen obecná informace z příbalového letáku, ne dávkovací rada. Konkrétní dávkování zůstává na obalu, lékaři nebo lékárníkovi.</p>
    <p><strong>Kdy pozor:</strong> výtah připomene hlavní kontraindikace, typické interakce a situace, kdy je lepší lék nepoužít bez ověření.</p>
    <p><strong>Rizika:</strong> jen prakticky a krátce, bez zbytečného strašení. U nejistého názvu nebo varianty bude viditelně napsáno, že je potřeba ověřit obal.</p>
    <p class="pil-warning">Domácí evidence. Ověřit obal, expiraci a příbalovou informaci. Nepoužívat jako dávkování.</p>
  `;
}

function formatMedicineMeta(medicine) {
  const parts = [];
  if (medicine.pilStatus) parts.push(`Status: ${medicine.pilStatus}`);
  if (medicine.pilCheckedDate) parts.push(`Ověřeno: ${medicine.pilCheckedDate}`);
  if (medicine.mustVerify === "ano") parts.push("Ověřit obal");
  return parts.join(" | ");
}

function openSymptoms() {
  resetDrawerMode();
  drawerKicker.textContent = "Hadí otazník";
  drawerTitle.textContent = "Co vás trápí?";
  drawerContent.innerHTML = `
    <p>Zadejte jednoduše, co bolí nebo jaké máte potíže.</p>
    <form class="symptom-form" id="symptomForm">
      <input id="symptomInput" type="text" placeholder="Třeba: bolí mě hlava">
      <button type="submit">Hledat v domácí lékárně</button>
    </form>
    <div id="symptomResult" class="status-line"></div>
  `;
  const form = drawerContent.querySelector("#symptomForm");
  const input = drawerContent.querySelector("#symptomInput");
  const result = drawerContent.querySelector("#symptomResult");
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const query = normalize(input.value);
    if (!query) {
      result.textContent = "Zkuste napsat, co vás trápí.";
      return;
    }
    if (containsUrgentTerm(query)) {
      result.innerHTML = `
        <p>Tohle může být vážnější. Domácí lékárna tady není vhodný první krok.</p>
        <p>Kontaktujte lékaře, pohotovost nebo linku 155 podle závažnosti.</p>
      `;
      return;
    }
    const matches = findSymptomMatches(query);
    if (!matches.length) {
      const chatGptPrompt = buildChatGptPrompt(input.value);
      const chatGptUrl = buildChatGptUrl(chatGptPrompt);
      result.innerHTML = `
        <p>Nerozumím přesně nebo v domácí evidenci nemám jasnou shodu. Můžete zkusit vybrat oblast ručně.</p>
        <section class="chatgpt-link-panel" aria-label="Otevřít ChatGPT">
          <h3>Otevřít ChatGPT?</h3>
          <p>Na Macu může prohlížeč otevřít odkaz ve stejné záložce. Nejjistější postup je zkopírovat dotaz, otevřít ChatGPT v nové záložce ručně a dotaz vložit.</p>
          <textarea class="chatgpt-prompt-copy" readonly>${escapeHtml(chatGptPrompt)}</textarea>
          <div class="action-row">
            <button type="button" class="secondary-action" id="copyChatGptPrompt">Zkopírovat dotaz</button>
            <a class="secondary-action" href="${escapeHtml(chatGptUrl)}" target="_blank" rel="noopener noreferrer">Otevřít ChatGPT</a>
          </div>
          <p class="chatgpt-status" id="chatGptStatus">Tip na Macu: použijte Cmd+klik nebo pravé tlačítko a "Otevřít odkaz v nové záložce".</p>
        </section>
        ${renderIntentSuggestions()}
        <div class="action-row">
          <button type="button" class="secondary-action" id="closeQuestion">Zavřít</button>
        </div>
      `;
      result.querySelectorAll("[data-intent-index]").forEach((button) => {
        button.addEventListener("click", () => {
          const intent = symptomIntents[Number(button.dataset.intentIndex)];
          result.innerHTML = renderSymptomMatches([intent]);
          result.querySelectorAll("[data-medicine]").forEach((medicineButton) => {
            medicineButton.addEventListener("click", () => openMedicine(medicineButton.dataset.medicine));
          });
        });
      });
      result.querySelector("#copyChatGptPrompt").addEventListener("click", () => copyChatGptPrompt(chatGptPrompt));
      result.querySelector("#closeQuestion").addEventListener("click", () => drawer.classList.remove("is-open"));
      return;
    }
    result.innerHTML = renderSymptomMatches(matches);
    result.querySelectorAll("[data-medicine]").forEach((button) => {
      button.addEventListener("click", () => openMedicine(button.dataset.medicine));
    });
  });
  openDrawer();
  input.focus();
}

function containsUrgentTerm(query) {
  return urgentTerms.some((term) => query.includes(normalize(term)));
}

function findSymptomMatches(query) {
  const searchTerms = expandSearchTerms(query);
  const intentMatches = symptomIntents
    .map((intent) => {
      const score = intent.terms.reduce((total, term) => {
        const normalizedTerm = normalize(term);
        if (!normalizedTerm) return total;
        if (searchTerms.some((searchTerm) => searchTerm.includes(normalizedTerm))) return total + normalizedTerm.length;
        return total;
      }, 0);
      return { ...intent, score };
    })
    .filter((intent) => intent.score > 0)
    .sort((left, right) => right.score - left.score)
    .slice(0, 3);
  const intentNames = new Set(intentMatches.flatMap((intent) => intent.names));
  const directNames = findMedicineMatches(searchTerms).filter((name) => !intentNames.has(name));
  if (directNames.length) {
    intentMatches.push({
      label: "Přímá shoda v evidenci",
      terms: [],
      names: directNames,
      note: "Tyto položky odpovídají přímo názvu, kategorii, použití nebo zkrácenému PIL textu.",
      score: 1,
    });
  }
  return intentMatches;
}

function expandSearchTerms(query) {
  const terms = new Set([query]);
  const aliases = [
    ["rycma", ["ryma", "ucpany nos", "nachlazeni"]],
    ["rima", ["ryma", "ucpany nos", "nachlazeni"]],
    ["kasel", ["kasel", "suchy kasel", "drazdivy kasel", "hlen"]],
    ["nachlazeni", ["nachlazeni", "ryma", "kasel", "ucpany nos"]],
    ["chripka", ["chripka", "nachlazeni", "kasel", "ryma"]],
  ];
  aliases.forEach(([needle, values]) => {
    if (query.includes(needle)) {
      values.forEach((value) => terms.add(normalize(value)));
    }
  });
  return Array.from(terms).filter(Boolean);
}

function findMedicineMatches(searchTerms) {
  return Object.entries(medicineData)
    .map(([name, medicine]) => {
      const haystack = normalize([
        name,
        medicine?.category,
        medicine?.use,
        medicine?.form,
        medicine?.searchTags,
        medicine?.pilShort,
      ].filter(Boolean).join(" "));
      const score = searchTerms.reduce((total, term) => {
        if (!term) return total;
        if (haystack.includes(term)) return total + term.length;
        return total;
      }, 0);
      return { name, score };
    })
    .filter((item) => item.score > 0)
    .sort((left, right) => right.score - left.score || left.name.localeCompare(right.name, "cs-CZ"))
    .slice(0, 8)
    .map((item) => item.name);
}

function renderIntentSuggestions() {
  return `
    <div class="suggestion-grid">
      ${symptomIntents.map((intent, index) => `
        <button type="button" class="suggestion-chip" data-intent-index="${index}">${escapeHtml(intent.label)}</button>
      `).join("")}
    </div>
  `;
}

function renderSymptomMatches(matches) {
  return `
    <p>V domácí evidenci jsem našel tyto možné souvislosti. Není to doporučení léčby ani dávkování.</p>
    ${matches.map((match) => `
      <section class="match-card">
        <h3>${escapeHtml(match.label)}</h3>
        <p>${escapeHtml(match.note)}</p>
        ${match.names.length ? `
          <div class="medicine-list compact-list">
            ${match.names.map((name) => `<button type="button" data-medicine="${escapeHtml(name)}">${escapeHtml(name)}</button>`).join("")}
          </div>
        ` : ""}
      </section>
    `).join("")}
  `;
}

function buildChatGptPrompt(rawQuestion) {
  return [
    `Mám tento zdravotní dotaz: "${rawQuestion}".`,
    "Odpověz obecně a bezpečně. Neznáš moje diagnózy ani léky.",
    "Upozorni, kdy je vhodné kontaktovat lékaře nebo lékárníka.",
  ].join(" ");
}

function buildChatGptUrl(prompt) {
  return `https://chatgpt.com/?q=${encodeURIComponent(prompt)}`;
}

async function copyChatGptPrompt(prompt) {
  const status = document.querySelector("#chatGptStatus");
  try {
    await navigator.clipboard.writeText(prompt);
    if (status) {
      status.textContent = "Dotaz je zkopírovaný. Otevřete ChatGPT v nové záložce a vložte ho.";
    }
  } catch {
    const promptBox = document.querySelector(".chatgpt-prompt-copy");
    if (promptBox) {
      promptBox.focus();
      promptBox.select();
    }
    if (status) {
      status.textContent = "Kopírování se nepovedlo automaticky. Označte text v poli a zkopírujte ho ručně.";
    }
  }
}

async function playHelp() {
  try {
    helpAudio.currentTime = 0;
    await helpAudio.play();
  } catch {
    openPanel("Nápověda", "Kliknutím otevřete krabičky. Hadí otazník se zeptá, co vás trápí.");
  }
}

function openPanel(title, text) {
  resetDrawerMode();
  drawerKicker.textContent = "Nápověda";
  drawerTitle.textContent = title;
  drawerContent.innerHTML = `<p>${escapeHtml(text)}</p>`;
  openDrawer();
}

function normalize(value) {
  return value
    .toLocaleLowerCase("cs-CZ")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}
