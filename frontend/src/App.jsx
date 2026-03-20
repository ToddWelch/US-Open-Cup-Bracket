import { useState, useRef, useEffect, useCallback } from "react";

/* ═══════════ TIER SYSTEM ═══════════ */
const TIERS = {
  MLS:    { label: "MLS",  color: "#ff6b6b", bg: "#C41E3A44" },
  "USL-C":{ label: "USLC", color: "#6ab0ff", bg: "#4A90D944" },
  USL1:   { label: "USL1", color: "#5ece7a", bg: "#2D7D4F44" },
  MLSNP:  { label: "NP",   color: "#a78bfa", bg: "#8B5CF644" },
  USL2:   { label: "USL2", color: "#f0a850", bg: "#E08A2C44" },
  AM:     { label: "AM",   color: "#c0c8d0", bg: "#9CA3AF44" },
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
const VG = 4;

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
  return <span style={{fontSize:size||7,fontWeight:700,padding:"0 3px",borderRadius:2,color:t.color,background:t.bg,fontFamily:"monospace",lineHeight:`${(size||7)+6}px`,flexShrink:0,border:`1px solid ${t.color}25`}}>{t.label}</span>;
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
        background:won?"#102e1c":"transparent",
        borderTop:isTop?"none":"1px solid #162a20",
        borderLeft:won?"2px solid #4ade80":"2px solid transparent",
        paddingLeft:5,paddingRight:5,gap:3}}>
        {name && <TierBadge team={name} size={sz.badge}/>}
        <span style={{flex:1,fontSize:sz.font,fontWeight:won?700:400,
          whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis",
          color:tbd?"#7aba8a":won?"#4ade80":"#9ecaae",
          fontStyle:tbd?"italic":"normal"}}>{dn}</span>
        {m.note && isTop && <span style={{fontSize:Math.max(6, sz.badge-1),color:"#4ade8066",fontFamily:"monospace"}}>{m.note}</span>}
        <span style={{fontSize:sz.font,fontWeight:700,minWidth:14,textAlign:"right",
          fontFamily:"monospace",
          color:won?"#4ade80":score!=null?"#4a7a5a":"#1e3e2e"}}>{score!=null?score:""}</span>
      </div>
    );
  };

  return (
    <foreignObject x={x} y={y} width={bw} height={bh}>
      <div style={{width:bw,height:bh,position:"relative",
        border:`1px solid ${cupset?"#E08A2C88":isChamp?"#4ade8060":win?"#2a5a3a":"#162a20"}`,
        borderRadius:isChamp?6:3,overflow:"hidden",
        background:isChamp?"#0e2418":"#0c1812",
        boxShadow:cupset?"0 0 8px #E08A2C22":isChamp?"0 0 24px #4ade8018":"none"}}>
        {cupset && <span style={{position:"absolute",top:-1,right:3,fontSize:Math.max(7,sz.badge-2),fontWeight:800,color:"#E08A2C",fontFamily:"monospace",letterSpacing:"0.05em"}}>CUPSET</span>}
        {isChamp && (
          <div style={{textAlign:"center",fontSize:9,fontWeight:800,color:"#4ade80",
            letterSpacing:"0.18em",fontFamily:"monospace",padding:"2px 0",height:headerH,
            display:"flex",alignItems:"center",justifyContent:"center",
            background:"linear-gradient(90deg,#0a1e14,#122e1e,#0a1e14)",
            borderBottom:"1px solid #1a3a2a"}}>FINAL &#183; OCT 21</div>
        )}
        {row(m.home,m.homeScore,win===m.home,true)}
        {row(m.away,m.awayScore,win===m.away,false)}
      </div>
    </foreignObject>
  );
}

/* ═══════════ BRACKET BUILDER ═══════════ */
function buildRegion(matches, padTop) {
  const rounds = [];
  const conns = [];

  const r1sz = ROUND_SIZES[0];
  const r1 = matches.map((m, i) => ({
    x: colX(0), y: padTop + i * (r1sz.ch + VG), match: m, roundIdx: 0
  }));
  rounds.push(r1);

  let prev = r1;
  for (let rIdx = 1; rIdx <= 5; rIdx++) {
    const sz = ROUND_SIZES[rIdx];
    const prevSz = ROUND_SIZES[rIdx - 1];
    const isMls = rIdx === 2;
    const cur = [];
    const cx = colX(rIdx);

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
        const newY = midY - sz.ch / 2;
        // Propagate winners from previous round into this round's matchup
        const w1 = p1.match ? getWinner(p1.match) : null;
        const w2 = p2?.match ? getWinner(p2.match) : null;
        const advMatch = (w1 || w2) ? { home: w1 || null, away: w2 || null, homeScore: null, awayScore: null } : null;
        cur.push({ x: cx, y: newY, match: advMatch, roundIdx: rIdx });
        conns.push({ x1: p1.x + pSz.cw, y1: p1mid, x2: cx, y2: midY });
        if (p2) conns.push({ x1: p2.x + pSz.cw, y1: p2mid, x2: cx, y2: midY });
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
      fill="none" stroke="#1a3a2a" strokeWidth={1} />;
  });
}

function DrawRounds({ rounds }) {
  return rounds.map((round, ri) => round.map((s, mi) => (
    <Cell key={`${ri}-${mi}`} match={s.match} x={s.x} y={s.y}
      roundIdx={s.roundIdx} isMls={s.isMls} />
  )));
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
    const interval = setInterval(fetchBracket, 5 * 60 * 1000);
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
  const topB = buildRegion(topR1, 8);
  const botB = buildRegion(botR1, 8);

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
    <div style={{ background: "#070f0b", minHeight: "100vh", color: "#c0d8cc", fontFamily: "'Segoe UI',system-ui,sans-serif" }}>

      {/* HEADER */}
      <div style={{ borderBottom: "1px solid #1a3a2a", padding: "14px 20px 12px",
        background: "linear-gradient(180deg,#0e2118 0%,#070f0b 100%)" }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 21, fontWeight: 800, color: "#e8f5ee", letterSpacing: "-0.02em" }}>
              <span style={{ color: "#4ade80" }}>2026</span>{" "}
              <a href="https://www.ussoccer.com/us-open-cup" target="_blank" rel="noopener noreferrer"
                style={{ color: "#e8f5ee", textDecoration: "none", borderBottom: "1px dashed #4ade8066" }}>
                Lamar Hunt U.S. Open Cup
              </a>
            </h1>
            <div style={{ fontSize: 14, color: "#8acca0", fontFamily: "monospace", marginTop: 2, letterSpacing: "0.1em" }}>
              111TH EDITION &#183; 80 TEAMS &#183; 7 ROUNDS &#183; $1M PURSE
            </div>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <div style={{ background: "#0c1812", border: "1px solid #1a3a2a", borderRadius: 4, padding: "3px 10px", textAlign: "center" }}>
              <div style={{ fontSize: 20, fontWeight: 800, color: "#4ade80", fontFamily: "monospace" }}>{totalComplete}<span style={{ fontSize: 14, color: "#8acca0" }}>/32</span></div>
              <div style={{ fontSize: 12, color: "#8acca0", fontFamily: "monospace", letterSpacing: "0.08em" }}>R1 DONE</div>
            </div>
            <div style={{ background: "#0c1812", border: "1px solid #1a3a2a", borderRadius: 4, padding: "3px 10px", textAlign: "center" }}>
              <div style={{ fontSize: 20, fontWeight: 800, color: "#E08A2C", fontFamily: "monospace" }}>{cupsetCount}</div>
              <div style={{ fontSize: 12, color: "#8acca0", fontFamily: "monospace", letterSpacing: "0.08em" }}>CUPSETS</div>
            </div>
          </div>
        </div>

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
                <span style={{ fontSize: 12, fontWeight: 700, padding: "1px 5px", borderRadius: 2, color: t.color, background: t.bg, fontFamily: "monospace", border: `1px solid ${t.color}25` }}>{t.label}</span>
                {info.url ? (
                  <a href={info.url} target="_blank" rel="noopener noreferrer"
                    style={{ fontSize: 13, color: "#8acca0", textDecoration: "none", borderBottom: "1px dashed #8acca044" }}>{info.name}</a>
                ) : (
                  <span style={{ fontSize: 13, color: "#8acca0" }}>{info.name}</span>
                )}
              </div>
            );
          })}
        </div>

        {/* Zoom Controls */}
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 10 }}>
          <span style={{ fontSize: 13, color: "#8acca0", fontFamily: "monospace", letterSpacing: "0.1em" }}>ZOOM</span>
          <input type="range" min={30} max={200} value={Math.round(zoom * 100)}
            onChange={e => setZoom(Number(e.target.value) / 100)}
            style={{ width: 100, accentColor: "#4ade80", height: 4, cursor: "pointer" }} />
          <span style={{ fontSize: 14, fontFamily: "monospace", color: "#4ade80", minWidth: 36 }}>{Math.round(zoom * 100)}%</span>
          <div style={{ display: "flex", gap: 3, marginLeft: 4 }}>
            {zoomPresets.map(p => (
              <button key={p.label} onClick={() => setZoom(p.val)} style={{
                background: Math.abs(zoom - p.val) < 0.05 ? "#4ade8018" : "transparent",
                border: Math.abs(zoom - p.val) < 0.05 ? "1px solid #4ade8040" : "1px solid #1a3a2a",
                borderRadius: 3, padding: "2px 7px", cursor: "pointer",
                color: Math.abs(zoom - p.val) < 0.05 ? "#4ade80" : "#3e6e4e",
                fontSize: 12, fontWeight: 700, fontFamily: "monospace",
              }}>{p.label}</button>
            ))}
          </div>
          <span style={{ fontSize: 12, color: "#8acca0", fontFamily: "monospace", marginLeft: 8 }}>Ctrl+Scroll or Pinch to zoom</span>
        </div>
      </div>

      {/* BRACKET */}
      <div ref={bracketRef} style={{ overflowX: "auto", overflowY: "auto", WebkitOverflowScrolling: "touch", cursor: "grab", userSelect: "none" }}>
        <div style={{
          transform: `scale(${zoom})`, transformOrigin: "top left",
          minWidth: svgW, padding: "0 20px",
          width: `${svgW + 40}px`,
        }}>
          {/* Round Column Headers */}
          <div style={{ display: "flex", paddingTop: 10, paddingBottom: 4 }}>
            {RNAMES.map((r, i) => (
              <div key={i} style={{ width: ROUND_SIZES[i].cw, marginLeft: i === 0 ? 0 : HG, textAlign: "center", flexShrink: 0 }}>
                <div style={{ fontSize: 14, fontWeight: 800, color: i === 0 ? "#4ade80" : "#8acca0", letterSpacing: "0.12em", fontFamily: "monospace" }}>{r.name}</div>
                <div style={{ fontSize: 12, color: "#7aba8a", fontFamily: "monospace" }}>{r.sub}</div>
              </div>
            ))}
            <div style={{ width: FINAL_SIZE.cw, marginLeft: HG, textAlign: "center", flexShrink: 0 }}>
              <div style={{ fontSize: 14, fontWeight: 800, color: "#4ade80", letterSpacing: "0.12em", fontFamily: "monospace" }}>FINAL</div>
              <div style={{ fontSize: 12, color: "#7aba8a", fontFamily: "monospace" }}>Oct 21</div>
            </div>
          </div>

          <svg width={svgW} height={totalH} style={{ display: "block" }}>

            {/* Upper Bracket */}
            <DrawConns conns={topB.conns} />
            <DrawRounds rounds={topB.rounds} />
            <text x={4} y={regionH + 8} fill="#8acca0" fontSize={10} fontFamily="monospace" fontWeight={700} letterSpacing="0.12em">UPPER BRACKET</text>

            {/* Divider */}
            <line x1={0} y1={regionH + dividerGap / 2} x2={colX(5) + semiSz.cw + 10} y2={regionH + dividerGap / 2}
              stroke="#1a3a2a" strokeWidth={1} strokeDasharray="6,4" opacity={0.6} />

            {/* Lower Bracket */}
            <g transform={`translate(0,${botOffset})`}>
              <DrawConns conns={botB.conns} />
              <DrawRounds rounds={botB.rounds} />
            </g>
            <text x={4} y={botOffset - 8} fill="#8acca0" fontSize={10} fontFamily="monospace" fontWeight={700} letterSpacing="0.12em">LOWER BRACKET</text>

            {/* Upper Semi -> Final */}
            <path d={`M${topSemi ? topSemi.x + semiSz.cw : colX(5) + semiSz.cw},${topSemiMidY} H${finalX - 16} V${finalY + FINAL_SIZE.ch * 0.35} H${finalX}`}
              fill="none" stroke="#4ade8040" strokeWidth={1.5} strokeLinecap="round" />

            {/* Lower Semi -> Final */}
            <path d={`M${botSemi ? botSemi.x + semiSz.cw : colX(5) + semiSz.cw},${botSemiMidY} H${finalX - 16} V${finalY + FINAL_SIZE.ch * 0.65} H${finalX}`}
              fill="none" stroke="#4ade8040" strokeWidth={1.5} strokeLinecap="round" />

            {/* Labels on converging lines */}
            <text x={finalX - 20} y={finalY + FINAL_SIZE.ch * 0.35 - 5} textAnchor="end" fill="#4ade8088" fontSize={10} fontFamily="monospace">UPPER</text>
            <text x={finalX - 20} y={finalY + FINAL_SIZE.ch * 0.65 + 10} textAnchor="end" fill="#4ade8088" fontSize={10} fontFamily="monospace">LOWER</text>

            {/* Final Box */}
            <Cell match={null} x={finalX} y={finalY} roundIdx={6} isChamp />

            {/* Trophy */}
            <text x={finalX + FINAL_SIZE.cw / 2} y={finalY - 12} textAnchor="middle" fontSize={26}>&#127942;</text>
          </svg>
        </div>
      </div>

      {/* FOOTER */}
      <div style={{
        borderTop: "1px solid #1a3a2a", padding: "10px 20px",
        display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 8,
        background: "#0a1610"
      }}>
        <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
          <span style={{ fontSize: 13, color: "#8acca0", fontFamily: "monospace" }}>
            PENDING: {pendingMatch ? `${pendingMatch.home} vs ${pendingMatch.away} (${pendingMatch.note})` : "All R1 Complete"}
          </span>
          <span style={{ fontSize: 13, color: "#8acca0", fontFamily: "monospace" }}>
            NEXT: Second Round Draw TBD
          </span>
        </div>
        <span style={{ fontSize: 12, color: "#8acca0", fontFamily: "monospace" }}>
          Data: ESPN &#183; ussoccer.com &#183; usopencup.welchproductsllc.com
        </span>
      </div>

      {/* SEO CONTENT */}
      <article style={{ borderTop: "1px solid #1a3a2a", padding: "24px 20px", background: "#0a1610", maxWidth: 900 }}>
        <h2 style={{ fontSize: 16, fontWeight: 700, color: "#8acca0", marginBottom: 12 }}>
          2026 Lamar Hunt U.S. Open Cup Bracket & Results
        </h2>
        <p style={{ fontSize: 13, color: "#6a9a7a", lineHeight: 1.7, marginBottom: 12 }}>
          The 111th edition of the Lamar Hunt U.S. Open Cup is the oldest ongoing soccer competition in the United States,
          open to all levels of men's soccer from Major League Soccer clubs to amateur and semi-professional teams.
          The 2026 tournament features 80 teams competing in a single-elimination format across seven rounds,
          from the First Round in March through the Final on October 21, with a $1 million prize purse.
        </p>
        <h3 style={{ fontSize: 14, fontWeight: 700, color: "#7aba8a", marginBottom: 8 }}>Tournament Format</h3>
        <p style={{ fontSize: 13, color: "#6a9a7a", lineHeight: 1.7, marginBottom: 12 }}>
          The First Round (March 17-19) features 48 professional teams from USL Championship, USL League One,
          and MLS NEXT Pro alongside 32 amateur qualifiers from leagues including USL League Two, UPSL, NPSL, and regional associations.
          The 32 First Round winners advance to the Second Round (March 31 - April 1),
          and the 16 Second Round winners are joined by 16 MLS teams entering in the Round of 32 (April 14-15).
          The tournament continues through the Round of 16, Quarterfinals, Semifinals, and the Final.
        </p>
        <h3 style={{ fontSize: 14, fontWeight: 700, color: "#7aba8a", marginBottom: 8 }}>First Round Highlights</h3>
        <p style={{ fontSize: 13, color: "#6a9a7a", lineHeight: 1.7, marginBottom: 12 }}>
          The 2026 First Round delivered dramatic results and memorable cupsets across 32 matches.
          Lexington SC recorded the largest margin of victory with a 9-0 demolition of Flower City Union.
          Union Omaha dominated BOHFS St. Louis 8-0, while San Antonio FC cruised past ASC New Stars 6-0.
          Amateur sides Valley 559 FC, Virginia Dream FC, Flint City Bucks, and Tennessee Tempo FC all pulled off cupsets
          against higher-division opponents, continuing the tradition of giant-killing that makes the Open Cup
          one of the most exciting tournaments in American soccer.
        </p>
        <h3 style={{ fontSize: 14, fontWeight: 700, color: "#7aba8a", marginBottom: 8 }}>About This Bracket Tracker</h3>
        <p style={{ fontSize: 13, color: "#6a9a7a", lineHeight: 1.7, marginBottom: 0 }}>
          This interactive bracket displays live scores and results for every round of the 2026 U.S. Open Cup.
          Teams are color-coded by league tier: MLS, USL Championship, USL League One, MLS NEXT Pro, USL League Two, and Amateur.
          Matches marked as cupsets indicate a lower-tier team defeating a higher-tier opponent.
          The bracket updates automatically with the latest results from{" "}
          <a href="https://www.ussoccer.com/us-open-cup/schedule" target="_blank" rel="noopener noreferrer"
            style={{ color: "#8acca0" }}>ussoccer.com</a>.
        </p>
      </article>

      {/* HOW IT WORKS */}
      <article style={{ borderTop: "1px solid #1a3a2a", padding: "24px 20px", background: "#0a1610", maxWidth: 900 }}>
        <h2 style={{ fontSize: 16, fontWeight: 700, color: "#8acca0", marginBottom: 14 }}>
          How This Website Works
        </h2>

        <h3 style={{ fontSize: 14, fontWeight: 700, color: "#7aba8a", marginBottom: 6 }}>Architecture</h3>
        <p style={{ fontSize: 13, color: "#6a9a7a", lineHeight: 1.7, marginBottom: 12 }}>
          This is a full-stack single-page application built with a{" "}
          <strong style={{ color: "#8acca0" }}>Python/Flask</strong> backend and a{" "}
          <strong style={{ color: "#8acca0" }}>React</strong> frontend bundled with{" "}
          <strong style={{ color: "#8acca0" }}>Vite</strong>.
          Flask serves both the REST API and the static production build as a single process.
          No database is needed. Tournament state is stored in a single JSON file that the scraper
          updates and the API serves directly.
        </p>

        <h3 style={{ fontSize: 14, fontWeight: 700, color: "#7aba8a", marginBottom: 6 }}>Live Data Pipeline</h3>
        <p style={{ fontSize: 13, color: "#6a9a7a", lineHeight: 1.7, marginBottom: 12 }}>
          Scores update automatically through a multi-source data pipeline with built-in redundancy:
        </p>
        <ul style={{ fontSize: 13, color: "#6a9a7a", lineHeight: 1.8, marginBottom: 12, paddingLeft: 20 }}>
          <li><strong style={{ color: "#8acca0" }}>Primary:</strong> ESPN public scoreboard API, queried by date range per round</li>
          <li><strong style={{ color: "#8acca0" }}>Backup:</strong> Wikipedia API, parsing structured wikitext football box templates</li>
          <li><strong style={{ color: "#8acca0" }}>Fallback:</strong> Direct scraping of ussoccer.com with BeautifulSoup</li>
          <li><strong style={{ color: "#8acca0" }}>Safety net:</strong> Existing data is never overwritten with fewer matches</li>
        </ul>
        <p style={{ fontSize: 13, color: "#6a9a7a", lineHeight: 1.7, marginBottom: 12 }}>
          An <strong style={{ color: "#8acca0" }}>APScheduler</strong> cron runs the pipeline every 2 hours by default,
          increasing to every 30 minutes during game windows (6 PM - midnight ET).
          The frontend polls the API every 5 minutes and re-renders when new data arrives.
        </p>

        <h3 style={{ fontSize: 14, fontWeight: 700, color: "#7aba8a", marginBottom: 6 }}>Bracket Rendering</h3>
        <p style={{ fontSize: 13, color: "#6a9a7a", lineHeight: 1.7, marginBottom: 12 }}>
          The bracket is rendered as an{" "}
          <strong style={{ color: "#8acca0" }}>SVG</strong> with{" "}
          <strong style={{ color: "#8acca0" }}>foreignObject</strong> elements for HTML match cells.
          Upper and lower brackets are computed independently, with L-shaped connector paths joining rounds.
          Cell sizes, fonts, and badge sizes scale progressively from 11px in the First Round up to 16px in the Final.
          Winners propagate forward automatically, so completed rounds populate the next round's matchups.
          Cupset detection compares tier rankings and flags when a lower-division team defeats a higher-division opponent.
        </p>

        <h3 style={{ fontSize: 14, fontWeight: 700, color: "#7aba8a", marginBottom: 6 }}>Interaction</h3>
        <p style={{ fontSize: 13, color: "#6a9a7a", lineHeight: 1.7, marginBottom: 12 }}>
          The bracket supports click-and-drag panning on desktop (mouse events bound to the scroll container),
          pinch-to-zoom on touch devices, and Ctrl+Scroll wheel zoom.
          Zoom is implemented via CSS <code style={{ color: "#8acca0", fontSize: 12 }}>transform: scale()</code> on
          the bracket container, with presets from 55% (Fit) to 200% (XXL).
        </p>

        <h3 style={{ fontSize: 14, fontWeight: 700, color: "#7aba8a", marginBottom: 6 }}>Deployment</h3>
        <p style={{ fontSize: 13, color: "#6a9a7a", lineHeight: 1.7, marginBottom: 12 }}>
          The app is containerized in a{" "}
          <strong style={{ color: "#8acca0" }}>multi-stage Docker</strong> build: Node 20 compiles the React frontend,
          then Python 3.11 serves it via <strong style={{ color: "#8acca0" }}>Gunicorn</strong>.
          Deployed on <strong style={{ color: "#8acca0" }}>Railway</strong> with automatic deploys from the{" "}
          <code style={{ color: "#8acca0", fontSize: 12 }}>main</code> branch.
          Health checks hit <code style={{ color: "#8acca0", fontSize: 12 }}>/api/health</code>.
        </p>

        <h3 style={{ fontSize: 14, fontWeight: 700, color: "#7aba8a", marginBottom: 6 }}>Tech Stack</h3>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 12 }}>
          {["Python 3.11", "Flask", "Gunicorn", "APScheduler", "BeautifulSoup", "React 18", "Vite", "SVG/foreignObject", "Docker", "Railway", "ESPN API", "Wikipedia API"].map(t => (
            <span key={t} style={{ fontSize: 11, fontWeight: 700, padding: "2px 8px", borderRadius: 3,
              color: "#4ade80", background: "#4ade8012", border: "1px solid #4ade8025", fontFamily: "monospace" }}>{t}</span>
          ))}
        </div>

        <h3 style={{ fontSize: 14, fontWeight: 700, color: "#7aba8a", marginBottom: 6 }}>Open Source</h3>
        <p style={{ fontSize: 13, color: "#6a9a7a", lineHeight: 1.7, marginBottom: 0 }}>
          The full source code is available at{" "}
          <a href="https://github.com/ToddWelch/US-Open-Cup-Bracket" target="_blank" rel="noopener noreferrer"
            style={{ color: "#8acca0", textDecoration: "none", borderBottom: "1px dashed #8acca044" }}>
            github.com/ToddWelch/US-Open-Cup-Bracket</a>.
        </p>
      </article>

      {/* BUILT BY */}
      <div style={{ borderTop: "1px solid #1a3a2a", padding: "16px 20px", background: "#080e0a", textAlign: "center" }}>
        <p style={{ fontSize: 13, color: "#6a9a7a", lineHeight: 1.6, margin: 0 }}>
          This site was designed and built entirely by{" "}
          <a href="https://claude.ai/code" target="_blank" rel="noopener noreferrer"
            style={{ color: "#8acca0", textDecoration: "none", borderBottom: "1px dashed #8acca044" }}>Claude Code</a>
          {" "}(AI), prompted by{" "}
          <a href="https://welchcommercesystems.com" target="_blank" rel="noopener noreferrer"
            style={{ color: "#4ade80", textDecoration: "none", fontWeight: 700, borderBottom: "1px dashed #4ade8044" }}>Welch Commerce Systems</a>.
        </p>
        <p style={{ fontSize: 12, color: "#5a8a6a", marginTop: 6, marginBottom: 0 }}>
          Want an AI-built app like this for your business?{" "}
          <a href="https://welchcommercesystems.com" target="_blank" rel="noopener noreferrer"
            style={{ color: "#8acca0", textDecoration: "none", borderBottom: "1px solid #8acca066" }}>
            Let's talk AI assisted automation &amp; development
          </a>
        </p>
      </div>
    </div>
  );
}
