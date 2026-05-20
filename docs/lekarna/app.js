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

const boxData = {
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
};

const medicinePhotos = {
  sample: {
    src: "./assets/meds/sample-hirudoid.jpeg",
    alt: "Ukázkové foto krabičky léku",
  },
};

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
    names: ["ACC Long", "Stoptussin IVAX"],
    note: "ACC je hlavně na hustý hlen. Varianta Stoptussinu není plně ověřená, proto ověřit obal.",
  },
  {
    label: "Rýma, nachlazení, chřipka",
    terms: ["ryma", "rýma", "nachlazeni", "nachlazení", "ucpany nos", "nos", "chripka", "chřipka"],
    names: ["Paralen Grip", "Panadol Novum", "Sterimar nosni hygiena", "Visine Yxin ED"],
    note: "Paralen Grip má více variant, nutné ověřit konkrétní složení na obalu.",
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

if (sessionStorage.getItem("lekarnaUnlocked") === "1") {
  unlock();
}

passwordForm.addEventListener("submit", (event) => {
  event.preventDefault();
  if (!passwordInput.value.trim()) {
    passwordInput.focus();
    return;
  }
  sessionStorage.setItem("lekarnaUnlocked", "1");
  unlock();
});

document.querySelectorAll("[data-action]").forEach((button) => {
  button.addEventListener("click", () => {
    const action = button.dataset.action;
    if (action === "box") {
      openBox(button.dataset.target);
    }
    if (action === "symptoms") {
      openSymptoms();
    }
    if (action === "help") {
      playHelp();
    }
  });
});

closeDrawer.addEventListener("click", () => drawer.classList.remove("is-open"));

function unlock() {
  lockScreen.classList.add("is-hidden");
  cockpit.classList.remove("is-hidden");
}

function openDrawer() {
  drawer.classList.add("is-open");
}

function resetDrawerMode() {
  drawer.classList.remove("is-detail");
}

function openBox(key) {
  resetDrawerMode();
  const box = boxData[key];
  drawerKicker.textContent = box.kicker;
  drawerTitle.textContent = box.title;
  drawerContent.innerHTML = `
    <p>${box.text}</p>
    <div class="medicine-list">
      ${box.medicines.map((name) => `<button type="button" data-medicine="${escapeHtml(name)}">${escapeHtml(name)}</button>`).join("")}
    </div>
  `;
  drawerContent.querySelectorAll("[data-medicine]").forEach((button) => {
    button.addEventListener("click", () => openMedicine(button.dataset.medicine));
  });
  openDrawer();
}

function openMedicine(name) {
  const photo = medicinePhotos[name] || medicinePhotos.sample;
  drawer.classList.add("is-detail");
  drawerKicker.textContent = "Detail léku";
  drawerTitle.textContent = name;
  drawerContent.innerHTML = `
    <div class="medicine-detail-grid">
      <section class="photo-window" aria-label="Malé foto krabičky">
        <p class="window-label">Malé foto</p>
        <figure class="medicine-photo-frame">
          <img src="${escapeHtml(photo.src)}" alt="${escapeHtml(photo.alt)}">
          <figcaption>${escapeHtml(name)}</figcaption>
        </figure>
        <p class="photo-caption">Zatím ukázková fotka pro test rozvržení. Později se načte správná fotka z bezpečného exportu.</p>
      </section>

      <section class="pil-window" aria-label="PIL Short">
        <div class="pil-scroll">
          <p class="window-label">PIL_Short</p>
          <p class="pil-lead">${escapeHtml(name)}</p>
          <p><strong>Na co lék je:</strong> sem se načte krátký, věcný výtah z příbalové informace. Popíše hlavní účel léku bez toho, aby z něj dělal osobní doporučení.</p>
          <p><strong>Způsob používání:</strong> zde bude jen obecná informace z příbalového letáku, ne dávkovací rada. Konkrétní dávkování zůstává na obalu, lékaři nebo lékárníkovi.</p>
          <p><strong>Kdy pozor:</strong> výtah připomene hlavní kontraindikace, typické interakce a situace, kdy je lepší lék nepoužít bez ověření.</p>
          <p><strong>Rizika:</strong> jen prakticky a krátce, bez zbytečného strašení. U nejistého názvu nebo varianty bude viditelně napsáno, že je potřeba ověřit obal.</p>
          <p class="pil-warning">Domácí evidence. Ověřit obal, expiraci a příbalovou informaci. Nepoužívat jako dávkování.</p>
        </div>
      </section>
    </div>
  `;
  openDrawer();
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
      result.innerHTML = `
        <p>Nerozumím přesně nebo v domácí evidenci nemám jasnou shodu. Můžete zkusit vybrat oblast ručně.</p>
        <p>ChatGPT se otevře v nové záložce. Tato lékárna zůstane otevřená v původní záložce.</p>
        ${renderIntentSuggestions()}
        <div class="action-row">
          <button type="button" class="secondary-action" id="openChatGpt">Otevřít ChatGPT v nové záložce</button>
          <button type="button" class="secondary-action" id="closeQuestion">Zavřít</button>
        </div>
        <p class="chatgpt-status" id="chatGptStatus"></p>
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
      result.querySelector("#openChatGpt").addEventListener("click", () => openChatGpt(input.value));
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
  return symptomIntents
    .map((intent) => {
      const score = intent.terms.reduce((total, term) => {
        const normalizedTerm = normalize(term);
        if (!normalizedTerm) return total;
        if (query.includes(normalizedTerm)) return total + normalizedTerm.length;
        return total;
      }, 0);
      return { ...intent, score };
    })
    .filter((intent) => intent.score > 0)
    .sort((left, right) => right.score - left.score)
    .slice(0, 3);
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

function openChatGpt(rawQuestion) {
  const prompt = [
    `Mám tento zdravotní dotaz: "${rawQuestion}".`,
    "Odpověz obecně a bezpečně. Neznáš moje diagnózy ani léky.",
    "Upozorni, kdy je vhodné kontaktovat lékaře nebo lékárníka.",
  ].join(" ");
  const url = `https://chatgpt.com/?q=${encodeURIComponent(prompt)}`;
  const opened = window.open(url, "_blank");
  if (opened) {
    opened.opener = null;
  }
  const status = document.querySelector("#chatGptStatus");
  if (status) {
    status.textContent = opened
      ? "ChatGPT se otevřel v nové záložce nebo okně. Lékárna zůstává v původní záložce."
      : "Prohlížeč nové okno zablokoval. Povolte vyskakovací okno nebo otevřete ChatGPT ručně.";
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
