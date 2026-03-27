import { useState, useRef, useEffect, useCallback } from "react";

/* ═══════════ TIER SYSTEM ═══════════ */
const TIERS = {
  MLS:    { label: "MLS",  color: "#fff", bg: "#C2002F" },
  "USL-C":{ label: "USLC", color: "#fff", bg: "#1F4CD7" },
  USL1:   { label: "USL1", color: "#fff", bg: "#27AE3D" },
  MLSNP:  { label: "NP",   color: "#fff", bg: "#7C3AED" },
  USL2:   { label: "USL2", color: "#fff", bg: "#D97706" },
  AM:     { label: "AM",   color: "#fff", bg: "#6B7280" },
};
const MLS_L=["Atlanta United","Austin FC","Charlotte FC","Chicago Fire FC","Colorado Rapids","Columbus Crew","D.C. United","Houston Dynamo FC","Minnesota United FC","New England Revolution","New York City FC","Orlando City SC","Red Bull New York","San Jose Earthquakes","Sporting Kansas City","St. Louis CITY SC"];
const USLC_L=["Charleston Battery","Detroit City FC","Hartford Athletic","Indy Eleven","Loudoun United FC","Louisville City FC","Pittsburgh Riverhounds SC","Rhode Island FC","Colorado Springs Switchbacks FC","El Paso Locomotive FC","FC Tulsa","Lexington SC","New Mexico United","Orange County SC","Phoenix Rising FC","Sacramento Republic FC","San Antonio FC"];
const USL1_L=["AV ALTA FC","Charlotte Independence","Chattanooga Red Wolves SC","FC Naples","Forward Madison FC","Greenville Triumph SC","One Knoxville SC","Portland Hearts of Pine","Richmond Kickers","Spokane Velocity FC","Union Omaha","Westchester SC"];
const MLSNP_L=["Carolina Core FC","Chattanooga FC"];
const USL2_L=["Vermont Green FC","Flint City Bucks","Steel City FC","Ventura County Fusion","Des Moines Menace","Northern Virginia FC","Asheville City SC","Flower City Union","West Chester United SC"];
function getTier(t){if(!t)return null;if(MLS_L.some(m=>t.includes(m)||m.includes(t)))return"MLS";if(USLC_L.some(m=>t.includes(m)||m.includes(t)))return"USL-C";if(USL1_L.some(m=>t.includes(m)||m.includes(t)))return"USL1";if(MLSNP_L.some(m=>t===m))return"MLSNP";if(USL2_L.some(m=>t.includes(m)||m.includes(t)))return"USL2";return"AM";}
function getWinner(m){if(m.homeScore==null||m.awayScore==null)return null;return m.homeScore>m.awayScore?m.home:m.away;}
const TIER_RANK = { MLS: 0, "USL-C": 1, USL1: 2, MLSNP: 3, USL2: 4, AM: 5 };
function isCupset(m) {
  const w = getWinner(m);
  if (!w) return false;
  const loser = w === m.home ? m.away : m.home;
  const wRank = TIER_RANK[getTier(w)] ?? 5;
  const lRank = TIER_RANK[getTier(loser)] ?? 5;
  return wRank > lRank;
}

/* ═══════════ PROGRESSIVE SIZING PER ROUND ═══════════ */
const ROUND_SIZES = [
  { font: 11, badge: 10, cw: 180, ch: 40 },  // R1
  { font: 12, badge: 10, cw: 184, ch: 42 },  // R2
  { font: 12, badge: 11, cw: 188, ch: 42 },  // R32 (same as R2)
  { font: 13, badge: 11, cw: 194, ch: 44 },  // R16
  { font: 14, badge: 12, cw: 200, ch: 46 },  // QF
  { font: 15, badge: 12, cw: 206, ch: 48 },  // SF
];
const FINAL_SIZE = { font: 16, badge: 13, cw: 218, ch: 60 };
const HG = 30;
const VG = 10;

function colX(colIdx) {
  let x = 0;
  for (let i = 0; i < colIdx; i++) {
    x += ROUND_SIZES[i].cw + HG;
  }
  return x;
}

const RNAMES=[
  {name:"1ST ROUND",sub:"Mar 17-19"},
  {name:"2ND ROUND",sub:"Mar 31 / Apr 1"},
  {name:"ROUND OF 32",sub:"Apr 14-15"},
  {name:"ROUND OF 16",sub:"Apr 28-29"},
  {name:"QUARTERS",sub:"May 19-20"},
  {name:"SEMIS",sub:"Sep 15-16"},
];

/* ═══════════ COMPONENTS ═══════════ */
function TierBadge({team, size}){
  const tier=getTier(team);if(!tier)return null;const t=TIERS[tier];
  return <span style={{fontSize:size||7,fontWeight:700,padding:"1px 4px",borderRadius:3,color:t.color,background:t.bg,fontFamily:"monospace",lineHeight:`${(size||7)+6}px`,flexShrink:0}}>{t.label}</span>;
}

function Cell({match, x, y, roundIdx, isMls, isChamp}){
  const sz = isChamp ? FINAL_SIZE : ROUND_SIZES[roundIdx] || ROUND_SIZES[0];
  const bw = sz.cw;
  const bh = sz.ch;
  const m = match || {home:null,away:null,homeScore:null,awayScore:null};
  const win = getWinner(m);
  const cupset = match && isCupset(m);
  const headerH = isChamp ? 18 : 0;
  const rowH = (bh - headerH) / 2;

  const row = (name, score, won, isTop) => {
    const tbd = !name;
    const dn = isMls && tbd && isTop ? "MLS Team" : isMls && tbd && !isTop ? "R2 Winner" : name || "TBD";
    return (
      <div style={{display:"flex",alignItems:"center",height:rowH,
        background:won?"#e8f5ee":"#fff",
        borderTop:isTop?"none":"1px solid #e0e0e0",
        borderLeft:won?"3px solid #27AE3D":"3px solid transparent",
        paddingLeft:5,paddingRight:5,gap:3}}>
        {name && <TierBadge team={name} size={sz.badge}/>}
        <span title={name || ""} style={{flex:1,fontSize:sz.font,fontWeight:won?700:400,
          whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis",
          color:tbd?"#999":won?"#15192B":"#333",
          fontStyle:tbd?"italic":"normal",cursor:name?"default":"inherit"}}>{dn}</span>
        {isTop && (() => {
          const isLive = m.status === "live";
          const isFT = m.status === "ft";
          const label = isLive ? (m.clock || "LIVE") : isFT ? (m.note || "FT") : m.note;
          if (!label) return null;
          return <span style={{fontSize:Math.max(6, sz.badge-1),fontFamily:"monospace",fontWeight:700,
            color:isLive?"#C2002F":isFT?"#27AE3D":"#999",
            animation:isLive?"pulse 1.5s ease-in-out infinite":undefined}}>{label}</span>;
        })()}
        <span style={{fontSize:sz.font,fontWeight:700,minWidth:14,textAlign:"right",
          fontFamily:"monospace",
          color:won?"#27AE3D":m.status==="live"?"#C2002F":score!=null?"#555":"#ccc"}}>{score!=null?score:""}</span>
      </div>
    );
  };

  return (
    <foreignObject x={x} y={y} width={bw} height={bh}>
      <div style={{width:bw,height:bh,position:"relative",
        border:`1px solid ${cupset?"#D97706":isChamp?"#C2002F":"#d0d0d0"}`,
        borderRadius:isChamp?6:3,overflow:"hidden",
        background:isChamp?"#fff":"#fff",
        boxShadow:cupset?"0 0 6px #D9770633":isChamp?"0 0 12px #C2002F22":"0 1px 3px #00000012"}}>
        {cupset && <span style={{position:"absolute",top:-1,right:3,fontSize:Math.max(7,sz.badge-2),fontWeight:800,color:"#D97706",fontFamily:"monospace",letterSpacing:"0.05em"}}>CUPSET</span>}
        {isChamp && (
          <div style={{textAlign:"center",fontSize:9,fontWeight:800,color:"#fff",
            letterSpacing:"0.18em",fontFamily:"monospace",padding:"2px 0",height:headerH,
            display:"flex",alignItems:"center",justifyContent:"center",
            background:"#C2002F",
            borderBottom:"1px solid #a0001f"}}>FINAL &#183; OCT 21</div>
        )}
        {row(m.home,m.homeScore,win===m.home,true)}
        {row(m.away,m.awayScore,win===m.away,false)}
      </div>
    </foreignObject>
  );
}

/* ═══════════ BRACKET BUILDER ═══════════ */
// convergeDir: "down" (upper bracket) or "up" (lower bracket)
//   Pulls later rounds toward the divider, clamped so a match never
//   goes past the edges of the feeder pair it comes from.
function buildRegion(matches, padTop, convergeDir) {
  const rounds = [];
  const conns = [];

  const r1sz = ROUND_SIZES[0];
  const r1 = matches.map((m, i) => ({
    x: colX(0), y: padTop + i * (r1sz.ch + VG), match: m, roundIdx: 0
  }));
  rounds.push(r1);

  // From R16 (rIdx=3) onward, pull toward feeder edge
  const CONVERGE = { 3: 0.5, 4: 0.7, 5: 0.85 };

  let prev = r1;
  for (let rIdx = 1; rIdx <= 5; rIdx++) {
    const sz = ROUND_SIZES[rIdx];
    const prevSz = ROUND_SIZES[rIdx - 1];
    const isMls = rIdx === 2;
    const cur = [];
    const cx = colX(rIdx);
    const converge = convergeDir ? (CONVERGE[rIdx] || 0) : 0;

    if (isMls) {
      for (let i = 0; i < prev.length; i++) {
        const p = prev[i];
        const pMidY = p.y + prevSz.ch / 2;
        const newY = pMidY - sz.ch / 2;
        cur.push({ x: cx, y: newY, match: null, isMls: true, roundIdx: rIdx });
        conns.push({ x1: p.x + prevSz.cw, y1: pMidY, x2: cx, y2: pMidY });
      }
    } else {
      for (let i = 0; i < prev.length; i += 2) {
        const p1 = prev[i], p2 = prev[i + 1];
        const pSz = ROUND_SIZES[rIdx - 1];
        const p1mid = p1.y + pSz.ch / 2;
        const p2mid = p2 ? p2.y + pSz.ch / 2 : p1mid;
        const midY = (p1mid + p2mid) / 2;

        let newY = midY - sz.ch / 2;
        if (converge > 0 && p2) {
          if (convergeDir === "down") {
            // Upper bracket: pull down, but top edge can't go below p2's bottom edge
            const maxY = p2.y + pSz.ch;
            const targetY = midY + (maxY - midY + sz.ch / 2) * converge - sz.ch / 2;
            newY = Math.min(targetY, maxY);
          } else {
            // Lower bracket: pull up, but bottom edge can't go above p1's top edge
            const minY = p1.y - sz.ch;
            const targetY = midY + (minY - midY + sz.ch / 2) * converge - sz.ch / 2;
            newY = Math.max(targetY, minY);
          }
        }

        const adjustedMidY = newY + sz.ch / 2;
        const w1 = p1.match ? getWinner(p1.match) : null;
        const w2 = p2?.match ? getWinner(p2.match) : null;
        const advMatch = (w1 || w2) ? { home: w1 || null, away: w2 || null, homeScore: null, awayScore: null } : null;
        cur.push({ x: cx, y: newY, match: advMatch, roundIdx: rIdx });
        conns.push({ x1: p1.x + pSz.cw, y1: p1mid, x2: cx, y2: adjustedMidY });
        if (p2) conns.push({ x1: p2.x + pSz.cw, y1: p2mid, x2: cx, y2: adjustedMidY });
      }
    }
    rounds.push(cur);
    prev = cur;
  }
  return { rounds, conns };
}

function DrawConns({ conns }) {
  return conns.map((c, i) => {
    const mx = (c.x1 + c.x2) / 2;
    return <path key={i} d={`M${c.x1},${c.y1}H${mx}V${c.y2}H${c.x2}`}
      fill="none" stroke="#c0c0c0" strokeWidth={1} />;
  });
}

function formatGameTime(isoStr) {
  if (!isoStr) return null;
  try {
    const d = new Date(isoStr);
    const mm = String(d.getMonth() + 1).padStart(2, "0");
    const dd = String(d.getDate()).padStart(2, "0");
    const yyyy = d.getFullYear();
    const et = d.toLocaleString("en-US", { timeZone: "America/New_York", hour: "numeric", minute: "2-digit", hour12: true });
    const pt = d.toLocaleString("en-US", { timeZone: "America/Los_Angeles", hour: "numeric", minute: "2-digit", hour12: true });
    return `${mm}/${dd}/${yyyy} ${et} ET / ${pt} PT`;
  } catch { return null; }
}

function DrawRounds({ rounds }) {
  return rounds.map((round, ri) => round.map((s, mi) => {
    const sz = ROUND_SIZES[s.roundIdx] || ROUND_SIZES[0];
    const gt = s.match && !s.match.status ? formatGameTime(s.match.gameTime) : null;
    return <g key={`${ri}-${mi}`}>
      <Cell match={s.match} x={s.x} y={s.y}
        roundIdx={s.roundIdx} isMls={s.isMls} />
      {gt && <text x={s.x + sz.cw / 2} y={s.y + sz.ch + 9}
        textAnchor="middle" fontSize={Math.max(7, sz.badge - 1)}
        fill="#777" fontFamily="monospace">{gt}</text>}
    </g>;
  }));
}

/* ═══════════ ZOOM HOOK ═══════════ */
function useZoom(ref, initial = 1) {
  const [zoom, setZoom] = useState(initial);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let lastDist = 0;

    function onWheel(e) {
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault();
        const delta = e.deltaY > 0 ? -0.05 : 0.05;
        setZoom(z => Math.min(2, Math.max(0.3, z + delta)));
      }
    }

    function onTouchStart(e) {
      if (e.touches.length === 2) {
        const dx = e.touches[0].clientX - e.touches[1].clientX;
        const dy = e.touches[0].clientY - e.touches[1].clientY;
        lastDist = Math.sqrt(dx * dx + dy * dy);
      }
    }

    function onTouchMove(e) {
      if (e.touches.length === 2) {
        e.preventDefault();
        const dx = e.touches[0].clientX - e.touches[1].clientX;
        const dy = e.touches[0].clientY - e.touches[1].clientY;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (lastDist > 0) {
          const scale = dist / lastDist;
          setZoom(z => Math.min(2, Math.max(0.3, z * scale)));
        }
        lastDist = dist;
      }
    }

    function onTouchEnd() { lastDist = 0; }

    el.addEventListener("wheel", onWheel, { passive: false });
    el.addEventListener("touchstart", onTouchStart, { passive: true });
    el.addEventListener("touchmove", onTouchMove, { passive: false });
    el.addEventListener("touchend", onTouchEnd, { passive: true });
    return () => {
      el.removeEventListener("wheel", onWheel);
      el.removeEventListener("touchstart", onTouchStart);
      el.removeEventListener("touchmove", onTouchMove);
      el.removeEventListener("touchend", onTouchEnd);
    };
  }, [ref]);

  return [zoom, setZoom];
}

/* ═══════════ DRAG-TO-SCROLL HOOK ═══════════ */
function useDragScroll(ref) {
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let isDown = false;
    let startX, startY, scrollLeft, scrollTop;

    function onMouseDown(e) {
      isDown = true;
      el.style.cursor = "grabbing";
      startX = e.clientX;
      startY = e.clientY;
      scrollLeft = el.scrollLeft;
      scrollTop = el.scrollTop;
    }

    function onMouseUp() {
      isDown = false;
      el.style.cursor = "grab";
    }

    function onMouseMove(e) {
      if (!isDown) return;
      e.preventDefault();
      el.scrollLeft = scrollLeft - (e.clientX - startX);
      el.scrollTop = scrollTop - (e.clientY - startY);
    }

    el.addEventListener("mousedown", onMouseDown);
    window.addEventListener("mouseup", onMouseUp);
    window.addEventListener("mousemove", onMouseMove);
    return () => {
      el.removeEventListener("mousedown", onMouseDown);
      window.removeEventListener("mouseup", onMouseUp);
      window.removeEventListener("mousemove", onMouseMove);
    };
  }, [ref]);
}

/* ═══════════ MAIN APP ═══════════ */
export default function App() {
  const [bracket, setBracket] = useState(null);
  const [error, setError] = useState(null);
  const isMobile = window.innerWidth <= 768;
  const [headerExpanded, setHeaderExpanded] = useState(!isMobile);
  const bracketRef = useRef(null);
  const [zoom, setZoom] = useZoom(bracketRef, 1.0);
  useDragScroll(bracketRef);

  const fetchBracket = useCallback(async () => {
    try {
      const resp = await fetch("/api/bracket");
      if (!resp.ok) throw new Error("Failed to load bracket");
      const data = await resp.json();
      setBracket(data);
      setError(null);
    } catch (e) {
      setError(e.message);
    }
  }, []);

  // Initial fetch + poll every 5 minutes
  useEffect(() => {
    fetchBracket();
    // Poll every 30s during evening game windows (6pm-midnight ET), otherwise every 5min
    const now = new Date();
    const etHour = new Date(now.toLocaleString("en-US", { timeZone: "America/New_York" })).getHours();
    const pollMs = (etHour >= 18 && etHour < 24) ? 30 * 1000 : 5 * 60 * 1000;
    const interval = setInterval(fetchBracket, pollMs);
    return () => clearInterval(interval);
  }, [fetchBracket]);

  if (error && !bracket) {
    return (
      <div style={{ background: "#070f0b", minHeight: "100vh", color: "#c0d8cc",
        display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "monospace" }}>
        Loading bracket...
      </div>
    );
  }

  if (!bracket) {
    return (
      <div style={{ background: "#070f0b", minHeight: "100vh", color: "#c0d8cc",
        display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "monospace" }}>
        Loading...
      </div>
    );
  }

  const R1 = bracket.rounds[0]?.matches || [];

  const topR1 = R1.slice(0, 16), botR1 = R1.slice(16, 32);
  const topB = buildRegion(topR1, 8, "down");
  const botB = buildRegion(botR1, 8, "up");

  const topSemi = topB.rounds[5]?.[0];
  const botSemi = botB.rounds[5]?.[0];
  const semiSz = ROUND_SIZES[5];

  const regionH = 16 * (ROUND_SIZES[0].ch + VG) + 20;
  const dividerGap = 58;
  const botOffset = regionH + dividerGap;
  const totalH = botOffset + regionH + 20;

  const finalCY = regionH + dividerGap / 2;
  const finalY = finalCY - FINAL_SIZE.ch / 2;
  const finalX = colX(5) + semiSz.cw + HG;

  const topSemiMidY = topSemi ? topSemi.y + semiSz.ch / 2 : regionH / 2;
  const botSemiMidY = botSemi ? botSemi.y + semiSz.ch / 2 + botOffset : botOffset + regionH / 2;

  const svgW = finalX + FINAL_SIZE.cw + 60;

  const totalComplete = R1.filter(m => getWinner(m)).length;
  const cupsetCount = R1.filter(m => isCupset(m)).length;
  const pendingMatch = R1.find(m => m.homeScore == null);

  const zoomPresets = [
    { label: "Fit", val: 0.55 },
    { label: "S", val: 0.7 },
    { label: "M", val: 0.85 },
    { label: "L", val: 1.0 },
    { label: "XL", val: 1.3 },
    { label: "XXL", val: 2.0 },
  ];

  return (
    <div style={{ background: "#f5f5f5", minHeight: "100vh", color: "#333", fontFamily: "'Segoe UI',system-ui,sans-serif" }}>

      {/* HEADER */}
      <div style={{ borderBottom: "1px solid #e0e0e0", padding: "14px 20px 12px",
        background: "#15192B" }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 21, fontWeight: 800, color: "#fff", letterSpacing: "-0.02em" }}>
              <span style={{ color: "#C2002F" }}>2026</span>{" "}
              <a href="https://www.ussoccer.com/us-open-cup" target="_blank" rel="noopener noreferrer"
                style={{ color: "#fff", textDecoration: "none", borderBottom: "1px dashed #ffffff44" }}>
                Lamar Hunt U.S. Open Cup
              </a>
            </h1>
            <div style={{ fontSize: 14, color: "#bfbfbf", fontFamily: "monospace", marginTop: 2, letterSpacing: "0.1em" }}>
              111TH EDITION &#183; 80 TEAMS &#183; 7 ROUNDS &#183; $1M PURSE
            </div>
            <div style={{ fontSize: 12, color: "#999", fontFamily: "monospace", marginTop: 3 }}>
              UPDATED: {bracket.lastScrape ? new Date(bracket.lastScrape).toLocaleString() : bracket.lastUpdated ? new Date(bracket.lastUpdated).toLocaleString() : "N/A"}
              {bracket.scrapeSource && <span> &#183; {bracket.scrapeSource}</span>}
              {bracket.scrapeStatus && <span style={{ color: bracket.scrapeStatus === "ok" ? "#27AE3D" : "#D97706", marginLeft: 4 }}> &#183; {bracket.scrapeStatus.toUpperCase()}</span>}
            </div>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <div style={{ background: "#212844", border: "1px solid #3a3f5c", borderRadius: 4, padding: "3px 10px", textAlign: "center" }}>
              <div style={{ fontSize: 20, fontWeight: 800, color: "#27AE3D", fontFamily: "monospace" }}>{totalComplete}<span style={{ fontSize: 14, color: "#bfbfbf" }}>/32</span></div>
              <div style={{ fontSize: 12, color: "#bfbfbf", fontFamily: "monospace", letterSpacing: "0.08em" }}>R1 DONE</div>
            </div>
            <div style={{ background: "#212844", border: "1px solid #3a3f5c", borderRadius: 4, padding: "3px 10px", textAlign: "center" }}>
              <div style={{ fontSize: 20, fontWeight: 800, color: "#D97706", fontFamily: "monospace" }}>{cupsetCount}</div>
              <div style={{ fontSize: 12, color: "#bfbfbf", fontFamily: "monospace", letterSpacing: "0.08em" }}>CUPSETS</div>
            </div>
          </div>
        </div>

        {/* Toggle for mobile */}
        <button onClick={() => setHeaderExpanded(e => !e)} style={{
          background: "transparent", border: "1px solid #3a3f5c", borderRadius: 3,
          padding: "4px 12px", cursor: "pointer", marginTop: 8,
          color: "#bfbfbf", fontSize: 12, fontWeight: 700, fontFamily: "monospace",
        }}>{headerExpanded ? "Hide Controls" : "Show Legend & Zoom"}</button>

        {headerExpanded && <>
          {/* Tier Legend */}
          <div style={{ display: "flex", gap: 10, marginTop: 8, flexWrap: "wrap" }}>
            {Object.entries(TIERS).map(([key, t]) => {
              const info = {
                MLS: { name: "Major League Soccer", url: "https://www.mlssoccer.com" },
                "USL-C": { name: "USL Championship", url: "https://www.uslchampionship.com" },
                USL1: { name: "USL League One", url: "https://www.uslleagueone.com" },
                MLSNP: { name: "MLS Next Pro", url: "https://www.mlsnextpro.com" },
                USL2: { name: "USL League Two", url: "https://www.uslleaguetwo.com" },
                AM: { name: "Amateur", url: null },
              }[key];
              return (
                <div key={key} style={{ display: "flex", alignItems: "center", gap: 3 }}>
                  <span style={{ fontSize: 12, fontWeight: 700, padding: "1px 5px", borderRadius: 3, color: t.color, background: t.bg, fontFamily: "monospace" }}>{t.label}</span>
                  {info.url ? (
                    <a href={info.url} target="_blank" rel="noopener noreferrer"
                      style={{ fontSize: 13, color: "#ddd", textDecoration: "none", borderBottom: "1px dashed #ffffff33" }}>{info.name}</a>
                  ) : (
                    <span style={{ fontSize: 13, color: "#ddd" }}>{info.name}</span>
                  )}
                </div>
              );
            })}
          </div>

          {/* Zoom Controls */}
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 10, flexWrap: "wrap" }}>
            <span style={{ fontSize: 13, color: "#bfbfbf", fontFamily: "monospace", letterSpacing: "0.1em" }}>ZOOM</span>
            <input type="range" min={30} max={200} value={Math.round(zoom * 100)}
              onChange={e => setZoom(Number(e.target.value) / 100)}
              style={{ width: 100, accentColor: "#C2002F", height: 4, cursor: "pointer" }} />
            <span style={{ fontSize: 14, fontFamily: "monospace", color: "#fff", minWidth: 36 }}>{Math.round(zoom * 100)}%</span>
            <div style={{ display: "flex", gap: 3, marginLeft: 4 }}>
              {zoomPresets.map(p => (
                <button key={p.label} onClick={() => setZoom(p.val)} style={{
                  background: Math.abs(zoom - p.val) < 0.05 ? "#C2002F" : "transparent",
                  border: Math.abs(zoom - p.val) < 0.05 ? "1px solid #C2002F" : "1px solid #3a3f5c",
                  borderRadius: 3, padding: "2px 7px", cursor: "pointer",
                  color: Math.abs(zoom - p.val) < 0.05 ? "#fff" : "#bfbfbf",
                  fontSize: 12, fontWeight: 700, fontFamily: "monospace",
                }}>{p.label}</button>
              ))}
            </div>
            <span style={{ fontSize: 12, color: "#999", fontFamily: "monospace", marginLeft: 8 }}>Ctrl+Scroll or Pinch to zoom</span>
          </div>
        </>}
      </div>

      {/* BRACKET */}
      <div ref={bracketRef} style={isMobile ? { userSelect: "none", background: "#eaeaea" } : { overflowX: "auto", overflowY: "hidden", WebkitOverflowScrolling: "touch", cursor: "grab", userSelect: "none", background: "#eaeaea" }}>
        <div style={{
          width: `${(svgW + 40) * zoom}px`,
        }}>
        <div style={{
          transform: `scale(${zoom})`, transformOrigin: "top left",
          width: `${svgW + 40}px`,
          padding: "0 20px",
        }}>
          {/* Round Column Headers */}
          <div style={{ display: "flex", paddingTop: 10, paddingBottom: 4 }}>
            {RNAMES.map((r, i) => (
              <div key={i} style={{ width: ROUND_SIZES[i].cw, marginLeft: i === 0 ? 0 : HG, textAlign: "center", flexShrink: 0 }}>
                <div style={{ fontSize: 14, fontWeight: 800, color: i === 0 ? "#C2002F" : "#15192B", letterSpacing: "0.12em", fontFamily: "monospace" }}>{r.name}</div>
                <div style={{ fontSize: 12, color: "#777", fontFamily: "monospace" }}>{r.sub}</div>
              </div>
            ))}
            <div style={{ width: FINAL_SIZE.cw, marginLeft: HG, textAlign: "center", flexShrink: 0 }}>
              <div style={{ fontSize: 14, fontWeight: 800, color: "#C2002F", letterSpacing: "0.12em", fontFamily: "monospace" }}>FINAL</div>
              <div style={{ fontSize: 12, color: "#777", fontFamily: "monospace" }}>Oct 21</div>
            </div>
          </div>

          <svg width={svgW} height={totalH} style={{ display: "block" }}>

            {/* Upper Bracket */}
            <DrawConns conns={topB.conns} />
            <DrawRounds rounds={topB.rounds} />
            <text x={4} y={regionH + 8} fill="#15192B" fontSize={10} fontFamily="monospace" fontWeight={700} letterSpacing="0.12em">UPPER BRACKET</text>

            {/* Divider */}
            <line x1={0} y1={regionH + dividerGap / 2} x2={colX(5) + semiSz.cw + 10} y2={regionH + dividerGap / 2}
              stroke="#c0c0c0" strokeWidth={1} strokeDasharray="6,4" opacity={0.6} />

            {/* Lower Bracket */}
            <g transform={`translate(0,${botOffset})`}>
              <DrawConns conns={botB.conns} />
              <DrawRounds rounds={botB.rounds} />
            </g>
            <text x={4} y={botOffset - 8} fill="#15192B" fontSize={10} fontFamily="monospace" fontWeight={700} letterSpacing="0.12em">LOWER BRACKET</text>

            {/* Upper Semi -> Final */}
            <path d={`M${topSemi ? topSemi.x + semiSz.cw : colX(5) + semiSz.cw},${topSemiMidY} H${finalX - 16} V${finalY + FINAL_SIZE.ch * 0.35} H${finalX}`}
              fill="none" stroke="#C2002F66" strokeWidth={1.5} strokeLinecap="round" />

            {/* Lower Semi -> Final */}
            <path d={`M${botSemi ? botSemi.x + semiSz.cw : colX(5) + semiSz.cw},${botSemiMidY} H${finalX - 16} V${finalY + FINAL_SIZE.ch * 0.65} H${finalX}`}
              fill="none" stroke="#C2002F66" strokeWidth={1.5} strokeLinecap="round" />

            {/* Labels on converging lines */}
            <text x={finalX - 20} y={finalY + FINAL_SIZE.ch * 0.35 - 5} textAnchor="end" fill="#C2002F88" fontSize={10} fontFamily="monospace">UPPER</text>
            <text x={finalX - 20} y={finalY + FINAL_SIZE.ch * 0.65 + 10} textAnchor="end" fill="#C2002F88" fontSize={10} fontFamily="monospace">LOWER</text>

            {/* Final Box */}
            <Cell match={null} x={finalX} y={finalY} roundIdx={6} isChamp />

            {/* Trophy */}
            <text x={finalX + FINAL_SIZE.cw / 2} y={finalY - 12} textAnchor="middle" fontSize={26}>&#127942;</text>
          </svg>
        </div>
        </div>
      </div>

      {/* FOOTER */}
      <div style={{
        borderTop: "1px solid #e0e0e0", padding: "10px 20px",
        display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 8,
        background: "#f7f7f7"
      }}>
        <div style={{ display: "flex", gap: 16, alignItems: "center", flexWrap: "wrap" }}>
          <span style={{ fontSize: 13, color: "#555", fontFamily: "monospace" }}>
            PENDING: {pendingMatch ? `${pendingMatch.home} vs ${pendingMatch.away} (${pendingMatch.note})` : "All R1 Complete"}
          </span>
          <span style={{ fontSize: 13, color: "#555", fontFamily: "monospace" }}>
            NEXT: Second Round Draw TBD
          </span>
        </div>
        <span style={{ fontSize: 12, color: "#777", fontFamily: "monospace" }}>
          Data: ESPN &#183; ussoccer.com &#183; usopencup.welchproductsllc.com
        </span>
      </div>

      {/* SCRAPE STATUS */}
      {bracket.lastScrape && (
        <div style={{
          borderTop: "1px solid #e0e0e0", padding: "8px 20px",
          background: "#f0f0f0", display: "flex", flexWrap: "wrap", gap: 12, alignItems: "center"
        }}>
          <span style={{ fontSize: 12, fontFamily: "monospace", color: "#777" }}>
            LAST SCRAPE: {new Date(bracket.lastScrape).toLocaleString()}
          </span>
          {bracket.scrapeSource && (
            <span style={{ fontSize: 12, fontFamily: "monospace", color: "#777" }}>
              SOURCE: {bracket.scrapeSource}
            </span>
          )}
          <span style={{ fontSize: 12, fontFamily: "monospace",
            color: bracket.scrapeStatus === "ok" ? "#27AE3D" : bracket.scrapeStatus === "stale" ? "#D97706" : "#C2002F"
          }}>
            STATUS: {bracket.scrapeStatus?.toUpperCase()}
          </span>
          {bracket.sourceResults && (
            <span style={{ fontSize: 11, fontFamily: "monospace", color: "#777" }}>
              {bracket.sourceResults.map(s => (
                <span key={s.name} style={{
                  marginRight: 8,
                  color: s.status === "ok" ? "#27AE3D" : s.status === "no_data" ? "#D97706" : "#C2002F"
                }}>
                  {s.name}: {s.status === "ok" ? `${s.matches} matches` : s.status}
                </span>
              ))}
            </span>
          )}
        </div>
      )}

      {/* SEO CONTENT */}
      <article style={{ borderTop: "1px solid #1a3a2a", padding: "24px 20px", background: "#f7f7f7", maxWidth: 900 }}>
        <h2 style={{ fontSize: 20, fontWeight: 700, color: "#15192B", marginBottom: 12 }}>
          2026 Lamar Hunt U.S. Open Cup Bracket & Results
        </h2>
        <p style={{ fontSize: 15, color: "#555", lineHeight: 1.7, marginBottom: 12 }}>
          The 111th edition of the Lamar Hunt U.S. Open Cup is the oldest ongoing soccer competition in the United States,
          open to all levels of men's soccer from Major League Soccer clubs to amateur and semi-professional teams.
          The 2026 tournament features 80 teams competing in a single-elimination format across seven rounds,
          from the First Round in March through the Final on October 21, with a $1 million prize purse.
        </p>
        <h3 style={{ fontSize: 16, fontWeight: 700, color: "#212844", marginBottom: 8 }}>Tournament Format</h3>
        <p style={{ fontSize: 15, color: "#555", lineHeight: 1.7, marginBottom: 12 }}>
          The First Round (March 17-19) features 48 professional teams from USL Championship, USL League One,
          and MLS NEXT Pro alongside 32 amateur qualifiers from leagues including USL League Two, UPSL, NPSL, and regional associations.
          The 32 First Round winners advance to the Second Round (March 31 - April 1),
          and the 16 Second Round winners are joined by 16 MLS teams entering in the Round of 32 (April 14-15).
          The tournament continues through the Round of 16, Quarterfinals, Semifinals, and the Final.
        </p>
        <h3 style={{ fontSize: 16, fontWeight: 700, color: "#212844", marginBottom: 8 }}>First Round Highlights</h3>
        <p style={{ fontSize: 15, color: "#555", lineHeight: 1.7, marginBottom: 12 }}>
          The 2026 First Round delivered dramatic results and memorable cupsets across 32 matches.
          Lexington SC recorded the largest margin of victory with a 9-0 demolition of Flower City Union.
          Union Omaha dominated BOHFS St. Louis 8-0, while San Antonio FC cruised past ASC New Stars 6-0.
          Amateur sides Valley 559 FC, Virginia Dream FC, Flint City Bucks, and Tennessee Tempo FC all pulled off cupsets
          against higher-division opponents, continuing the tradition of giant-killing that makes the Open Cup
          one of the most exciting tournaments in American soccer.
        </p>
        <h3 style={{ fontSize: 16, fontWeight: 700, color: "#212844", marginBottom: 8 }}>About This Bracket Tracker</h3>
        <p style={{ fontSize: 15, color: "#555", lineHeight: 1.7, marginBottom: 0 }}>
          This interactive bracket displays live scores and results for every round of the 2026 U.S. Open Cup.
          Teams are color-coded by league tier: MLS, USL Championship, USL League One, MLS NEXT Pro, USL League Two, and Amateur.
          Matches marked as cupsets indicate a lower-tier team defeating a higher-tier opponent.
          The bracket updates automatically with the latest results from{" "}
          <a href="https://www.ussoccer.com/us-open-cup/schedule" target="_blank" rel="noopener noreferrer"
            style={{ color: "#15192B" }}>ussoccer.com</a>.
        </p>
      </article>

      {/* HOW IT WORKS */}
      <section style={{ borderTop: "1px solid #1a3a2a", padding: "24px 20px", background: "#f7f7f7" }}>
        <h2 style={{ fontSize: 20, fontWeight: 700, color: "#15192B", marginBottom: 16 }}>
          How This Website Works
        </h2>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 14 }}>
          {/* ARCHITECTURE */}
          <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 6, padding: 16 }}>
            <div style={{ fontSize: 12, fontWeight: 800, color: "#C2002F", fontFamily: "monospace", letterSpacing: "0.12em", marginBottom: 8 }}>ARCHITECTURE</div>
            <p style={{ fontSize: 15, color: "#555", lineHeight: 1.7, margin: 0 }}>
              Full-stack single-page application with a <strong style={{ color: "#15192B" }}>Python/Flask</strong> backend
              and <strong style={{ color: "#15192B" }}>React 18</strong> frontend bundled with <strong style={{ color: "#15192B" }}>Vite</strong>.
              Flask serves both the REST API and the static production build as a single process.
              No database needed - tournament state lives in a single JSON file that the scraper updates and the API serves directly.
            </p>
          </div>

          {/* LIVE DATA PIPELINE */}
          <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 6, padding: 16 }}>
            <div style={{ fontSize: 12, fontWeight: 800, color: "#C2002F", fontFamily: "monospace", letterSpacing: "0.12em", marginBottom: 8 }}>LIVE DATA PIPELINE</div>
            <p style={{ fontSize: 15, color: "#555", lineHeight: 1.7, margin: 0 }}>
              Scores update automatically through a triple-redundant pipeline.{" "}
              <strong style={{ color: "#15192B" }}>Primary:</strong> ESPN public scoreboard API, queried by date range per round.{" "}
              <strong style={{ color: "#15192B" }}>Backup:</strong> Wikipedia API, parsing structured wikitext football box templates.{" "}
              <strong style={{ color: "#15192B" }}>Fallback:</strong> Direct scraping of ussoccer.com with BeautifulSoup.
              Existing data is never overwritten with fewer matches. APScheduler runs every 2 hours, increasing to every 30 minutes
              during game windows (6 PM - midnight ET). The frontend polls every 5 minutes.
              Per-source health status is tracked and displayed on every scrape cycle.
            </p>
          </div>

          {/* BRACKET RENDERING */}
          <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 6, padding: 16 }}>
            <div style={{ fontSize: 12, fontWeight: 800, color: "#C2002F", fontFamily: "monospace", letterSpacing: "0.12em", marginBottom: 8 }}>BRACKET RENDERING</div>
            <p style={{ fontSize: 15, color: "#555", lineHeight: 1.7, margin: 0 }}>
              The NCAA-style bracket is rendered as <strong style={{ color: "#15192B" }}>SVG</strong> with{" "}
              <strong style={{ color: "#15192B" }}>foreignObject</strong> elements for rich HTML match cells.
              Upper and lower brackets are computed independently with L-shaped connector paths joining rounds.
              Cell sizes, fonts, and badge sizes scale progressively from 11px in the First Round up to 16px in the Final.
              Winners propagate forward automatically, and cupset detection compares tier rankings to flag lower-division upsets.
            </p>
          </div>

          {/* INTERACTION */}
          <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 6, padding: 16 }}>
            <div style={{ fontSize: 12, fontWeight: 800, color: "#C2002F", fontFamily: "monospace", letterSpacing: "0.12em", marginBottom: 8 }}>INTERACTION</div>
            <p style={{ fontSize: 15, color: "#555", lineHeight: 1.7, margin: 0 }}>
              Click-and-drag panning on desktop via mouse events bound to the scroll container.
              Pinch-to-zoom on touch devices and Ctrl+Scroll wheel zoom on desktop.
              Zoom is implemented via CSS <code style={{ color: "#15192B", fontSize: 14 }}>transform: scale()</code> with
              presets from 55% (Fit) to 200% (XXL). Six tier-colored badges classify all 80 teams by league,
              with links to each league's official website in the legend.
            </p>
          </div>

          {/* DEPLOYMENT */}
          <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 6, padding: 16 }}>
            <div style={{ fontSize: 12, fontWeight: 800, color: "#C2002F", fontFamily: "monospace", letterSpacing: "0.12em", marginBottom: 8 }}>DEPLOYMENT</div>
            <p style={{ fontSize: 15, color: "#555", lineHeight: 1.7, margin: 0 }}>
              Containerized in a <strong style={{ color: "#15192B" }}>multi-stage Docker</strong> build: Node 20 compiles
              the React frontend, then Python 3.11 serves it via <strong style={{ color: "#15192B" }}>Gunicorn</strong>.
              Deployed on <strong style={{ color: "#15192B" }}>Railway</strong> with automatic deploys from{" "}
              <code style={{ color: "#15192B", fontSize: 14 }}>main</code>.
              Health checks hit <code style={{ color: "#15192B", fontSize: 14 }}>/api/health</code>.
              SEO includes Open Graph, Twitter Cards, JSON-LD structured data, FAQ schema, and semantic HTML content.
            </p>
          </div>

          {/* MONITORING */}
          <div style={{ background: "#fff", border: "1px solid #e0e0e0", borderRadius: 6, padding: 16 }}>
            <div style={{ fontSize: 12, fontWeight: 800, color: "#C2002F", fontFamily: "monospace", letterSpacing: "0.12em", marginBottom: 8 }}>MONITORING</div>
            <p style={{ fontSize: 15, color: "#555", lineHeight: 1.7, margin: 0 }}>
              Every scrape cycle tests all three data sources independently and records per-source status
              (success with match count, no data, or error). Results are saved to the data file and displayed
              on the page with color-coded health indicators. When 2 or more sources fail,
              a <strong style={{ color: "#15192B" }}>Slack</strong> alert fires to the ops channel with failure details.
              Manual scrape and test-alert API endpoints allow on-demand diagnostics without redeploying.
            </p>
          </div>
        </div>

        {/* Tech Stack Badges */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 16 }}>
          {["Python 3.11", "Flask", "Gunicorn", "APScheduler", "BeautifulSoup", "React 18", "Vite", "SVG/foreignObject", "Docker", "Railway", "ESPN API", "Wikipedia API", "Slack Webhooks"].map(t => (
            <span key={t} style={{ fontSize: 13, fontWeight: 700, padding: "3px 10px", borderRadius: 3,
              color: "#C2002F", background: "#C2002F0a", border: "1px solid #C2002F25", fontFamily: "monospace" }}>{t}</span>
          ))}
        </div>

        {/* Open Source */}
        <p style={{ fontSize: 15, color: "#555", lineHeight: 1.7, marginTop: 14, marginBottom: 0 }}>
          <strong style={{ color: "#15192B" }}>Open Source</strong> - The full source code is available at{" "}
          <a href="https://github.com/ToddWelch/US-Open-Cup-Bracket" target="_blank" rel="noopener noreferrer"
            style={{ color: "#15192B", textDecoration: "none", borderBottom: "1px dashed #8acca044" }}>
            github.com/ToddWelch/US-Open-Cup-Bracket</a>.
        </p>
      </section>

      {/* BUILT BY */}
      <div style={{ borderTop: "1px solid #e0e0e0", padding: "16px 20px", background: "#15192B", textAlign: "center" }}>
        <p style={{ fontSize: 15, color: "#bfbfbf", lineHeight: 1.6, margin: 0 }}>
          This site was designed and built entirely by{" "}
          <a href="https://claude.ai/code" target="_blank" rel="noopener noreferrer"
            style={{ color: "#ddd", textDecoration: "none", borderBottom: "1px dashed #ffffff44" }}>Claude Code</a>
          {" "}(AI), prompted by{" "}
          <a href="https://welchcommercesystems.com" target="_blank" rel="noopener noreferrer"
            style={{ color: "#fff", textDecoration: "none", fontWeight: 700, borderBottom: "1px dashed #ffffff44" }}>Welch Commerce Systems</a>.
        </p>
        <p style={{ fontSize: 14, color: "#999", marginTop: 6, marginBottom: 0 }}>
          Want an AI-built app like this for your business?{" "}
          <a href="https://welchcommercesystems.com" target="_blank" rel="noopener noreferrer"
            style={{ color: "#ddd", textDecoration: "none", borderBottom: "1px solid #ffffff44" }}>
            Let's talk AI assisted automation &amp; development
          </a>
        </p>
      </div>
    </div>
  );
}
