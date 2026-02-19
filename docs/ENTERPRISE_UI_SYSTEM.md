# Enterprise UI System (Fleet Management)

Target: SAP / Oracle / Microsoft internal tools vibe — calm, compact, audit-ready.

## Phase 1 — Design System Definition

### 1) Color System

Principles:
- Neutral-first UI (grays) + one strong brand blue.
- Surfaces clearly separated from background via border + subtle shadow.
- States readable (WCAG-ish contrast) without neon.

```css
:root{
  /* Brand */
  --fm-primary-50:  #EEF4FF;
  --fm-primary-100: #DCE8FF;
  --fm-primary-200: #BBD3FF;
  --fm-primary-300: #8FB5FF;
  --fm-primary-400: #5C8DFF;
  --fm-primary-500: #2F63F6; /* Primary */
  --fm-primary-600: #2352D8;
  --fm-primary-700: #1F45B3;

  /* Neutrals */
  --fm-bg:         #F4F6F9;  /* App background */
  --fm-surface:    #FFFFFF;  /* Cards, panels */
  --fm-surface-2:  #FBFCFE;  /* Raised/alt surface */
  --fm-border:     #D9DEE7;
  --fm-border-2:   #E7EBF2;
  --fm-text:       #0B1220;
  --fm-muted:      #5A667A;
  --fm-muted-2:    #77839A;

  /* Sidebar */
  --fm-sidebar-bg: #0E1728;
  --fm-sidebar-text:#D7DEEA;
  --fm-sidebar-muted:#9AA6BA;
  --fm-sidebar-border: rgba(255,255,255,.08);
  --fm-sidebar-active-bg: rgba(47,99,246,.16);
  --fm-sidebar-hover-bg: rgba(255,255,255,.06);

  /* States */
  --fm-success: #15803D;
  --fm-success-bg: rgba(21,128,61,.12);
  --fm-warning: #B45309;
  --fm-warning-bg: rgba(180,83,9,.14);
  --fm-danger:  #B91C1C;
  --fm-danger-bg: rgba(185,28,28,.12);
  --fm-info:    #0369A1;
  --fm-info-bg: rgba(3,105,161,.12);

  /* Hover + stripes */
  --fm-hover: rgba(11,18,32,.04);
  --fm-table-stripe: rgba(11,18,32,.02);
}
```

### 2) Typography Scale (compact, enterprise)

```css
:root{
  --fm-font-sans: Inter, system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif;

  --fm-h1: 1.45rem; /* 23px */
  --fm-h2: 1.20rem; /* 19px */
  --fm-h3: 1.05rem; /* 17px */

  --fm-section-title: .92rem; /* 14.7px */
  --fm-label: .80rem;         /* 12.8px */
  --fm-body: .92rem;          /* 14.7px */
  --fm-table: .88rem;         /* 14px */
  --fm-muted-size: .82rem;    /* 13px */

  --fm-leading: 1.35;
}
```

Rules:
- Page title = H1, subtitle muted.
- Labels small + semi-bold; inputs compact.
- Table text slightly smaller than body.

### 3) Spacing System (8px grid)

```css
:root{
  --fm-1: 4px;
  --fm-2: 8px;
  --fm-3: 12px;
  --fm-4: 16px;
  --fm-5: 20px;
  --fm-6: 24px;
  --fm-7: 32px;
  --fm-8: 40px;
}
```

### 4) Shadow Levels (subtle)

```css
:root{
  --fm-shadow-0: none;
  --fm-shadow-1: 0 1px 2px rgba(11,18,32,.06);
  --fm-shadow-2: 0 6px 18px rgba(11,18,32,.08);
  --fm-shadow-3: 0 12px 30px rgba(11,18,32,.10);
}
```

### 5) Radius Scale (serious, not cartoon)

```css
:root{
  --fm-radius-1: 8px;
  --fm-radius-2: 10px;
  --fm-radius-3: 12px;
}
```

### 6) Button hierarchy

- Primary: solid blue (submit/apply)
- Secondary: outline neutral (cancel/reset)
- Ghost: no border (inline actions)
- Danger: solid/outline red (destructive)

### 7) Form inputs

- Height: compact (approx 36px)
- Border 1px, focus ring blue (subtle)
- Required fields: label includes * (optional)

### 8) Table standard

- Sticky header
- Compact rows
- Zebra striping light
- Hover highlight
- Numeric columns right-aligned

### 9) Card standard

- White surface, border, small shadow
- Header uses muted title + right actions

### 10) Status badge system

- Pills with background tint, readable text, consistent sizing.

## Phase 2+ Implementation Notes

- Use macros for: page header, toolbar, export cards, badges.
- Keep routes/endpoint names unchanged (UI only).

## Tailwind (optional suggestion)

If later moving to Tailwind: keep tokens above as CSS variables and map via `theme.extend.colors` (but not required now).
