# Conditional Documentation Index

Load these docs when the listed conditions apply.

- app_docs/feature-adw-5-schedule-management-ui.md
  - Conditions:
    - When working with cron schedule creation, editing, or deletion in the UI
    - When implementing or debugging the SchedulesSection component in SettingsPage
    - When adding per-schedule geo overrides to scheduler.js or routes/schedules.js
    - When troubleshooting schedule CRUD flows or geo fallback behavior in _fire

- app_docs/feature-adw-3-aio-files-uploader.md
  - Conditions:
    - When working with ADW screenshot uploading or the review pipeline
    - When implementing or debugging `upload_review_screenshots` in `adw_review_iso.py`
    - When configuring AIO credentials for the ADW pipeline
    - When troubleshooting missing or broken screenshot URLs in GitHub issue comments
    - When extending or replacing upload strategies (AIO Files, R2, GitHub Raw)

- app_docs/feature-adw-7-screenshot-lightbox-prev-next-navigation.md
  - Conditions:
    - When working with the screenshot lightbox in StepResult or RunSummary
    - When adding navigation, keyboard shortcuts, or state lifting to run results UI
    - When troubleshooting lightbox open/close or navigation behavior in the run view
    - When extending the Lightbox component with new controls or display modes

- app_docs/feature-adw-8-aem-content-fragments-service.md
  - Conditions:
    - When working with AEM Content Fragments or the aem-cf.js service
    - When implementing or debugging the `content` step type in runner.js
    - When configuring AEM author/publish env vars (AEM_AUTHOR_URL, AEM_PUBLISH_URL)
    - When extending CF fetching with new auth modes or field filter strategies

- app_docs/feature-adw-13-cta-validator-button-text-fix.md
  - Conditions:
    - When working with the `check_cta` step type in planner.js or runner.js
    - When debugging CTA button lookup failures in validateCTA()
    - When updating the planner system prompt for CTA-related step generation rules
    - When the CTA validator fails to find a button by label

- app_docs/feature-adw-19-cicd-pre-merge-checks.md
  - Conditions:
    - When adding or modifying GitHub Actions CI workflows
    - When configuring ESLint rules or the root `.eslintrc.json`
    - When troubleshooting CI job failures (lint, client build, server tests)
    - When setting up branch protection rules or adding new CI checks

- app_docs/feature-adw-21-typescript-foundation.md
  - Conditions:
    - When adding TypeScript to client files or importing domain interfaces
    - When working with `api.ts`, `runObserver.ts`, or tsconfig settings
    - When troubleshooting `tsc --noEmit` or Vite build failures in the client
    - When extending `Plan`, `Run`, `StepResult`, `Schedule`, `Settings`, `Message`, or `Conversation` interfaces

- app_docs/feature-adw-22-spectrum-layout-shell.md
  - Conditions:
    - When working with Sidebar, App, MessageInput, or MessageList components
    - When adopting Adobe React Spectrum in client layout or navigation components
    - When troubleshooting the typing-indicator animation or `animations.css`
    - When converting additional `.jsx` components to `.tsx` with Spectrum primitives

- app_docs/feature-adw-28-spectrum-token-cleanup.md
  - Conditions:
    - When adding layout or color to any client component (Flex/View/Text conventions)
    - When deciding whether UNSAFE_style is appropriate for a given CSS property
    - When mapping a hardcoded hex color or rem font size to a Spectrum token
    - When troubleshooting tsc or vite build failures after Spectrum adoption changes

- app_docs/feature-adw-30-spectrum-2-s1-component-rewrite.md
  - Conditions:
    - When migrating any client component from @adobe/react-spectrum (S1) to @react-spectrum/s2 (S2)
    - When using the style() macro from @react-spectrum/s2/style in client components
    - When working with App.tsx, Sidebar.tsx, or MessageInput.tsx layout or styling
    - When troubleshooting unplugin-parcel-macros or the style() macro in Vite builds

- app_docs/feature-adw-32-s2-batch2-page-components-typescript.md
  - Conditions:
    - When working with ChatPage, HistoryPage, SettingsPage, or RunDetailPage
    - When using S2 Badge, Picker/PickerItem, TextField, or Checkbox in page components
    - When extending or modifying the S2 status badge variant map (completed/failed/cancelled/running)
    - When adding new page components and need a reference for S2 + TypeScript page patterns
