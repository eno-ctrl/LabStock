# LabStock Design System Audit & Flet Component Mapping

This document maps the Stitch Design System (`clinical_precision/DESIGN.md`) and the 12 extracted screen references to native Flet UI components and workflows.

## 1. Visual Token System

| Token Name | Hex Code | Visual Role | Flet Usage |
| :--- | :--- | :--- | :--- |
| **Primary Navy** | `#15263B` | Shell navigation, topbar, primary action buttons | `ft.Colors` or hex `"#15263B"` |
| **Secondary Navy** | `#213B54` | Table headers, secondary toolbars, active nav states | `"#213B54"` |
| **Primary Mint** | `#36B78A` | Focal tracking, confirmed stock, active chips, positive badges | `"#36B78A"` |
| **Dark Green** | `#21805F` | High-contrast text on mint tags, hover on mint buttons | `"#21805F"` |
| **Canvas Background** | `#F5F7FA` | Flat non-elevated application substrate | `"#F5F7FA"` |
| **Surface** | `#FFFFFF` | Cards, modals, drawers, input backgrounds | `"#FFFFFF"` |
| **Primary Content Text** | `#1E293B` | Main labels, table text, headers | `"#1E293B"` |
| **Secondary Content Text** | `#64748B` | Subheaders, hints, timestamps | `"#64748B"` |
| **Structural Border** | `#E2E8F0` | 1px crisp container outlines, dividers | `"#E2E8F0"` |
| **Success Status** | `#198754` | In-stock confirmations, pass-rate audits | `"#198754"` |
| **Warning Status** | `#D99000` | Low inventory thresholds, pending orders | `"#D99000"` |
| **Error / Stockout** | `#DC3545` | Stockout alerts, destructive actions | `"#DC3545"` |
| **Information Status** | `#2673C8` | In-transit spare parts, general notices | `"#2673C8"` |

## 2. Typography Standard
- **Primary Font Family**: `Inter`, sans-serif (labels, headings, body text)
- **Monospace Font Family**: `JetBrains Mono` / `Courier New` monospace (for SKUs, batch IDs, serials, and tabular metrics)
- **Tabular Numerals**: Standard vertical numeric alignment for stock counts and financial figures.

## 3. Screen-to-Flet Component Mapping

| # | Screen Reference | Layout Pattern | Core Flet Components | Live Workflow |
| :--- | :--- | :--- | :--- | :--- |
| 1 | `labstock_login` | Centered card on canvas | `ft.Card`, `ft.TextField`, `ft.ElevatedButton`, `ft.Checkbox`, brand emblem | POST `/api/v1/auth/login`, session token storage |
| 2 | `labstock_dashboard` | 4-column metric grid + quick actions strip + attention cards | `MetricCard`, `ft.Row` action chips, `ft.ListView` of low/out-of-stock items | GET `/api/v1/dashboard/summary`, `/dashboard/recent-activity` |
| 3 | `labstock_inventory_management` | Filter toolbar + Search bar + Data table / card list | `SearchBar`, `FilterBar`, `DataTable` with status chips, pagination buttons | GET `/api/v1/items`, deactivation modal |
| 4 | `labstock_add_or_edit_inventory_item` | Multi-section form card | `ft.TextField`, `ft.Dropdown`, `ft.Switch`, validation banner | POST / PATCH `/api/v1/items`, supplier dropdown |
| 5 | `labstock_item_details_history` | Header summary + balance metrics + chronological ledger | `ft.Tabs`, metadata card, movement history `DataTable` | GET `/api/v1/items/{id}`, `/items/{id}/movements` |
| 6 | `labstock_stock_movements` | Action buttons (Receipt, Issue, Return, Damage, Adjust) + Ledger table | Form modal dialogs for each movement type with confirmation + filtered ledger | POST `/api/v1/movements/*`, GET `/movements` |
| 7 | `labstock_low_stock_replenishment` | Low-stock / Out-of-stock dual tables + Reorder suggestion | Status pill badges, threshold vs on-hand indicators, "Draft Purchase Request" button | GET `/api/v1/replenishment/*`, create PR draft |
| 8 | `labstock_reports_analytics` | Report category dropdown + date picker/filters + preview table + CSV export | Export button with formula sanitization, interactive report selector | GET `/api/v1/reports/*`, CSV download stream |
| 9 | `labstock_supplier_management` | Supplier directory list/table + add/edit modal | Contact cards, active toggle, associated items count | GET / POST / PATCH `/api/v1/suppliers` |
| 10 | `labstock_purchase_requests` | Purchase request list with lifecycle status + request details drawer | Status badges (`Draft` -> `Received`), line items table, receive stock dialog | GET / POST `/api/v1/purchase-requests/*` |
| 11 | `labstock_user_management` | User account table + role assignment dialog | Admin-only role badges, active switches, protection against last admin deletion | GET / POST / PATCH `/api/v1/users` |
| 12 | `labstock_settings` | Safe configuration cards | Display prefs, stock rules, system engine status, DB backend info | Safe system diagnostics and preferences |
