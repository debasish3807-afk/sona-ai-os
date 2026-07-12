# Frontend

The frontend applications for Sona AI OS, providing user interfaces across web and desktop platforms.

## Structure

```
frontend/
├── web/       — Web application (browser-based interface)
├── desktop/   — Desktop application (Electron/Tauri)
└── shared/    — Shared components, utilities, and design system
```

## Platforms

### Web (`web/`)

The primary web-based interface for Sona AI OS. Provides a responsive, accessible experience for all modern browsers.

### Desktop (`desktop/`)

Native desktop application wrapping the web interface with additional system-level capabilities like file system access, notifications, and keyboard shortcuts.

### Shared (`shared/`)

Common code shared between platforms:
- UI component library
- Design tokens and theming
- API client and state management
- Type definitions and utilities

## Design Principles

- Component-driven development
- Responsive and accessible (WCAG 2.1 AA)
- Dark/light theme support
- Performance-first approach
- Consistent design language across platforms
