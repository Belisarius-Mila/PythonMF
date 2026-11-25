(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const canvas = $("canvas"),
    ctx = canvas.getContext("2d");
  const original = new Image(),
    result = new Image();
  const cacheKey = "samantha-interior-mask-pilot-v1";
  const colors = {
    PIXEL_LOCK: "#bd4435",
    CONTEXT_ONLY: "#666",
    GEOMETRY_LOCK: "#b77920",
    EDITABLE: "#248457",
    FREE_DESIGN: "#3874c0",
  };
  let layers = [],
    selected = "",
    revision = 0,
    baseHash = "",
    variants = [];
  let undo = [],
    redo = [],
    stroke = null,
    polygon = [];
  let scale = 1,
    offset = [0, 0],
    dirty = false,
    busy = false,
    pending = null;
  const pointers = new Map();
  let gesture = null;
  function status(text) {
    $("status").textContent = text;
  }
  function current() {
    return layers.find((layer) => layer.id === selected);
  }
  function cache() {
    try {
      localStorage.setItem(
        cacheKey,
        JSON.stringify({
          layers,
          selected,
          revision,
          baseHash,
          dirty,
          pending,
        }),
      );
    } catch (_) {
      status("Úložiště prohlížeče je plné. Ulož práci na server.");
    }
  }
  function snapshot() {
    undo.push(JSON.stringify(layers));
    if (undo.length > 100) undo.shift();
    redo = [];
  }
  function changed() {
    dirty = true;
    cache();
    status("Rozepsáno v tomto zařízení.");
    refreshLayers();
    draw();
  }
  function refreshLayers() {
    $("layers").replaceChildren(
      ...layers.map((layer) => {
        const option = document.createElement("option");
        option.value = layer.id;
        option.textContent = layer.name;
        option.selected = layer.id === selected;
        return option;
      }),
    );
    if (pending) {
      document
        .querySelectorAll(
          ".toolbar button,.toolbar input,.toolbar select,aside input,aside select,#add,#reload,#copy",
        )
        .forEach((el) => (el.disabled = true));
    }
    const layer = current();
    for (const id of ["name", "mode", "visible"])
      $(id).disabled = !layer || busy || !!pending;
    if (layer) {
      $("name").value = layer.name;
      $("mode").value = layer.mode;
      $("visible").checked = layer.visible;
    }
    $("undo").disabled = busy || !!pending || !undo.length;
    $("redo").disabled = busy || !!pending || !redo.length;
  }
  function fit() {
    scale = Math.min(canvas.width / 1000, canvas.height / 650);
    offset = [
      (canvas.width - 1000 * scale) / 2,
      (canvas.height - 650 * scale) / 2,
    ];
    draw();
  }
  function resize() {
    const box = $("viewport").getBoundingClientRect();
    canvas.width = Math.round(box.width);
    canvas.height = Math.round(box.height);
    fit();
  }
  function localPoint(event) {
    const b = canvas.getBoundingClientRect();
    return [event.clientX - b.left, event.clientY - b.top];
  }
  function nativePoint(event) {
    const p = localPoint(event);
    return [
      Math.max(0, Math.min(999, (p[0] - offset[0]) / scale)),
      Math.max(0, Math.min(649, (p[1] - offset[1]) / scale)),
    ];
  }
  function path(context, item) {
    const pts = item.points;
    context.beginPath();
    if (item.tool === "rect") {
      context.rect(
        pts[0][0],
        pts[0][1],
        pts[1][0] - pts[0][0],
        pts[1][1] - pts[0][1],
      );
    } else {
      context.moveTo(...pts[0]);
      pts.slice(1).forEach((point) => context.lineTo(...point));
      if (item.tool === "polygon") context.closePath();
    }
    context.lineWidth = item.width;
    context.lineCap = "round";
    context.lineJoin = "round";
    if (item.tool === "brush") {
      context.stroke();
      const p = pts[0];
      context.beginPath();
      context.arc(p[0], p[1], item.width / 2, 0, Math.PI * 2);
      context.fill();
    } else context.fill();
  }
  function layerOverlay(layer) {
    const surface = document.createElement("canvas");
    surface.width = 1000;
    surface.height = 650;
    const paint = surface.getContext("2d");
    paint.fillStyle = colors[layer.mode];
    paint.strokeStyle = colors[layer.mode];
    for (const item of layer.strokes) {
      paint.globalCompositeOperation = item.erase
        ? "destination-out"
        : "source-over";
      path(paint, item);
    }
    if (stroke && layer.id === selected) {
      paint.globalCompositeOperation = stroke.erase
        ? "destination-out"
        : "source-over";
      path(paint, stroke);
    }
    ctx.globalAlpha = 0.35;
    ctx.drawImage(surface, 0, 0);
    ctx.globalAlpha = 1;
  }
  function draw() {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (!original.complete || !original.naturalWidth) return;
    ctx.save();
    ctx.translate(...offset);
    ctx.scale(scale, scale);
    ctx.drawImage(original, 0, 0);
    const view = $("view").value,
      ready = result.complete && result.naturalWidth;
    if (ready && view === "after") ctx.drawImage(result, 0, 0);
    if (ready && view === "diff") {
      ctx.globalCompositeOperation = "difference";
      ctx.drawImage(result, 0, 0);
      ctx.globalCompositeOperation = "source-over";
    }
    if (ready && view === "compare") {
      const x = 1000 * (1 - Number($("split").value) / 100);
      ctx.save();
      ctx.beginPath();
      ctx.rect(x, 0, 1000 - x, 650);
      ctx.clip();
      ctx.drawImage(result, 0, 0);
      ctx.restore();
      ctx.strokeStyle = "white";
      ctx.lineWidth = 3 / scale;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, 650);
      ctx.stroke();
    }
    if (view === "edit") {
      layers.filter((layer) => layer.visible).forEach(layerOverlay);
      if (polygon.length) {
        ctx.strokeStyle = colors[current()?.mode] || "#222";
        ctx.lineWidth = 2 / scale;
        ctx.beginPath();
        ctx.moveTo(...polygon[0]);
        polygon.slice(1).forEach((p) => ctx.lineTo(...p));
        ctx.stroke();
        for (const p of polygon) {
          ctx.beginPath();
          ctx.arc(...p, 4 / scale, 0, Math.PI * 2);
          ctx.fill();
        }
      }
    }
    ctx.restore();
  }
  function finishStroke() {
    if (!stroke || !current()) return;
    snapshot();
    current().strokes.push(stroke);
    stroke = null;
    changed();
  }
  canvas.addEventListener("pointerdown", (event) => {
    if (busy || pending) return;
    event.preventDefault();
    try {
      canvas.setPointerCapture(event.pointerId);
    } catch (_) {
      /* Synthetic pointer or cancelled contact. */
    }
    pointers.set(event.pointerId, localPoint(event));
    if (pointers.size === 2) {
      stroke = null;
      const [a, b] = [...pointers.values()];
      gesture = {
        distance: Math.hypot(a[0] - b[0], a[1] - b[1]),
        center: [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2],
        scale,
        offset: [...offset],
      };
      draw();
      return;
    }
    if ($("tool").value === "pan") {
      gesture = { start: localPoint(event), offset: [...offset] };
      return;
    }
    if (!current() || $("view").value !== "edit") return;
    const p = nativePoint(event),
      tool = $("tool").value;
    if (tool === "polygon") {
      polygon.push(p);
      draw();
      return;
    }
    stroke = {
      tool: tool === "erase" ? "brush" : tool,
      erase: tool === "erase",
      width: Number($("width").value),
      points: tool === "rect" ? [p, p] : [p],
    };
  });
  canvas.addEventListener("pointermove", (event) => {
    if (!pointers.has(event.pointerId)) return;
    pointers.set(event.pointerId, localPoint(event));
    if (gesture && pointers.size === 2 && gesture.distance) {
      const [a, b] = [...pointers.values()],
        center = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
      scale = Math.max(
        0.1,
        Math.min(
          8,
          (gesture.scale * Math.hypot(a[0] - b[0], a[1] - b[1])) /
            Math.max(1, gesture.distance),
        ),
      );
      offset = center.map(
        (v, i) =>
          v - ((gesture.center[i] - gesture.offset[i]) * scale) / gesture.scale,
      );
    } else if (gesture?.start) {
      const p = localPoint(event);
      offset = p.map((v, i) => gesture.offset[i] + v - gesture.start[i]);
    } else if (stroke) {
      const p = nativePoint(event);
      if (stroke.tool === "rect") stroke.points[1] = p;
      else if (stroke.points.length < 5000) stroke.points.push(p);
    }
    draw();
  });
  function pointerEnd(event) {
    pointers.delete(event.pointerId);
    if (!gesture) finishStroke();
    if (!pointers.size) gesture = null;
  }
  canvas.addEventListener("pointerup", pointerEnd);
  canvas.addEventListener("pointercancel", () => {
    stroke = null;
    gesture = null;
    pointers.clear();
    draw();
  });
  $("finishPolygon").onclick = () => {
    if (polygon.length < 3 || !current()) return;
    snapshot();
    current().strokes.push({
      tool: "polygon",
      erase: false,
      width: 1,
      points: polygon,
    });
    polygon = [];
    changed();
  };
  $("add").onclick = () => {
    snapshot();
    const id = crypto.randomUUID();
    layers.push({
      id,
      name: "Oblast " + (layers.length + 1),
      mode: "PIXEL_LOCK",
      visible: true,
      strokes: [],
    });
    selected = id;
    polygon = [];
    changed();
  };
  $("layers").onchange = () => {
    selected = $("layers").value;
    polygon = [];
    cache();
    refreshLayers();
    draw();
  };
  for (const id of ["name", "mode", "visible"])
    $(id).onchange = () => {
      if (!current()) return;
      snapshot();
      current()[id === "name" ? "name" : id === "mode" ? "mode" : "visible"] =
        id === "visible" ? $(id).checked : $(id).value;
      changed();
    };
  $("undo").onclick = () => {
    if (!undo.length) return;
    redo.push(JSON.stringify(layers));
    layers = JSON.parse(undo.pop());
    selected = layers.some((l) => l.id === selected) ? selected : layers[0]?.id;
    changed();
  };
  $("redo").onclick = () => {
    if (!redo.length) return;
    undo.push(JSON.stringify(layers));
    layers = JSON.parse(redo.pop());
    selected = layers.some((l) => l.id === selected) ? selected : layers[0]?.id;
    dirty = true;
    cache();
    refreshLayers();
    draw();
  };
  function zoom(factor) {
    const old = scale;
    scale = Math.max(0.1, Math.min(8, scale * factor));
    offset = [
      canvas.width / 2 - ((canvas.width / 2 - offset[0]) * scale) / old,
      canvas.height / 2 - ((canvas.height / 2 - offset[1]) * scale) / old,
    ];
    draw();
  }
  $("zoomIn").onclick = () => zoom(1.25);
  $("zoomOut").onclick = () => zoom(0.8);
  $("fit").onclick = fit;
  $("tool").onchange = () => {
    polygon = [];
    draw();
  };
  $("view").onchange = () => {
    $("sliderLabel").hidden = $("view").value !== "compare";
    draw();
  };
  $("split").oninput = draw;
  document.addEventListener("keydown", (event) => {
    if (event.target.matches("input,select,textarea")) return;
    if (event.key === "Escape") {
      polygon = [];
      stroke = null;
      draw();
    }
    if ((event.ctrlKey || event.metaKey) && event.key === "z") {
      event.preventDefault();
      $(event.shiftKey ? "redo" : "undo").click();
    }
  });
  async function readState() {
    const response = await fetch("/api/interior/masks/state", {
      cache: "no-store",
    });
    if (!response.ok) throw Error("Uložený stav není dostupný.");
    return response.json();
  }
  function renderVariants() {
    $("variants").replaceChildren(
      ...variants.map((variant) => {
        const button = document.createElement("button"),
          img = document.createElement("img"),
          label = document.createElement("span");
        img.src = "/api/interior/masks/image?variant=" + variant.id;
        img.alt = "";
        label.textContent = variant.title;
        button.append(img, label);
        button.onclick = () => openVariant(variant);
        return button;
      }),
    );
  }
  function openVariant(variant) {
    result.onload = draw;
    result.src = "/api/interior/masks/image?variant=" + variant.id;
    $("view").value = "compare";
    $("sliderLabel").hidden = false;
    const r = variant.report;
    $("report").textContent =
      "Změněné chráněné pixely: " +
      r.protected_changed_pixels +
      ". Geometrie: neověřená. Překryv s ochranou: " +
      r.conflict_pixels +
      " px.";
  }
  async function send(action, copy = false) {
    if (busy) return;
    if (polygon.length || stroke) {
      status("Nejdřív dokonči nebo zruš rozkreslený tvar.");
      return;
    }
    busy = true;
    document
      .querySelectorAll("button,input,select")
      .forEach((el) => (el.disabled = true));
    try {
      if (copy) {
        const state = await readState();
        revision = state.revision;
      }
      if (!pending) {
        pending = {
          action: copy ? "copy" : action,
          request_id: crypto.randomUUID(),
          expected_revision: revision,
          base_sha256: baseHash,
          layers: JSON.parse(JSON.stringify(layers)),
          title: $("title").value,
          color: $("color").value,
          feather: Number($("feather").value),
        };
        cache();
      }
      const response = await fetch("/api/interior/masks/action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(pending),
      });
      const data = await response.json();
      if (!data.ok) {
        pending = null;
        cache();
        if (data.error === "conflict") $("conflict").hidden = false;
        throw Error(data.message || "Uložení se nezdařilo.");
      }
      revision = data.revision;
      pending = null;
      dirty = false;
      cache();
      $("conflict").hidden = true;
      const state = await readState();
      variants = state.variants;
      renderVariants();
      if (copy) {
        layers = state.layers;
        selected = layers[0]?.id;
        undo = [];
        redo = [];
        cache();
        draw();
      }
      if (data.variant_id)
        openVariant(variants.find((v) => v.id === data.variant_id));
      status("Uloženo · revize " + revision);
    } catch (error) {
      status(
        error.message +
          (pending ? " Příští uložení ověří stejnou operaci." : ""),
      );
    } finally {
      busy = false;
      document
        .querySelectorAll("button,input,select")
        .forEach((el) => (el.disabled = false));
      refreshLayers();
    }
  }
  $("save").onclick = () => send("save");
  $("generate").onclick = () => send("variant");
  $("copy").onclick = () => send("variant", true);
  $("reload").onclick = async () => {
    try {
      const state = await readState();
      layers = state.layers;
      revision = state.revision;
      dirty = false;
      pending = null;
      undo = [];
      redo = [];
      selected = layers[0]?.id;
      cache();
      $("conflict").hidden = true;
      refreshLayers();
      draw();
      status("Načtena serverová revize " + revision);
    } catch (error) {
      status(error.message);
    }
  };
  window.addEventListener("beforeunload", (event) => {
    if (dirty) {
      event.preventDefault();
      event.returnValue = "";
    }
  });
  async function init() {
    try {
      const state = await readState();
      layers = state.layers;
      revision = state.revision;
      baseHash = state.base_sha256;
      variants = state.variants;
      let saved = null;
      try {
        saved = JSON.parse(localStorage.getItem(cacheKey) || "null");
      } catch (_) {
        status("Místní kopie není dostupná. Používám serverovou práci.");
      }
      if (saved?.dirty && saved.baseHash === baseHash) {
        layers = saved.layers;
        dirty = true;
        pending = saved.pending;
        selected = saved.selected;
        if (saved.revision !== revision) $("conflict").hidden = false;
        revision = saved.revision;
      }
      selected = selected || layers[0]?.id;
      renderVariants();
      refreshLayers();
      original.onload = resize;
      original.src = "/api/interior/masks/image";
      new ResizeObserver(resize).observe($("viewport"));
      status(
        dirty
          ? "Obnovena místní rozepsaná práce."
          : "Uloženo · revize " + revision,
      );
      if (variants[0]) openVariant(variants[0]);
    } catch (error) {
      status(error.message);
    }
  }
  init();
})();
