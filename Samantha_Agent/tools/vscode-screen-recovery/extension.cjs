"use strict";

const ID = "samantha-local.screen-recovery";

function parseRequest(uri) {
  if (uri.scheme !== "vscode" || uri.authority !== ID || uri.path !== "/attach" || uri.fragment) {
    throw new Error("Neplatný odkaz obnovy screenu.");
  }
  const params = new URLSearchParams(uri.query);
  if ([...params].length !== 2 || !/^\d{1,5}$/.test(params.get("port") || "")
      || !/^[a-f0-9]{64}$/.test(params.get("ticket") || "")) {
    throw new Error("Neplatný požadavek obnovy screenu.");
  }
  const port = Number(params.get("port"));
  if (port < 1 || port > 65535) throw new Error("Neplatný port Cockpitu.");
  return {port, ticket: params.get("ticket")};
}

function createHandler(vscode, fetcher = fetch, platform = process.platform) {
  const terminals = new Map();
  let busy = false;
  return {
    async handleUri(uri) {
      if (busy) return;
      busy = true;
      try {
        if (platform !== "darwin" || !vscode.workspace.isTrusted) {
          throw new Error("Obnova vyžaduje místní VS Code na Macu a důvěryhodné okno.");
        }
        const {port, ticket} = parseRequest(uri);
        const response = await fetcher(`http://127.0.0.1:${port}/api/screen/sessions/claim`, {
          method: "POST", headers: {"Content-Type": "application/json"},
          body: JSON.stringify({ticket}), signal: AbortSignal.timeout(10000), redirect: "error"
        });
        const data = await response.json();
        if (!response.ok || !data.ok || !/^[0-9]+\.[A-Za-z0-9_.-]+$/.test(data.socket || "")) {
          throw new Error("Požadavek obnovy vypršel nebo screen není dostupný. Obnov přehled v Cockpitu.");
        }
        const previous = terminals.get(data.socket);
        if (previous && vscode.window.terminals.includes(previous) && previous.exitStatus === undefined) {
          previous.show(false);
          return;
        }
        // Start screen directly. Never send text into an existing shell/Codex.
        const terminal = vscode.window.createTerminal({
          name: `Samantha · ${data.socket}`, shellPath: "/usr/bin/screen",
          shellArgs: ["-d", "-r", data.socket], env: {STY: null},
          isTransient: true
        });
        terminals.set(data.socket, terminal);
        terminal.show(false);
      } catch (_) {
        vscode.window.showErrorMessage("Screen se nepodařilo obnovit. Zkontroluj místní Cockpit, důvěryhodnost okna a aktuální přehled screenů. Požadavek se automaticky neopakuje.");
      } finally {
        busy = false;
      }
    }
  };
}

function activate(context) {
  const vscode = require("vscode");
  context.subscriptions.push(vscode.window.registerUriHandler(createHandler(vscode)));
}

module.exports = {activate, createHandler, parseRequest};
