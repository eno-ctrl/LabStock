---
name: Clinical Precision
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#44474d'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#74777d'
  outline-variant: '#c4c6cd'
  surface-tint: '#4f5f77'
  primary: '#001125'
  on-primary: '#ffffff'
  primary-container: '#15263b'
  on-primary-container: '#7d8da7'
  inverse-primary: '#b7c8e3'
  secondary: '#47617b'
  on-secondary: '#ffffff'
  secondary-container: '#c5dfff'
  on-secondary-container: '#4a637e'
  tertiary: '#00140c'
  on-tertiary: '#ffffff'
  tertiary-container: '#002c1d'
  on-tertiary-container: '#09a075'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d3e4ff'
  primary-fixed-dim: '#b7c8e3'
  on-primary-fixed: '#0a1c31'
  on-primary-fixed-variant: '#37485e'
  secondary-fixed: '#cfe4ff'
  secondary-fixed-dim: '#afc9e8'
  on-secondary-fixed: '#001d34'
  on-secondary-fixed-variant: '#2f4962'
  tertiary-fixed: '#7ff9c7'
  tertiary-fixed-dim: '#61dcac'
  on-tertiary-fixed: '#002115'
  on-tertiary-fixed-variant: '#005139'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.005em
  title-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: 0em
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0em
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.03em
  code-md:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
    letterSpacing: 0em
  code-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-compact: 0.5rem
  margin: 1.5rem
  margin-compact: 1rem
  space-xxs: 0.125rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1rem
  space-xl: 1.5rem
  space-2xl: 2rem
---

## Brand & Style

This design system serves technical laboratory personnel, inventory managers, and procurement specialists operating in rigorous, compliance-driven environments. The visual language conveys uncompromising reliability, clinical precision, and calm efficiency under pressure. It eliminates decorative ambiguity in favor of structured data density, immediate scanning, and verifiable state representation.

The aesthetic fuses **Corporate / Modern** discipline with **Technical Utility**:
- High-density information architecture paired with deliberate structural padding to reduce cognitive strain during inventory reconciliation.
- Strict visual hierarchy driven by systematic borders, tonal compartmentalization, and disciplined accent color usage.
- Tactile, accessible affordances tailored for cross-platform desktop operations, barcode-scanner workflows, and rapid keyboard entry.

## Colors

The palette establishes a stable, clinical baseline with authoritative deep navies, balanced by energetic mint greens for successful actions, active states, and focal tracking points.

### Role Mapping
- **Primary Navy (`#15263B`)**: Shell navigation, primary button backgrounds, master headings, and high-impact structural containers.
- **Secondary Navy (`#213B54`)**: Sub-headers, secondary toolbars, table headers, and selected navigation states.
- **Primary Mint Green (`#36B78A`)**: Primary callouts, confirmed inventory status, active badges, stock adjustments, and high-priority primary affirmative actions.
- **Dark Green (`#21805F`)**: Hover states for mint elements, high-contrast text on light green badges, and deep status markers requiring WCAG AAA compliance.
- **Background (`#F5F7FA`)**: Canvas substrate providing slight cool contrast against nested components.
- **Surface (`#FFFFFF`)**: Data cards, data tables, modals, flyouts, and input backgrounds.
- **Text & Borders**:
  - Primary Content: `#1E293B`
  - Secondary / Supporting: `#64748B`
  - Structural Borders: `#E2E8F0`

### Status Tokens
- **Success (`#198754`)**: In-stock confirmations, pass-rate audits, completed maintenance cycles.
- **Warning (`#D99000`)**: Low inventory thresholds, calibration due within 7 days, partial shipments.
- **Error (`#DC3545`)**: Stockouts, expired reagents, non-compliance alerts, failed verification.
- **Information (`#2673C8`)**: In-transit spare parts, general notices, batch metadata tags.

## Typography

The typography standard relies on **Inter** for all UI surfaces, supported by **JetBrains Mono** strictly for SKUs, batch tracking IDs, serial identifiers, and tabular unit counts.

### Usage Standards
- **Tabular Alignment**: Enable `font-variant-numeric: tabular-nums` across all numeric readouts, tables, and metric dashboards to guarantee uniform vertical alignment.
- **SKU & Serial Codes**: Apply `code-md` or `code-sm` paired with subtle container backgrounds to differentiate structural catalog IDs from conversational inventory names.
- **Form Labels & Table Headers**: Use `label-sm` with uppercase transformation and `0.03em` tracking on table headers, providing distinct visual separation from cell values.

## Layout & Spacing

The layout model is optimized for high-density enterprise workflows utilizing an 8pt architectural rhythm, with a supplementary 4pt sub-scale for micro-components (table cells, chips, form paddings).

### Layout Geometry
- **Container Structure**: 12-column dynamic responsive layout for analytical dashboards; dual-pane master-detail arrangement for parts catalogs and batch inspection views.
- **Breakpoints**:
  - `Desktop Expanded` (>1440px): Persistent sidebar (260px), 24px margins, standard 16px grid gutters.
  - `Desktop Standard` (1024px - 1439px): Collapsible icon-rail sidebar (72px), 20px margins, 16px gutters.
  - `Field Tablet / Mobile` (<1023px): Off-canvas navigation drawer, single-column stacked records, 16px margins, 8px gutters.
- **Data Table Density**: Strict 40px row height for compact mode, 48px for standard inventory listing mode with nested thumbnail chips.

## Elevation & Depth

To preserve laboratory-grade legibility and prevent interface visual fatigue, the design system minimizes deep ambient shadows. Depth is achieved via **tonal layering** and **crisp 1px boundary lines**.

### Elevation Stack
- **Level 0 (Base Canvas)**: `#F5F7FA` — flat, non-elevated application background.
- **Level 1 (Card & Table Surface)**: `#FFFFFF` bounded by a strict `1px solid #E2E8F0` border. Zero drop-shadow in resting state; subtle `0 2px 4px rgba(21, 38, 59, 0.04)` on hover.
- **Level 2 (Dropdowns, Menus & Toolbars)**: `#FFFFFF`, `1px solid #E2E8F0`, with `0 4px 12px rgba(21, 38, 59, 0.08)`.
- **Level 3 (Modals, Slide-over Drawers)**: `#FFFFFF`, `1px solid #E2E8F0`, with `0 12px 32px rgba(21, 38, 59, 0.16)`.
- **Level 4 (Toasts & Floating Action Banners)**: `#15263B` (Primary Navy solid background) with `0 8px 24px rgba(21, 38, 59, 0.20)`.

## Shapes

The interface balances sharp enterprise structure with approachable accessibility using **8px to 12px corner geometry**.

### Corner Mapping
- **Buttons, Form Inputs, Badges, Dropdowns**: `8px` (`0.5rem`) for crisp precision and distinct interactive bounding boxes.
- **Cards, Table Shells, Filter Toolbars**: `10px` (`0.625rem`) for balanced perimeter definition.
- **Modals, Flyout Drawers, Master Overview Panels**: `12px` (`0.75rem`) to soften larger viewports.
- **Status Pills, Count Indicators**: Fully rounded (`9999px`) to immediately distinguish scalar metadata from structural action targets.

## Components

### Buttons
- **Primary**: Background `#15263B`, text `#FFFFFF`, hover `#213B54`, active scale `0.98`. Border-radius `8px`. Padding `8px 16px`.
- **Accent Primary**: Background `#36B78A`, text `#FFFFFF`, hover `#21805F`. Used for critical inventory updates (e.g., "Receive Stock", "Audit Pass").
- **Secondary / Outline**: Background `#FFFFFF`, border `1px solid #E2E8F0`, text `#1E293B`, hover background `#F5F7FA`, hover border `#CBD5E1`.
- **Destructive**: Background `#FFFFFF`, border `1px solid #FCA5A5`, text `#DC3545`, hover background `#FEF2F2`.

### Status Badges & Chips
- Formed with a 1px border, 4px vertical padding, 8px horizontal padding, and `9999px` radius:
  - **In-Stock / Approved**: Background `#EBFBF5`, border `#36B78A`, text `#21805F`.
  - **Low Stock / Calibrating**: Background `#FFFBEB`, border `#FCD34D`, text `#D99000`.
  - **Critical Stockout / Expired**: Background `#FEF2F2`, border `#FCA5A5`, text `#DC3545`.
  - **SKU Chip**: Monospace text (`JetBrains Mono`), background `#F1F5F9`, border `#E2E8F0`, text `#1E293B`.

### Input Fields & Controls
- **Text Inputs**: Height 38px (compact) or 44px (default). Background `#FFFFFF`, border `1px solid #E2E8F0`, text `#1E293B`, placeholder `#94A3B8`.
- **Focus State**: `1px solid #36B78A` border with an explicit `0 0 0 3px rgba(54, 183, 138, 0.15)` focus ring.
- **Checkboxes & Radios**: 18px box size, 4px radius (checkbox) or circular (radio), border `1.5px solid #CBD5E1`. Active state fill `#15263B` with high-contrast white check indicator.

### Data Tables
- **Header**: Background `#F8FAFC`, bottom border `1px solid #E2E8F0`, label `label-sm` in `#64748B`.
- **Row**: Alternating hover fill `#F8FAFC`, dividing border `1px solid #E2E8F0`. Tabular mono-spacing applied to units, quantities, and dates.
- **Action Columns**: Right-aligned pinning with low-profile icon buttons.

### Modals & Drawers
- **Backdrop**: `#15263B` with 45% opacity and subtle `2px` blur.
- **Drawer Panels**: Anchored right, fixed width (480px or 640px), solid white surface with a continuous left border of `1px solid #E2E8F0`.