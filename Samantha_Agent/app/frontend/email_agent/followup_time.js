(() => {
  "use strict";
  const formatter = new Intl.DateTimeFormat("en-CA", {timeZone: "Europe/Prague",
    year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23"});
  function toInput(instant) {
    const date = new Date(instant);
    if (!Number.isFinite(date.getTime())) throw new Error("Neplatný čas kontroly.");
    const p = Object.fromEntries(formatter.formatToParts(date).map(x => [x.type, x.value]));
    return `${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}`;
  }
  function fromInput(value) {
    if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(value)) throw new Error("Doplň den a čas kontroly.");
    const [year, month, day, hour, minute] = value.match(/\d+/g).map(Number);
    if (year < 2000 || month < 1 || month > 12 || day < 1 || hour > 23 || minute > 59)
      throw new Error("Neplatný den nebo čas kontroly.");
    const local = Date.UTC(year, month - 1, day, hour, minute);
    // Modern Prague uses CET/CEST. Verify each candidate against the actual zone;
    // reject a spring gap or autumn ambiguity rather than silently moving time.
    const matches = [60, 120].map(offset => new Date(local - offset * 60000))
      .filter(date => toInput(date) === value);
    if (matches.length !== 1) throw new Error("Tento čas je neplatný nebo nejednoznačný kvůli změně času. Zvol jinou hodinu.");
    return matches[0].toISOString();
  }
  window.SamanthaFollowupTime = {toInput, fromInput};
})();
