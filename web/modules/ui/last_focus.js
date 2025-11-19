/**
 * Manage last-focused element references for modals/editors.
 * Replaces usage of `window.__lastSettingsTrigger` and `window.__lastEditorTrigger`.
 */

let lastSettingsTrigger = null;
let lastEditorTrigger = null;

export function setLastSettingsTrigger(el) {
    try { lastSettingsTrigger = el; } catch (_) { lastSettingsTrigger = null; }
}

export function focusLastSettingsTrigger() {
    try { lastSettingsTrigger?.focus?.(); } catch (_) {}
}

export function setLastEditorTrigger(el) {
    try { lastEditorTrigger = el; } catch (_) { lastEditorTrigger = null; }
}

export function focusLastEditorTrigger() {
    try { lastEditorTrigger?.focus?.(); } catch (_) {}
}

export default {
    setLastSettingsTrigger,
    focusLastSettingsTrigger,
    setLastEditorTrigger,
    focusLastEditorTrigger
};
