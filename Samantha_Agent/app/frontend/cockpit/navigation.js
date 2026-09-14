(function () {
  "use strict";

  function createDialogs({dialogs, onChange = () => {}, fallbackFocus}) {
    const entries = new Map(dialogs.map(({element, close}) => [element, {element, close, origin: null, lastFocus: null}]));
    const originalInert = new Map();
    const originalZ = new Map();
    let stack = [];
    let activation = null;
    let returningFocus = false;
    const visible = element => !!element && element.isConnected && element.getClientRects().length > 0 && !element.closest('[inert]');
    const top = () => stack[stack.length - 1];
    const focusable = element => [...element.querySelectorAll('button, a[href], input, select, textarea, iframe, [tabindex]')]
      .filter(node => node.tabIndex >= 0 && !node.disabled && visible(node));
    function focusInside(entry, preferred) {
      const heading = entry.element.querySelector('h2, h3');
      const target = preferred && entry.element.contains(preferred) && visible(preferred)
        ? preferred : heading || focusable(entry.element)[0] || entry.element;
      if (!target.hasAttribute('tabindex') && !target.matches('button, a, input, select, textarea, iframe')) target.tabIndex = -1;
      target.focus({preventScroll: true});
    }
    function sync() {
      const previous = top();
      const opened = [...entries.values()].filter(entry => !entry.element.classList.contains('hidden'));
      const added = opened.filter(entry => !stack.includes(entry));
      stack = stack.filter(entry => opened.includes(entry));
      for (const entry of added) {
        const origin = activation || document.activeElement;
        if (!entry.element.contains(origin)) {
          const parent = origin && [...entries.values()].find(item => item.element.contains(origin));
          entry.origin = parent && !opened.includes(parent) ? parent.origin || origin : origin;
        }
        stack.push(entry);
      }
      activation = null;
      // Restore our previous mask before computing the next modal layer.
      for (const [element, inert] of originalInert) element.inert = inert;
      originalInert.clear();
      for (const [element, z] of originalZ) element.style.zIndex = z;
      originalZ.clear();
      const active = top();
      stack.forEach((entry, index) => {
        originalZ.set(entry.element, entry.element.style.zIndex);
        entry.element.style.zIndex = String(20 + index * 10);
      });
      document.body.classList.toggle('cockpit-dialog-open', !!active);
      if (active) {
        if (active !== previous || !active.element.contains(document.activeElement)) focusInside(active, active.lastFocus);
        for (const element of document.body.children) {
          if (element === active.element || element.tagName === 'SCRIPT' || element.tagName === 'STYLE') continue;
          originalInert.set(element, element.inert);
          element.inert = true;
        }
      } else if (previous) {
        // An explicit handoff to e.g. document search has already placed focus.
        const current = document.activeElement;
        if (!visible(current) || current === document.body || previous.element.contains(current)) {
          const target = visible(previous.origin) ? previous.origin : fallbackFocus;
          if (target) target.focus({preventScroll: true});
        }
      }
      onChange(active && active.element);
    }
    document.addEventListener('click', event => {
      activation = event.target.closest('button, a, [role="button"], summary') || document.activeElement;
      const entry = top();
      if (entry && entry.element.contains(activation)) entry.lastFocus = activation;
      // A later programmatic opening must not inherit an unrelated old click.
      setTimeout(() => { activation = null; }, 0);
    }, true);
    document.addEventListener('focusin', event => {
      const entry = top();
      if (!entry) return;
      if (entry.element.contains(event.target)) entry.lastFocus = event.target;
      else if (!returningFocus) {
        returningFocus = true;
        focusInside(entry, entry.lastFocus);
        returningFocus = false;
      }
    });
    document.addEventListener('keydown', event => {
      const entry = top();
      if (!entry || event.isComposing || event.defaultPrevented) return;
      if (event.key === 'Escape') {
        event.preventDefault();
        event.stopPropagation();
        entry.close();
      } else if (event.key === 'Tab') {
        const nodes = focusable(entry.element);
        const first = nodes[0], last = nodes[nodes.length - 1];
        if (!nodes.length) {
          event.preventDefault();
          focusInside(entry);
        } else if (event.shiftKey && (document.activeElement === first || !nodes.includes(document.activeElement))) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && (document.activeElement === last || !entry.element.contains(document.activeElement))) {
          event.preventDefault();
          first.focus();
        }
      }
    });
    const observer = new MutationObserver(sync);
    for (const element of entries.keys()) observer.observe(element, {attributes: true, attributeFilter: ['class']});
    sync();
    return {sync, top: () => top()?.element || null};
  }

  window.SamanthaNavigation = {createDialogs};
})();
