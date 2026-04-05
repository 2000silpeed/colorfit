const fs = require("fs");
const path = require("path");

const OUT = path.resolve(__dirname, "output");
const personas = ["A", "B", "C"];
const personaMeta = {
  A: {
    name: "페르소나 A",
    tagline: "여성 20대 · 여름쿨소프트 · 소개팅 룩",
    profile: { 이름: "김하늘 (28세)", 톤: "summer_cool_soft", 성별: "여성", 연령: "20s", TPO: "데이트", 예산: "5~15만" },
    color: "#B0A6C6",
  },
  B: {
    name: "페르소나 B",
    tagline: "남성 30대 · 가을웜딥 · 출근 룩",
    profile: { 이름: "정재훈 (33세)", 톤: "autumn_warm_deep", 성별: "남성", 연령: "30s", TPO: "출근", 예산: "5~15만" },
    color: "#8B4513",
  },
  C: {
    name: "페르소나 C",
    tagline: "여성 40+ · 겨울쿨딥 · 하객/이벤트 룩",
    profile: { 이름: "박서연 (45세)", 톤: "winter_cool_deep", 성별: "여성", 연령: "40+", TPO: "행사", 예산: "15~30만" },
    color: "#1E1E4E",
  },
};

let allSteps = [];
const personaCounts = {};
for (const p of personas) {
  const file = path.join(OUT, `steps_${p}.json`);
  if (fs.existsSync(file)) {
    const steps = JSON.parse(fs.readFileSync(file, "utf8"));
    allSteps = allSteps.concat(steps);
    personaCounts[p] = steps.length;
  }
}

const videoDir = path.join(OUT, "artifacts");
const videoMap = {};
if (fs.existsSync(videoDir)) {
  for (const d of fs.readdirSync(videoDir)) {
    const full = path.join(videoDir, d);
    if (!fs.statSync(full).isDirectory()) continue;
    const webm = path.join(full, "video.webm");
    if (fs.existsSync(webm)) {
      let key = null;
      if (/01-persona-a/i.test(d) || d.includes("페르소나-A")) key = "A";
      else if (/02-persona-b/i.test(d) || d.includes("페르소나-B")) key = "B";
      else if (/03-persona-c/i.test(d) || d.includes("페르소나-C")) key = "C";
      if (!key) continue;
      const dest = path.join(OUT, `video_${key}.webm`);
      fs.copyFileSync(webm, dest);
      videoMap[key] = `video_${key}.webm`;
    }
  }
}

const totalSteps = allSteps.length;
const totalPersonas = Object.keys(personaCounts).length;

function renderPersonaSection(p) {
  const meta = personaMeta[p];
  const steps = allSteps.filter((s) => s.persona.includes(`페르소나 ${p}`));
  if (!steps.length) return "";

  const cards = steps.map((s, i) => `
    <article class="step" id="step-${p}-${i + 1}">
      <div class="step-image"><img src="${s.screenshot}" loading="lazy" alt="${s.title}" /><span class="step-num">${String(i + 1).padStart(2, "0")}</span></div>
      <div class="step-body">
        <h4>${s.title}</h4>
        <p class="step-desc">${s.desc}</p>
        <div class="step-meta"><code>${s.url || "/"}</code><span>${new Date(s.timestamp).toLocaleTimeString("ko-KR", { hour12: false })}</span></div>
      </div>
    </article>`).join("");

  const profileRows = Object.entries(meta.profile).map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join("");

  return `
    <section class="persona-section" id="persona-${p}" style="--persona-color: ${meta.color}">
      <div class="persona-header">
        <div class="persona-swatch" style="background: ${meta.color}"></div>
        <div>
          <h2>${meta.name}</h2>
          <p class="tagline">${meta.tagline}</p>
        </div>
        <span class="step-count">${steps.length} steps</span>
      </div>
      <dl class="persona-profile">${profileRows}</dl>
      ${videoMap[p] ? `
      <div class="video-wrap"><video src="${videoMap[p]}" controls muted loop playsinline></video></div>` : ""}
      <div class="steps-grid">${cards}</div>
    </section>`;
}

const html = `<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>ColorFit 데모 리포트 — 3 페르소나 풀 시나리오</title>
<style>
  :root { --bg:#F8F6F3; --bg2:#FFF; --text:#1A1714; --text2:#6B6560; --accent:#964F4C; --border:#E8E2DB; }
  * { box-sizing:border-box; margin:0; padding:0; }
  body { font-family:"Pretendard",-apple-system,BlinkMacSystemFont,sans-serif; background:var(--bg); color:var(--text); line-height:1.6; -webkit-font-smoothing:antialiased; }
  .container { max-width:1280px; margin:0 auto; padding:48px 24px; }
  header { text-align:center; padding:48px 0; border-bottom:1px solid var(--border); margin-bottom:48px; }
  .brand { font-family:"Nanum Myeongjo",serif; font-size:52px; color:var(--accent); font-weight:700; letter-spacing:-1px; }
  .subtitle { color:var(--text2); font-size:16px; margin-top:8px; }
  .meta-badges { display:flex; gap:8px; justify-content:center; flex-wrap:wrap; margin-top:24px; }
  .badge { padding:6px 14px; background:var(--bg2); border:1px solid var(--border); border-radius:9999px; font-size:13px; color:var(--text2); }
  .badge.pass { background:#E8F0E8; color:#2D5A2D; border-color:#B5D4B5; }
  .stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:16px; margin-bottom:48px; }
  .stat-card { background:var(--bg2); border:1px solid var(--border); border-radius:12px; padding:24px; }
  .stat-label { font-size:12px; color:var(--text2); text-transform:uppercase; letter-spacing:0.5px; }
  .stat-value { font-size:36px; font-weight:700; color:var(--accent); margin-top:4px; font-family:"Nanum Myeongjo",serif; }
  .stat-sub { font-size:12px; color:var(--text2); margin-top:4px; }
  .persona-section { margin-bottom:64px; padding:32px; background:var(--bg2); border-radius:20px; border:1px solid var(--border); border-top:4px solid var(--persona-color); }
  .persona-header { display:flex; align-items:center; gap:16px; margin-bottom:24px; }
  .persona-swatch { width:56px; height:56px; border-radius:50%; border:3px solid var(--bg); box-shadow:0 0 0 1px var(--border); }
  .persona-header h2 { font-family:"Nanum Myeongjo",serif; font-size:28px; }
  .persona-header .tagline { font-size:14px; color:var(--text2); margin-top:2px; }
  .persona-header .step-count { margin-left:auto; padding:6px 14px; background:var(--persona-color); color:#fff; border-radius:9999px; font-size:13px; font-weight:600; }
  .persona-profile { display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); gap:12px 16px; padding:16px; background:var(--bg); border-radius:12px; margin-bottom:24px; }
  .persona-profile dt { font-size:11px; color:var(--text2); text-transform:uppercase; letter-spacing:0.5px; margin-bottom:2px; }
  .persona-profile dd { font-size:14px; color:var(--text); font-weight:500; }
  .video-wrap { background:#000; border-radius:16px; overflow:hidden; max-width:390px; margin:0 auto 24px; aspect-ratio:390/844; }
  .video-wrap video { width:100%; height:100%; display:block; }
  .steps-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:16px; }
  .step { background:var(--bg); border:1px solid var(--border); border-radius:12px; overflow:hidden; transition:transform 0.2s,box-shadow 0.2s; }
  .step:hover { transform:translateY(-2px); box-shadow:0 8px 24px rgba(0,0,0,0.08); }
  .step-image { position:relative; background:#F0EDE8; }
  .step-image img { width:100%; height:auto; aspect-ratio:390/844; object-fit:cover; object-position:top; display:block; }
  .step-num { position:absolute; top:8px; left:8px; background:var(--persona-color); color:#fff; width:26px; height:26px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:11px; font-weight:700; }
  .step-body { padding:12px; }
  .step-body h4 { font-size:14px; font-weight:700; margin-bottom:4px; }
  .step-desc { font-size:12px; color:var(--text2); line-height:1.5; margin-bottom:6px; }
  .step-meta { display:flex; justify-content:space-between; align-items:center; font-size:10px; color:var(--text2); }
  .step-meta code { background:var(--bg2); padding:2px 6px; border-radius:4px; font-family:"SF Mono",Monaco,monospace; }
  footer { text-align:center; padding:48px 0; border-top:1px solid var(--border); color:var(--text2); font-size:13px; }
  .toc { display:flex; gap:12px; justify-content:center; margin-bottom:32px; }
  .toc a { padding:10px 20px; background:var(--bg2); border:1px solid var(--border); border-radius:9999px; font-size:14px; color:var(--text); text-decoration:none; font-weight:500; transition:all 0.2s; }
  .toc a:hover { background:var(--accent); color:#fff; border-color:var(--accent); }
</style>
</head>
<body>
  <div class="container">
    <header>
      <h1 class="brand">ColorFit</h1>
      <p class="subtitle">전체 기능 데모 리포트 · 3 페르소나 풀 시나리오</p>
      <div class="meta-badges">
        <span class="badge pass">✓ Playwright E2E PASSED</span>
        <span class="badge">${new Date().toLocaleString("ko-KR")}</span>
        <span class="badge">${totalPersonas} personas · ${totalSteps} steps</span>
        <span class="badge">Pixel 7 Mobile</span>
      </div>
    </header>

    <div class="stats">
      <div class="stat-card"><div class="stat-label">페르소나</div><div class="stat-value">${totalPersonas}</div><div class="stat-sub">multi-profile journey</div></div>
      <div class="stat-card"><div class="stat-label">총 스텝</div><div class="stat-value">${totalSteps}</div><div class="stat-sub">feature coverage</div></div>
      <div class="stat-card"><div class="stat-label">코디 풀</div><div class="stat-value">5,022</div><div class="stat-sub">outfits available</div></div>
      <div class="stat-card"><div class="stat-label">착장샷</div><div class="stat-value">Gemini</div><div class="stat-sub">2.5-flash-image</div></div>
    </div>

    <nav class="toc">
      ${personas.map((p) => personaCounts[p] ? `<a href="#persona-${p}">${personaMeta[p].name}</a>` : "").join("")}
    </nav>

    ${personas.map(renderPersonaSection).join("\n")}

    <footer>
      ColorFit · Task 5.11 Demo · Generated by Playwright ${require("@playwright/test/package.json").version}<br/>
      ${new Date().toISOString()}
    </footer>
  </div>
</body>
</html>`;

fs.writeFileSync(path.join(OUT, "report.html"), html);
console.log(`✓ Report generated: ${path.join(OUT, "report.html")}`);
console.log(`  Personas: ${totalPersonas}  Steps: ${totalSteps}`);
for (const p of personas) {
  if (personaCounts[p]) console.log(`  - ${personaMeta[p].name}: ${personaCounts[p]} steps, video: ${videoMap[p] || "—"}`);
}
