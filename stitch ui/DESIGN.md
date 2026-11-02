---
name: Groww AI Discovery Engine
colors:
  surface: '#10141a'
  surface-dim: '#10141a'
  surface-bright: '#353940'
  surface-container-lowest: '#0a0e14'
  surface-container-low: '#181c22'
  surface-container: '#1c2026'
  surface-container-high: '#262a31'
  surface-container-highest: '#31353c'
  on-surface: '#dfe2eb'
  on-surface-variant: '#bacac1'
  inverse-surface: '#dfe2eb'
  inverse-on-surface: '#2d3137'
  outline: '#85948c'
  outline-variant: '#3c4a43'
  surface-tint: '#2fe0aa'
  primary: '#44edb7'
  on-primary: '#003828'
  primary-container: '#00d09c'
  on-primary-container: '#00533c'
  inverse-primary: '#006c4f'
  secondary: '#bcc2ff'
  on-secondary: '#00179b'
  secondary-container: '#152ecf'
  on-secondary-container: '#aab3ff'
  tertiary: '#5eecaf'
  on-tertiary: '#003824'
  tertiary-container: '#3acf95'
  on-tertiary-container: '#005338'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#59fdc5'
  primary-fixed-dim: '#2fe0aa'
  on-primary-fixed: '#002116'
  on-primary-fixed-variant: '#00513b'
  secondary-fixed: '#dfe0ff'
  secondary-fixed-dim: '#bcc2ff'
  on-secondary-fixed: '#000b62'
  on-secondary-fixed-variant: '#102bcd'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#10141a'
  on-background: '#dfe2eb'
  surface-variant: '#31353c'
typography:
  headline-xl:
    fontFamily: Geist
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Geist
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Geist
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.005em
  body-lg:
    fontFamily: Geist
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 22px
  body-md:
    fontFamily: Geist
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 18px
  body-sm:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  metric-display:
    fontFamily: JetBrains Mono
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 34px
    letterSpacing: -0.03em
  metric-lg:
    fontFamily: JetBrains Mono
    fontSize: 20px
    fontWeight: '500'
    lineHeight: 26px
    letterSpacing: -0.02em
  metric-sm:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
    letterSpacing: -0.01em
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.04em
  label-xs:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '500'
    lineHeight: 12px
    letterSpacing: 0.06em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 0.75rem
  gutter-compact: 0.5rem
  margin: 1rem
  margin-compact: 0.75rem
  space-2xs: 0.125rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1rem
  space-xl: 1.5rem
---

## Brand & Style

The design system is crafted for high-density, mission-critical product analytics in wealth management. Built specifically for Senior Growth Product Managers and retention leads, the visual tone conveys institutional precision, predictive intelligence, and operational clarity. It merges high-contrast technical minimalism with modern developer-console ergonomics.

The visual narrative relies on focused information scent: dark obsidian bases allow automated cohort insights and real-time behavioral telemetry to pop with zero chromatic noise. The aesthetic bridges high-performance financial terminals and contemporary AI observability platforms—commanding, deterministic, and analytical.

## Colors

The palette is engineered specifically for deep-focus monitoring and cognitive ergonomics across long analysis sessions:

- **Canvas & Surface Architecture**: `#0D1117` provides a non-reflective, true-terminal backdrop. Cards and elevated control panels sit at `#161B22`, framed by crisp `#30363D` architectural strokes. Muted interactive states rest at `#21262D`.
- **Primary Brand Accelerator**: Groww Mint (`#00D09C`) anchors primary actions, key state changes, and core system telemetry.
- **Intelligence & Correlation**: Indigo Blue (`#5367FF`) indicates secondary actions, AI discovery flags, predictive modeling cues, and confidence scoring.
- **Behavioral Signal Mapping**:
  - **Continuers & Positive Drift**: Vibrant Green (`#10B981`) flags users actively continuing their SIP mandates.
  - **Friction & At-Risk Cohorts**: Amber (`#F59E0B`) highlights early churn signals, bank authorization delays, and payment retries.
  - **Critical Drop Triggers**: Coral Red (`#EF4444`) commands attention for immediate drop-offs, mandate cancellations, and negative conversion leaks.
- **Text & Numeric Hierarchy**: Pure White (`#F0F6FC`) for critical metrics and titles; Slate Gray (`#8B949E`) for tabular headers and metadata; Dim Muted (`#484F58`) for disabled or structural dividers.

## Typography

The typography couples the structural clarity of Geist for rapid textual ingestion with the technical precision of JetBrains Mono for telemetry, financial quantities, confidence intervals, and percentages. 

- **Geist** governs navigation, headers, cohort descriptions, and narrative discovery insights. Optical tracking stays tight (-0.01em to -0.02em) on all headlines to preserve dense spatial bounds.
- **JetBrains Mono** enforces tabular numeral alignment across dense tables, funnel node counters, and KPI scorecards, preventing eye fatigue during high-volume cohort scans. All currency symbols (`₹`), percentage changes (`+12.4%`), and probability thresholds are strictly rendered in mono.

## Layout & Spacing

A compact 12-column fluid workbench layout optimized for 1440px+ display environments, maintaining tight density without visual degradation:

- **Rhythm**: Built upon a strict 4px sub-grid with primary jumps scaled to 8px/12px/16px. Internal component padding stays within 8px–12px to maximize metric display area above the fold.
- **Workbench Multi-Pane Pattern**: Fixed 240px contextual left-rail for cohort filters and navigation, flanked by a fluid analytical grid. Metric summary bands, Sankey transition flows, and data grids sit adjacent within unified horizontal visual planes.
- **Responsive Condensation**: At lower viewports (<1024px), secondary telemetry trays collapse into slide-out drawers, retaining primary funnel conversion paths in full column spans.

## Elevation & Depth

Visual hierarchy abandons diffuse drop shadows in favor of crisp luminous boundaries, 1px perimeter outlines, and tonal stacking:

- **Level 0 (Canvas Base)**: `#0D1117` provides zero-depth canvas foundation.
- **Level 1 (Panels & Card Containers)**: `#161B22` background bounded by a sharp `1px solid #30363D` border. Surfaces convey strict architectural containment.
- **Level 2 (Active/Hover Cards)**: Surface rises to `#1C2128` with borders dynamically escalating to `rgba(255, 255, 255, 0.15)`. When highlighting active cohorts, border lines accent with subtle directional glow: `box-shadow: inset 0 1px 0 0 rgba(0, 208, 156, 0.3)`.
- **Level 3 (Modals, Slide-Overs & Popovers)**: `#21262D` surface with `1px solid #484F58` border and a deep, crisp containment shadow (`0 16px 32px rgba(1, 4, 9, 0.85)`).
- **Signal Tracers**: High-priority alert nodes and AI anomaly highlights utilize razor-thin glowing edge accents: `1px solid rgba(239, 68, 68, 0.5)` for drop risks and `1px solid rgba(0, 208, 156, 0.5)` for auto-continuation breakouts.

## Shapes

The design system adopts roundedness level `2`:
- **Cards & Data Modules**: Defined with `rounded-xl` (1.5rem / 24px on outer shells, trimmed to 12px–16px internally where micro-tables live) to soften large dashboard panes and create a polished, human-centered SaaS experience.
- **Buttons, Filter Pills, and Inputs**: Structured with 8px radius (`rounded-md` feel) for precise hit areas.
- **Status Tags & Micro Badges**: Built with 4px–6px radius to avoid pill sprawl and preserve strict tabular grid lines.

## Components

### Buttons
- **Primary (Action/Export)**: Solid `#00D09C` background, `#0D1117` text, font weight 600, 8px radius. Hover: `#00b889` with subtle inner highlight. Focus ring: `2px solid rgba(0, 208, 156, 0.4)`.
- **Secondary (Simulate Cohort)**: Solid `#5367FF` with white text, font weight 500, 8px radius. Hover: `#4256eb`.
- **Tertiary/Ghost**: Transparent with `1px solid #30363D`, `#C9D1D9` text. Hover: `#21262D` surface with `#F0F6FC` text.

### KPI Cards & Metric Tiles
- **Structure**: `#161B22` background, `rounded-xl` container, `1px solid #30363D`. Header shows cohort title in `label-md` uppercase gray, accompanied by mini AI prediction chips.
- **Metric Presentation**: Primary integer in `metric-display`, accompanied by contextual inline delta tags (`+4.2% MoM` in `#10B981` or `-18.1% drop-off` in `#EF4444`).

### Cohort Chips & Flow Indicators
- **Continuers**: Background `rgba(16, 185, 129, 0.12)`, text `#10B981`, border `1px solid rgba(16, 185, 129, 0.3)`.
- **At-Risk / Warning**: Background `rgba(245, 158, 11, 0.12)`, text `#F59E0B`, border `1px solid rgba(245, 158, 11, 0.3)`.
- **Critical Leaks**: Background `rgba(239, 68, 68, 0.12)`, text `#EF4444`, border `1px solid rgba(239, 68, 68, 0.3)`.
- **AI Suggested Intervention**: Background `rgba(83, 103, 255, 0.12)`, text `#5367FF`, border `1px solid rgba(83, 103, 255, 0.3)`.

### Tabular Lists & Cohort Breakdown Grids
- **Header**: `#0D1117` background with uppercase `label-xs` typography, `#8B949E` text, and zero divider bleed.
- **Rows**: Alternating hover highlights (`#1C2128`), height 36px for high information throughput. Numeric values right-aligned in `JetBrains Mono`.
- **Inline Funnel Sparkbars**: Compact 4px height bar gauges nested inside table cells to illustrate transition rates between SIP Month 1, Month 2, and Month 3.

### Inputs & Date / Cohort Pickers
- **Field**: `#0D1117` background, `1px solid #30363D`, 6px radius, `JetBrains Mono` placeholder text in `#484F58`. On focus: `1px solid #00D09C` with zero shadow blur.

### AI Insight Cards
- Specialized card variation: Left edge accent mark (2px vertical stroke in `#5367FF`), dark gradient backdrop (`linear-gradient(135deg, rgba(83, 103, 255, 0.05) 0%, #161B22 100%)`), integrated single-click "Deploy Intervention" action buttons.