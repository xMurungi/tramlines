import "./styles/tokens.css";

// Phase 0 placeholder: proves the toolchain builds. The viewer arrives in Phase 4.
const app = document.querySelector<HTMLElement>("#app");
if (!app) throw new Error("missing #app element");

app.innerHTML = `
  <section style="min-height:100vh;display:grid;place-items:center;text-align:center;padding:16px">
    <div>
      <h1 style="font-family:var(--font-display);font-weight:400;letter-spacing:0.3em;color:var(--gold)">TRAMLINES</h1>
      <p style="font-family:var(--font-mono);color:var(--text-muted)">phase 0 · the machine is not yet running</p>
    </div>
  </section>
`;
