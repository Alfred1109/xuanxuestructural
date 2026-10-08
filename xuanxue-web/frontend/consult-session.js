(function () {
    // Navigation and editable drafts share one account-scoped session boundary.
    function owner() {
        return window.authClient && window.authClient.getCurrentUserId
            ? window.authClient.getCurrentUserId() || 'guest' : 'guest';
    }

    function key(scope) { return 'xuanxue_consult_draft:' + (scope || owner()); }

    function readDraft(scope) {
        try {
            var raw = window.sessionStorage.getItem(key(scope));
            return raw ? JSON.parse(raw) : null;
        } catch (_error) { return null; }
    }

    function saveDraft(payload, scope) {
        try {
            window.sessionStorage.setItem(key(scope), JSON.stringify({
                payload: payload, updated_at: new Date().toISOString()
            }));
            return true;
        } catch (_error) { return false; }
    }

    function clearDraft(scope) {
        try { window.sessionStorage.removeItem(key(scope)); } catch (_error) { /* unavailable storage */ }
    }

    function url(page, values) {
        var target = new URL(page, window.location.href);
        var current = new URLSearchParams(window.location.search);
        ['apiBase', 'guideUrl'].forEach(function (name) {
            if (current.has(name)) { target.searchParams.set(name, current.get(name)); }
        });
        Object.keys(values || {}).forEach(function (name) {
            if (values[name] !== null && values[name] !== undefined) {
                target.searchParams.set(name, values[name]);
            }
        });
        return target.toString();
    }

    function resultId(data) {
        return data && (data.history_id || (data.account_history && data.account_history.history_id));
    }

    function editablePayload(detail) {
        if (detail.request_payload) { return detail.request_payload; }
        var data = detail.consultation || detail;
        var profile = data.profile || {};
        return Object.assign({}, profile.birth || {}, {
            question: data.question || '', gender: profile.gender || '', location: profile.location || ''
        });
    }

    function requestId(kind, fingerprint) {
        var storageKey = 'xuanxue_request:' + owner() + ':' + kind;
        try {
            var previous = JSON.parse(window.sessionStorage.getItem(storageKey) || 'null');
            if (previous && previous.fingerprint === fingerprint) { return previous.id; }
            var id = window.crypto.randomUUID();
            window.sessionStorage.setItem(storageKey, JSON.stringify({ id: id, fingerprint: fingerprint }));
            return id;
        } catch (_error) { return window.crypto.randomUUID(); }
    }
    function clearRequestId(kind, scope) {
        try { window.sessionStorage.removeItem('xuanxue_request:' + (scope || owner()) + ':' + kind); } catch (_error) { /* unavailable storage */ }
    }

    window.consultSession = {
        owner: owner, readDraft: readDraft, saveDraft: saveDraft, clearDraft: clearDraft,
        url: url, resultId: resultId, editablePayload: editablePayload, requestId: requestId, clearRequestId: clearRequestId
    };
})();
