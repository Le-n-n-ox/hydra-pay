# Hydra Pay dashboard (frontend)

React + TypeScript app for the Hydra Pay dashboard, built with Vite, Tailwind CSS, shadcn/ui (Base UI), lucide-react, Recharts, Motion and Sonner.

`dashboard.py` serves the **built** app from `../static/`, so day-to-day use (`start.bat`) needs no Node.js. You only need Node when you change the UI.

## Develop

```bash
cd frontend
npm install
npm run dev        # landing page on http://localhost:5173, dashboard on /dashboard; API calls go to dashboard.py on :8000
```

Keep `python dashboard.py` running in another window while you develop.

## Build

```bash
npm run build      # type-checks, then writes the app to ../static/
```

Commit the updated `static/` folder so the dashboard works without a build step.

## Themes

Open the palette button (top right) to choose **Light / Dark / System** and one of six themes: Hydra, Emerald, Sunset, Orchid, Aqua or Graphite. The sun/moon button flips light/dark in one click. The choice is saved per browser in `localStorage` (`hydra-ui`) and applied by an inline script in `index.html` before the first paint, so there is no flash of the wrong theme.

A link can preset the appearance, for example `http://localhost:8000/dashboard?mode=light&theme=sunset`.

- Palettes live in `src/themes.css`: one light block and one dark block per theme, using the shadcn variables plus `--brand-1/2/3`, `--brand-text`, `--good`, `--bad`, `--warn`.
- In components use `from-brand-1 to-brand-2`, `text-good`, `text-bad`, `text-warn`, `text-brand-text`, and `foreground/[0.05]`-style overlays. Avoid fixed colours such as `blue-500` or `white/5`, so the component works in every theme.
- Charts read the live colours through `useThemeColors()`.
- To add a theme: add its blocks to `src/themes.css`, add it to `THEMES` in `src/hooks/useTheme.tsx`, and add its id to the list in `index.html`.

## Layout

| Path | What it holds |
|---|---|
| `index.html` → `/` | Public landing page (`src/landing/`) |
| `dashboard.html` → `/dashboard` | The dashboard (`src/main.tsx`) |
| `src/App.tsx` | Dashboard shell: sidebar, top bar with service status, new-card banner, page switching (`#overview`, `#payments`, `#cards`, `#activity`, `#telco`) |
| `src/views/` | One file per screen |
| `src/components/shared.tsx` | Animated background, stat cards, panels, badges, avatars, RFID card graphic |
| `src/components/charts.tsx` | Recharts charts |
| `src/components/dialogs.tsx` | Add/edit card, top-up, replace-card dialogs |
| `src/components/ui/` | shadcn/ui components |
| `src/hooks/useAdmin.tsx` | Admin PIN dialog; every admin action goes through `useAdmin()` |
| `src/hooks/useDashboard.ts` | Polls `/api/data` every 2 s and `/api/telco/status` every 10 s |
| `src/lib/api.ts` | Types for the Flask API |
