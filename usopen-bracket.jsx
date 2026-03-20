import { useState, useRef, useEffect, useCallback } from "react";

/* ═══════════ TIER SYSTEM ═══════════ */
const TIERS = {
  MLS:    { label: "MLS",  color: "#C41E3A", bg: "#C41E3A22" },
  "USL-C":{ label: "USLC", color: "#4A90D9", bg: "#4A90D922" },
  USL1:   { label: "USL1", color: "#2D7D4F", bg: "#2D7D4F22" },
  MLSNP:  { label: "NP",   color: "#8B5CF6", bg: "#8B5CF622" },
  USL2:   { label: "USL2", color: "#E08A2C", bg: "#E08A2C22" },
  AM:     { label: "AM",   color: "#9CA3AF", bg: "#9CA3AF22" },
};
const MLS_L=["Atlanta United","Austin FC","Charlotte FC","Chicago Fire FC","Colorado Rapids","Columbus Crew","D.C. United","Houston Dynamo FC","Minnesota United FC","New England Revolution","New York City FC","Orlando City SC","Red Bull New York","San Jose Earthquakes","Sporting Kansas City","St. Louis CITY SC"];
const USLC_L=["Charleston Battery","Detroit City FC","Hartford Athletic","Indy Eleven","Loudoun United FC","Louisville City FC","Pittsburgh Riverhounds SC","Rhode Island FC","Colorado Springs Switchbacks FC","El Paso Locomotive FC","FC Tulsa","Lexington SC","New Mexico United","Orange County SC","Phoenix Rising FC","Sacramento Republic FC","San Antonio FC"];
const USL1_L=["AV ALTA FC","Charlotte Independence","Chattanooga Red Wolves SC","FC Naples","Forward Madison FC","Greenville Triumph SC","One Knoxville SC","Portland Hearts of Pine","Richmond Kickers","Spokane Velocity FC","Union Omaha","Westchester SC"];
const MLSNP_L=["Carolina Core FC","Chattanooga FC"];
const USL2_L=["Vermont Green FC","Flint City Bucks","Steel City FC","Ventura County Fusion","Des Moines Menace","Northern Virginia FC","Asheville City SC","Flower City Union","West Chester United SC"];
function getTier(t){if(!t)return null;if(MLS_L.some(m=>t.includes(m)||m.includes(t)))return"MLS";if(USLC_L.some(m=>t.includes(m)||m.includes(t)))return"USL-C";if(USL1_L.some(m=>t.includes(m)||m.includes(t)))return"USL1";if(MLSNP_L.some(m=>t===m))return"MLSNP";if(USL2_L.some(m=>t.includes(m)||m.includes(t)))return"USL2";return"AM";}
function getWinner(m){if(m.homeScore==null||m.awayScore==null)return null;return m.homeScore>m.awayScore?m.home:m.away;}

/* ═══════════ DATA ═══════════ */
const R1=[
  {home:"Richmond Kickers",away:"Northern Virginia FC",homeScore:2,awayScore:0},
  {home:"Rhode Island FC",away:"CD Faialense",homeScore:4,awayScore:0},
  {home:"Vermont Green FC",away:"Portland Hearts of Pine",homeScore:1,awayScore:0},
  {home:"Detroit City FC",away:"Michigan Rangers",homeScore:5,awayScore:1},
  {home:"West Chester United SC",away:"Loudoun United FC",homeScore:1,awayScore:2},
  {home:"Colorado Springs Switchbacks FC",away:"Azteca FC",homeScore:3,awayScore:0},
  {home:"Indy Eleven",away:"Des Moines Menace",homeScore:3,awayScore:0},
  {home:"Phoenix Rising FC",away:"San Ramon FC",homeScore:4,awayScore:0},
  {home:"Chattanooga FC",away:"Kalonji Pro-Profile",homeScore:2,awayScore:1},
  {home:"Asheville City SC",away:"Greenville Triumph SC",homeScore:3,awayScore:1},
  {home:"Charleston Battery",away:"Badgers FC",homeScore:2,awayScore:1},
  {home:"Louisville City FC",away:"Southern Indiana FC",homeScore:2,awayScore:0},
  {home:"FC Naples",away:"Red Force",homeScore:3,awayScore:0},
  {home:"FC Motown",away:"Hartford Athletic",homeScore:0,awayScore:2},
  {home:"SC Vistula Garfield",away:"One Knoxville SC",homeScore:1,awayScore:3},
  {home:"BOHFS St. Louis",away:"Union Omaha",homeScore:0,awayScore:8},
  {home:"Little Rock Rangers",away:"FC Tulsa",homeScore:2,awayScore:4},
  {home:"San Antonio FC",away:"ASC New Stars",homeScore:6,awayScore:0},
  {home:"New Mexico United",away:"Cruizers FC",homeScore:3,awayScore:2},
  {home:"Sacramento Republic FC",away:"El Farolito",homeScore:2,awayScore:0,note:"AET"},
  {home:"AV ALTA FC",away:"Valley 559 FC",homeScore:0,awayScore:1},
  {home:"Ventura County Fusion",away:"Spokane Velocity FC",homeScore:1,awayScore:2},
  {home:"Orange County SC",away:"Laguna United FC",homeScore:3,awayScore:0},
  {home:"Carolina Core FC",away:"Virginia Dream FC",homeScore:1,awayScore:2},
  {home:"Charlotte Independence",away:"Ristozi FC",homeScore:4,awayScore:1},
  {home:"Flint City Bucks",away:"Forward Madison FC",homeScore:2,awayScore:0},
  {home:"Lexington SC",away:"Flower City Union",homeScore:9,awayScore:0},
  {home:"Westchester SC",away:"NY Renegades FC",homeScore:2,awayScore:0},
  {home:"Laredo Heat",away:"El Paso Locomotive FC",homeScore:0,awayScore:2},
  {home:"Tennessee Tempo FC",away:"Chattanooga Red Wolves SC",homeScore:1,awayScore:0},
  {home:"Pittsburgh Riverhounds SC",away:"Steel City FC",homeScore:null,awayScore:null,note:"Mar 25"},
  {home:"FC America CFL Spurs",away:"South Georgia Tormenta FC",homeScore:1,awayScore:0,note:"FF"},
];

/* ═══════════ PROGRESSIVE SIZING PER ROUND ═══════════ */
// roundIndex: 0=R1, 1=R2, 2=R32, 3=R16, 4=QF, 5=SF
// Font: 10 -> 11 -> 11 -> 12 -> 13 -> 13 -> 14 (final)
// Badge: 7 -> 7 -> 8 -> 8 -> 9 -> 9 -> 10
// Cell W: 172 -> 176 -> 180 -> 186 -> 192 -> 198
// Cell H: 36 -> 38 -> 38 -> 40 -> 42 -> 44
const ROUND_SIZES = [
  { font: 10, badge: 7,  cw: 172, ch: 36 },  // R1
  { font: 11, badge: 7,  cw: 176, ch: 38 },  // R2
  { font: 11, badge: 8,  cw: 180, ch: 38 },  // R32
  { font: 12, badge: 8,  cw: 186, ch: 40 },  // R16
  { font: 13, badge: 9,  cw: 192, ch: 42 },  // QF
  { font: 13, badge: 9,  cw: 198, ch: 44 },  // SF
];
const FINAL_SIZE = { font: 14, badge: 10, cw: 210, ch: 56 };
const HG = 30;
const VG = 4;

// Compute column X positions (cumulative widths + gaps)
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
  const bw = isChamp ? sz.cw : sz.cw;
  const bh = isChamp ? sz.ch : sz.ch;
  const m = match || {home:null,away:null,homeScore:null,awayScore:null};
  const win = getWinner(m);
  const headerH = isChamp ? 18 : 0;
  const rowH = (bh - headerH) / 2;

  const row = (name, score, won, isTop) => {
    const tbd = !name;
    const dn = isMls && tbd && isTop ? "MLS Team" : isMls && tbd && !isTop ? "R2 Winner" : name || "TBD";
    return (
      <div style={{display:"flex",alignItems:"center",height:rowH,
        background:won?"#102e1c":"transparent",
        borderTop:isTop?"none":"1px solid #162a20",
        paddingLeft:5,paddingRight:5,gap:3}}>
        {name && <TierBadge team={name} size={sz.badge}/>}
        <span style={{flex:1,fontSize:sz.font,fontWeight:won?700:400,
          whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis",
          color:tbd?"#2e4e3e":won?"#4ade80":"#7ea892",
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
      <div style={{width:bw,height:bh,
        border:`1px solid ${isChamp?"#4ade8060":win?"#2a5a3a":"#162a20"}`,
        borderRadius:isChamp?6:3,overflow:"hidden",
        background:isChamp?"#0e2418":"#0c1812",
        boxShadow:isChamp?"0 0 24px #4ade8018":"none"}}>
        {isChamp && (
          <div style={{textAlign:"center",fontSize:9,fontWeight:800,color:"#4ade80",
            letterSpacing:"0.18em",fontFamily:"monospace",padding:"2px 0",height:headerH,
            display:"flex",alignItems:"center",justifyContent:"center",
            background:"linear-gradient(90deg,#0a1e14,#122e1e,#0a1e14)",
            borderBottom:"1px solid #1a3a2a"}}>FINAL &bull; OCT 21</div>
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

  // R1
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
        cur.push({ x: cx, y: newY, match: null, roundIdx: rIdx });
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

/* ═══════════ MAIN APP ═══════════ */
export default function App() {
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
  const amUpsets = R1.filter(m => { const w = getWinner(m); if (!w) return false; const t = getTier(w); return t === "AM" || t === "USL2"; }).length;
  const pendingMatch = R1.find(m => m.homeScore == null);

  const bracketRef = useRef(null);
  const [zoom, setZoom] = useZoom(bracketRef, 1.0);

  const zoomPresets = [
    { label: "Fit", val: 0.55 },
    { label: "S", val: 0.7 },
    { label: "M", val: 0.85 },
    { label: "L", val: 1.0 },
    { label: "XL", val: 1.3 },
  ];

  return (
    <div style={{ background: "#070f0b", minHeight: "100vh", color: "#c0d8cc", fontFamily: "'Segoe UI',system-ui,sans-serif" }}>

      {/* ── HEADER ── */}
      <div style={{ borderBottom: "1px solid #1a3a2a", padding: "14px 20px 12px",
        background: "linear-gradient(180deg,#0e2118 0%,#070f0b 100%)" }}>
        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
          <div>
            <h1 style={{ margin: 0, fontSize: 21, fontWeight: 800, color: "#e8f5ee", letterSpacing: "-0.02em" }}>
              <span style={{ color: "#4ade80" }}>2026</span> Lamar Hunt U.S. Open Cup
            </h1>
            <div style={{ fontSize: 9, color: "#3e6e4e", fontFamily: "monospace", marginTop: 2, letterSpacing: "0.1em" }}>
              111TH EDITION &bull; 80 TEAMS &bull; 7 ROUNDS &bull; $1M PURSE
            </div>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <div style={{ background: "#0c1812", border: "1px solid #1a3a2a", borderRadius: 4, padding: "3px 10px", textAlign: "center" }}>
              <div style={{ fontSize: 15, fontWeight: 800, color: "#4ade80", fontFamily: "monospace" }}>{totalComplete}<span style={{ fontSize: 9, color: "#3e6e4e" }}>/32</span></div>
              <div style={{ fontSize: 7, color: "#3e6e4e", fontFamily: "monospace", letterSpacing: "0.08em" }}>R1 DONE</div>
            </div>
            <div style={{ background: "#0c1812", border: "1px solid #1a3a2a", borderRadius: 4, padding: "3px 10px", textAlign: "center" }}>
              <div style={{ fontSize: 15, fontWeight: 800, color: "#E08A2C", fontFamily: "monospace" }}>{amUpsets}</div>
              <div style={{ fontSize: 7, color: "#3e6e4e", fontFamily: "monospace", letterSpacing: "0.08em" }}>UPSETS</div>
            </div>
          </div>
        </div>

        {/* Tier Legend */}
        <div style={{ display: "flex", gap: 10, marginTop: 8, flexWrap: "wrap" }}>
          {Object.entries(TIERS).map(([key, t]) => (
            <div key={key} style={{ display: "flex", alignItems: "center", gap: 3 }}>
              <span style={{ fontSize: 7, fontWeight: 700, padding: "0 3px", borderRadius: 2, color: t.color, background: t.bg, fontFamily: "monospace", border: `1px solid ${t.color}25` }}>{t.label}</span>
              <span style={{ fontSize: 8, color: "#4a7a5a" }}>{key === "MLS" ? "Major League Soccer" : key === "USL-C" ? "USL Championship" : key === "USL1" ? "USL League One" : key === "MLSNP" ? "MLS Next Pro" : key === "USL2" ? "USL League Two" : "Amateur"}</span>
            </div>
          ))}
        </div>

        {/* Zoom Controls */}
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 10 }}>
          <span style={{ fontSize: 8, color: "#3e6e4e", fontFamily: "monospace", letterSpacing: "0.1em" }}>ZOOM</span>
          <input type="range" min={30} max={200} value={Math.round(zoom * 100)}
            onChange={e => setZoom(Number(e.target.value) / 100)}
            style={{ width: 100, accentColor: "#4ade80", height: 4, cursor: "pointer" }} />
          <span style={{ fontSize: 9, fontFamily: "monospace", color: "#4ade80", minWidth: 36 }}>{Math.round(zoom * 100)}%</span>
          <div style={{ display: "flex", gap: 3, marginLeft: 4 }}>
            {zoomPresets.map(p => (
              <button key={p.label} onClick={() => setZoom(p.val)} style={{
                background: Math.abs(zoom - p.val) < 0.05 ? "#4ade8018" : "transparent",
                border: Math.abs(zoom - p.val) < 0.05 ? "1px solid #4ade8040" : "1px solid #1a3a2a",
                borderRadius: 3, padding: "2px 7px", cursor: "pointer",
                color: Math.abs(zoom - p.val) < 0.05 ? "#4ade80" : "#3e6e4e",
                fontSize: 8, fontWeight: 700, fontFamily: "monospace",
              }}>{p.label}</button>
            ))}
          </div>
          <span style={{ fontSize: 7, color: "#2a4a3a", fontFamily: "monospace", marginLeft: 8 }}>Ctrl+Scroll or Pinch to zoom</span>
        </div>
      </div>

      {/* ── BRACKET ── */}
      <div ref={bracketRef} style={{ overflowX: "auto", overflowY: "auto", WebkitOverflowScrolling: "touch", cursor: "grab" }}>
        <div style={{
          transform: `scale(${zoom})`, transformOrigin: "top left",
          minWidth: svgW, padding: "0 20px",
          width: `${svgW + 40}px`,
        }}>
          {/* Round Column Headers */}
          <div style={{ display: "flex", paddingTop: 10, paddingBottom: 4 }}>
            {RNAMES.map((r, i) => (
              <div key={i} style={{ width: ROUND_SIZES[i].cw, marginLeft: i === 0 ? 0 : HG, textAlign: "center", flexShrink: 0 }}>
                <div style={{ fontSize: 8, fontWeight: 800, color: i === 0 ? "#4ade80" : "#2e5e3e", letterSpacing: "0.12em", fontFamily: "monospace" }}>{r.name}</div>
                <div style={{ fontSize: 7, color: "#2a4a3a", fontFamily: "monospace" }}>{r.sub}</div>
              </div>
            ))}
            <div style={{ width: FINAL_SIZE.cw, marginLeft: HG, textAlign: "center", flexShrink: 0 }}>
              <div style={{ fontSize: 8, fontWeight: 800, color: "#4ade80", letterSpacing: "0.12em", fontFamily: "monospace" }}>FINAL</div>
              <div style={{ fontSize: 7, color: "#2a4a3a", fontFamily: "monospace" }}>Oct 21</div>
            </div>
          </div>

          <svg width={svgW} height={totalH} style={{ display: "block" }}>

            {/* Upper Bracket */}
            <DrawConns conns={topB.conns} />
            <DrawRounds rounds={topB.rounds} />
            <text x={4} y={regionH + 8} fill="#1e3e2e" fontSize={8} fontFamily="monospace" fontWeight={700} letterSpacing="0.12em">UPPER BRACKET</text>

            {/* Divider */}
            <line x1={0} y1={regionH + dividerGap / 2} x2={colX(5) + semiSz.cw + 10} y2={regionH + dividerGap / 2}
              stroke="#1a3a2a" strokeWidth={1} strokeDasharray="6,4" opacity={0.6} />

            {/* Lower Bracket */}
            <g transform={`translate(0,${botOffset})`}>
              <DrawConns conns={botB.conns} />
              <DrawRounds rounds={botB.rounds} />
            </g>
            <text x={4} y={botOffset - 8} fill="#1e3e2e" fontSize={8} fontFamily="monospace" fontWeight={700} letterSpacing="0.12em">LOWER BRACKET</text>

            {/* Upper Semi -> Final */}
            <path d={`M${topSemi ? topSemi.x + semiSz.cw : colX(5) + semiSz.cw},${topSemiMidY} H${finalX - 16} V${finalY + FINAL_SIZE.ch * 0.35} H${finalX}`}
              fill="none" stroke="#4ade8040" strokeWidth={1.5} strokeLinecap="round" />

            {/* Lower Semi -> Final */}
            <path d={`M${botSemi ? botSemi.x + semiSz.cw : colX(5) + semiSz.cw},${botSemiMidY} H${finalX - 16} V${finalY + FINAL_SIZE.ch * 0.65} H${finalX}`}
              fill="none" stroke="#4ade8040" strokeWidth={1.5} strokeLinecap="round" />

            {/* Labels on converging lines */}
            <text x={finalX - 20} y={finalY + FINAL_SIZE.ch * 0.35 - 5} textAnchor="end" fill="#4ade8044" fontSize={6} fontFamily="monospace">UPPER</text>
            <text x={finalX - 20} y={finalY + FINAL_SIZE.ch * 0.65 + 10} textAnchor="end" fill="#4ade8044" fontSize={6} fontFamily="monospace">LOWER</text>

            {/* Final Box */}
            <Cell match={null} x={finalX} y={finalY} roundIdx={6} isChamp />

            {/* Trophy */}
            <text x={finalX + FINAL_SIZE.cw / 2} y={finalY - 12} textAnchor="middle" fontSize={26}>🏆</text>
          </svg>
        </div>
      </div>

      {/* ── FOOTER ── */}
      <div style={{
        borderTop: "1px solid #1a3a2a", padding: "10px 20px",
        display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 8,
        background: "#0a1610"
      }}>
        <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
          <span style={{ fontSize: 9, color: "#2e5e3e", fontFamily: "monospace" }}>
            PENDING: {pendingMatch ? `${pendingMatch.home} vs ${pendingMatch.away} (${pendingMatch.note})` : "All R1 Complete"}
          </span>
          <span style={{ fontSize: 9, color: "#2e5e3e", fontFamily: "monospace" }}>
            NEXT: Second Round Draw TBD
          </span>
        </div>
        <span style={{ fontSize: 8, color: "#1e3e2e", fontFamily: "monospace" }}>
          Source: ussoccer.com &bull; welchproductsllc.com
        </span>
      </div>
    </div>
  );
}
