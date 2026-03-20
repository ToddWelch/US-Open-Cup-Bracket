# Welch Commerce Systems - Dark Green Design System

Use this as a reference when applying the shared design language across Welch Commerce projects (US Open Cup Bracket, Pro Wrestling TV Ratings Tracker, etc.).

## Color Palette

```
Page background:       #070f0b
Header gradient:       linear-gradient(180deg, #0e2118 0%, #070f0b 100%)
Card/panel background: #0c1812
Footer background:     #0a1610
Bottom bar background: #080e0a

Borders:
  Normal:              #1a3a2a
  Highlighted:         #2a5a3a
  Divider (dashed):    #1a3a2a, strokeDasharray="6,4"

Primary accent:        #4ade80  (bright green - used for key numbers, active states, highlights)
Text colors:
  Headline:            #e8f5ee
  Body/primary:        #c0d8cc
  Secondary/labels:    #8acca0
  Tertiary/muted:      #7aba8a
  Subtle/hint:         #6a9a7a
  Links:               #8acca0 with border-bottom: 1px dashed #8acca044
  Link (CTA/bold):     #4ade80, fontWeight: 700, border-bottom: 1px dashed #4ade8044

Scrollbar:
  Track:               #0a1610
  Thumb:               #1a3a2a
  Thumb hover:         #2a5a3a
```

## Typography

```
Font family:           'Segoe UI', system-ui, sans-serif
Monospace:             monospace (used for stats, labels, badges, data)

Font sizes (minimum 12px for all UI text):
  Page title (h1):     21px, fontWeight: 800, letterSpacing: -0.02em
  Subtitle/tagline:    14px, monospace, letterSpacing: 0.1em
  Section headers:     16px, fontWeight: 700
  Subheaders (h3):     14px, fontWeight: 700
  Stat numbers:        20px, fontWeight: 800, monospace
  Stat labels:         12px, monospace, letterSpacing: 0.08em
  Stat suffix (/32):   14px
  Badge text:          12px, fontWeight: 700, monospace
  Badge description:   13px
  Controls/zoom:       13px label, 14px value, 12px buttons, 12px hint
  Body text:           13px, lineHeight: 1.7
  Footer text:         13px (primary), 12px (secondary)
  Source/credit:       12px, monospace
  Column headers:      14px, fontWeight: 800, monospace, letterSpacing: 0.12em
  Column subtitles:    12px, monospace
```

## Badge/Tag Style

```
fontSize:      12px (in header legend) or scaled per context
fontWeight:    700
padding:       1px 5px
borderRadius:  2px
fontFamily:    monospace
color:         [tier/category color - bright version]
background:    [tier/category color + "44" alpha for ~27% opacity]
border:        1px solid [tier/category color + "25" alpha]
```

## Buttons (e.g. zoom presets)

```
Active:
  background:    #4ade8018
  border:        1px solid #4ade8040
  color:         #4ade80

Inactive:
  background:    transparent
  border:        1px solid #1a3a2a
  color:         #8acca0

Shared:
  borderRadius:  3px
  padding:       2px 7px
  fontSize:      12px
  fontWeight:    700
  fontFamily:    monospace
  cursor:        pointer
```

## Card/Panel Style

```
background:    #0c1812
border:        1px solid #1a3a2a (normal) or #2a5a3a (highlighted/winner)
borderRadius:  3px (small) or 6px (featured)
boxShadow:     none (normal) or 0 0 24px #4ade8018 (featured)
```

## Global CSS Reset

```css
*, *::before, *::after {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  background: #070f0b;
  color: #c0d8cc;
  font-family: 'Segoe UI', system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
}

::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: #0a1610; }
::-webkit-scrollbar-thumb { background: #1a3a2a; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #2a5a3a; }
```

## Footer: Welch Commerce Systems Credit

Use this exact footer at the bottom of every Welch Commerce project.

### React/JSX version:

```jsx
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
```

### Plain HTML version:

```html
<!-- BUILT BY -->
<div style="border-top: 1px solid #1a3a2a; padding: 16px 20px; background: #080e0a; text-align: center;">
  <p style="font-size: 13px; color: #6a9a7a; line-height: 1.6; margin: 0;">
    This site was designed and built entirely by
    <a href="https://claude.ai/code" target="_blank" rel="noopener noreferrer"
      style="color: #8acca0; text-decoration: none; border-bottom: 1px dashed #8acca044;">Claude Code</a>
    (AI), prompted by
    <a href="https://welchcommercesystems.com" target="_blank" rel="noopener noreferrer"
      style="color: #4ade80; text-decoration: none; font-weight: 700; border-bottom: 1px dashed #4ade8044;">Welch Commerce Systems</a>.
  </p>
  <p style="font-size: 12px; color: #5a8a6a; margin-top: 6px; margin-bottom: 0;">
    Want an AI-built app like this for your business?
    <a href="https://welchcommercesystems.com" target="_blank" rel="noopener noreferrer"
      style="color: #8acca0; text-decoration: none; border-bottom: 1px solid #8acca066;">
      Let's talk AI assisted automation &amp; development
    </a>
  </p>
</div>
```
