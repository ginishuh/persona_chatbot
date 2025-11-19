// web/modules/files/pending.js
// 중앙화된 파일/템플릿 pending 상태 관리

let pendingFileListSelect = null;
let pendingFileListType = null;
let pendingTemplateSelect = null;
let pendingLoadType = null;
let pendingTemplateItem = null;
let pendingTemplateModal = false;
let pendingAddFromTemplate = false;

export function setPendingFileList(selectElement, type) {
    pendingFileListSelect = selectElement;
    pendingFileListType = type;
}

export function consumePendingFileList() {
    const out = { select: pendingFileListSelect, type: pendingFileListType };
    pendingFileListSelect = null;
    pendingFileListType = null;
    return out;
}

export function setPendingTemplateSelect(selectElement) {
    pendingTemplateSelect = selectElement;
}

export function consumePendingTemplateSelect() {
    const out = pendingTemplateSelect;
    pendingTemplateSelect = null;
    return out;
}

export function setPendingLoadType(type) {
    pendingLoadType = type;
}

export function getPendingLoadType() {
    return pendingLoadType;
}

export function clearPendingLoadType() {
    pendingLoadType = null;
}

export function setPendingTemplateItem(el) {
    pendingTemplateItem = el;
}

export function consumePendingTemplateItem() {
    const out = pendingTemplateItem;
    pendingTemplateItem = null;
    return out;
}

export function setPendingTemplateModal(flag) {
    pendingTemplateModal = !!flag;
}

export function isPendingTemplateModal() {
    return !!pendingTemplateModal;
}

export function clearPendingTemplateModal() {
    pendingTemplateModal = false;
}

export function setPendingAddFromTemplate(flag) {
    pendingAddFromTemplate = !!flag;
}

export function isPendingAddFromTemplate() {
    return !!pendingAddFromTemplate;
}

export function clearPendingAddFromTemplate() {
    pendingAddFromTemplate = false;
}
