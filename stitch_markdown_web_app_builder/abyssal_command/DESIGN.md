---
name: Abyssal Command
colors:
  surface: '#111412'
  surface-dim: '#111412'
  surface-bright: '#373a37'
  surface-container-lowest: '#0c0f0d'
  surface-container-low: '#1a1c1a'
  surface-container: '#1e201e'
  surface-container-high: '#282b28'
  surface-container-highest: '#333533'
  on-surface: '#e2e3df'
  on-surface-variant: '#c4c6cc'
  inverse-surface: '#e2e3df'
  inverse-on-surface: '#2f312e'
  outline: '#8e9196'
  outline-variant: '#44474c'
  surface-tint: '#bac8dc'
  primary: '#bac8dc'
  on-primary: '#243141'
  primary-container: '#0d1b2a'
  on-primary-container: '#768497'
  inverse-primary: '#525f71'
  secondary: '#a5d0b9'
  on-secondary: '#0e3727'
  secondary-container: '#29513f'
  on-secondary-container: '#97c2ab'
  tertiary: '#75daa8'
  on-tertiary: '#003823'
  tertiary-container: '#001f12'
  on-tertiary-container: '#299468'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#d6e4f9'
  primary-fixed-dim: '#bac8dc'
  on-primary-fixed: '#0f1c2c'
  on-primary-fixed-variant: '#3a4859'
  secondary-fixed: '#c1ecd4'
  secondary-fixed-dim: '#a5d0b9'
  on-secondary-fixed: '#002114'
  on-secondary-fixed-variant: '#274e3d'
  tertiary-fixed: '#92f7c3'
  tertiary-fixed-dim: '#75daa8'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005235'
  background: '#111412'
  on-background: '#e2e3df'
  surface-variant: '#333533'
  status-critical: '#E63946'
  status-warning: '#FFB703'
  status-stable: '#2D6A4F'
  status-emergency: '#9B2226'
  telemetry-teal: '#2EC4B6'
  deep-navy: '#01080E'
  surface-slate: '#1B263B'
typography:
  display-lg:
    fontFamily: Hanken Grotesk
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Hanken Grotesk
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
  headline-md:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  data-mono:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
    letterSpacing: 0.02em
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '700'
    lineHeight: 16px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 16px
  margin-mobile: 16px
  margin-desktop: 32px
  panel-gap: 24px
---

## Brand & Style

The design system is built for high-stakes, real-time crisis intervention. It balances the cold precision of scientific telemetry with the ethical urgency of wildlife preservation. The brand personality is **authoritative, vigilant, and radically transparent**, designed to evoke a sense of calm focus amidst a developing ecological emergency.

The visual style is **Corporate / Modern** with **Minimalist** efficiency, optimized for a high-density "Operations Center" environment. It utilizes a deep maritime dark mode to reduce eye strain during extended monitoring shifts, while employing high-intensity status colors that command immediate attention without cluttering the cognitive field. The UI prioritizes data visibility over decorative elements, favoring clean lines and structural integrity to reinforce a sense of institutional trust and accountability.

## Colors

The palette is anchored in **Deep Navy** and **Surface Slate** to establish a maritime-themed, low-light environment. This dark foundation allows the functional colors to surface with maximum contrast.

- **Primary & Neutral**: The background is dominated by `deep-navy`, while `neutral` (off-white/slate) is reserved for high-legibility text and primary UI borders.
- **Status Indicators**: These are non-negotiable. `status-critical` (Red) and `status-emergency` (Deep Red) are used only for life-threatening pod metrics or resource exhaustion. `status-warning` (Amber) indicates a projected bottleneck, and `status-stable` (Emerald) denotes health and sustainability.
- **Functional Accents**: `telemetry-teal` is used for non-critical data visualization, active states, and interactive elements like calibration toggles.
- **Marketplace**: Bay Credits (BC) interactions use the `tertiary-teal` to distinguish economic activity from biological telemetry.

## Typography

The typographic system is optimized for speed of comprehension under stress. 

- **Headlines**: Hanken Grotesk provides a sharp, contemporary professional feel for dashboard titles and section headers.
- **Body**: Inter is the workhorse for all qualitative descriptions and metadata, selected for its exceptional legibility in dark mode.
- **Data & Telemetry**: JetBrains Mono is used for all numerical values, stock levels, coordinates, and timestamps. Its fixed-width nature ensures that data grids remain stable and columns align perfectly, facilitating rapid scanning of fluctuating metrics.
- **Mobile Considerations**: On smaller viewports, `display-lg` should scale down to `headline-lg` metrics to maintain visual hierarchy without overwhelming the screen.

## Layout & Spacing

This design system employs a **Fluid Grid** model built on a 4px baseline unit. The layout is designed to maximize "information density per square inch" without sacrificing clarity.

- **Grid System**: A 12-column grid is used for desktop, collapsing to 8 for tablet and 4 for mobile. 
- **Side-by-Side Comparisons**: A primary layout pattern is the split-screen comparison (e.g., Naive vs. Fair Priority). These panels should maintain a strict `panel-gap` of 24px to distinguish distinct logic flows.
- **Banners**: Global alerts (Silent Need / Unmet Need) occupy the full width of the viewport above the primary navigation, acting as persistent status reminders.
- **Density**: Use tight padding in data tables (`8px` vertical) to ensure maximum row visibility on a single fold.

## Elevation & Depth

To maintain a "Public Ledger" aesthetic, the system avoids traditional soft shadows and instead uses **Tonal Layers** and **Low-contrast Outlines**.

- **Surfaces**: The base background is `deep-navy`. Secondary containers (widgets, pod profiles) use `surface-slate` with a subtle `1px` border in a slightly lighter neutral tone.
- **Depth tiers**:
    - **Level 0 (Base)**: Primary background.
    - **Level 1 (Card)**: Dashboard widgets and data grids.
    - **Level 2 (Active)**: Modals and quick-trade overlays. These use a very subtle backdrop blur (4px) to separate the interaction from the background telemetry.
- **Status Banners**: Use high-contrast solid backgrounds rather than shadows to denote priority. An "Unmet Need" banner should feel "anchored" to the top of the UI, not floating above it.

## Shapes

The shape language is **Soft** but disciplined. 

- **Primary Elements**: Buttons, input fields, and widget containers use a `0.25rem` (4px) corner radius. This provides a professional, engineered feel that is more approachable than sharp corners but more serious than fully rounded ones.
- **Status Badges**: Use `rounded-lg` (8px) or pill shapes to distinguish them from interactive buttons.
- **Charts**: Data points in line charts should be sharp, while bars in charts should have 0px roundedness on the bottom and 2px on the top to emphasize growth or depletion.

## Components

- **Status Badges**: High-contrast labels (e.g., CRITICAL, STABLE). Must use `label-caps` typography and the associated status color background with white or high-contrast black text.
- **Telemetry Cards**: Used for Pod Profiles. They must include a `data-mono` sub-header for real-time runway projections and a mini-line chart showing 24h stock depletion.
- **Fair-Priority Toggles**: Specialized switches that allow the user to toggle between raw drone data and calibrated outputs. The toggle should use `telemetry-teal` for the active state.
- **Banners (Crisis Alerts)**: Full-width components for "Silent Need Alerts." These should use a subtle pulse animation if the status is `emergency`.
- **Marketplace Inputs**: Input fields for Bay Credits should include the shell icon (`🦪`) as a prefix and use monospaced font for the currency values.
- **Data Grids**: Zebra-striped rows using a very subtle contrast difference between `deep-navy` and `surface-slate`. Hover states should highlight the entire row in a low-opacity `telemetry-teal`.
- **Resource Matrix**: A dense grid showing resource mismatches, utilizing the status colors to highlight specific cells where supply does not meet "Fair-Priority" demand.