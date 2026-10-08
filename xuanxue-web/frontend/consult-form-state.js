(function () {
    var form, scope = 'guest', extras = {}, touched = false, restoring = false, generation = 0;
    var fields = ['question', 'year', 'month', 'day', 'hour', 'minute', 'gender', 'location'];
    var previousClear = null;
    function node(name) { return document.getElementById('consult' + name[0].toUpperCase() + name.slice(1)); }
    function status(message) {
        var target = document.getElementById('consultDraftStatus');
        if (target) { target.textContent = message; }
    }
    function read() {
        var value = Object.assign({}, extras);
        fields.forEach(function (name) {
            var raw = node(name).value.trim();
            value[name] = ['question', 'gender', 'location'].includes(name) ? raw : raw === '' ? null : Number(raw);
        });
        return value;
    }
    function apply(value) {
        value = value || {};
        extras = {};
        ['purpose', 'matter_type', 'visual_context'].forEach(function (name) {
            if (value[name] !== undefined) { extras[name] = value[name]; }
        });
        fields.forEach(function (name) { node(name).value = value[name] == null ? '' : value[name]; });
    }
    function save() {
        if (!form || restoring) { return; }
        touched = true;
        var saved = window.consultSession.saveDraft(read(), scope);
        status(saved ? '草稿已保存到当前标签页，返回或刷新可继续填写。' : '浏览器无法保存草稿，请保留当前页面。');
    }
    async function restore(reason) {
        var current = ++generation;
        var nextScope = window.consultSession.owner();
        var guestDraft = scope === 'guest' && nextScope !== 'guest' && touched ? window.consultSession.readDraft('guest') : null;
        var accountDraft = window.consultSession.readDraft(nextScope);
        if (guestDraft && accountDraft && accountDraft.updated_at > guestDraft.updated_at) { guestDraft = null; }
        if (nextScope !== scope) {
            previousClear = null;
            document.getElementById('undoClearConsultBtn').hidden = true;
        }
        scope = nextScope;
        var draft = guestDraft || accountDraft;
        var params = new URLSearchParams(window.location.search);
        var editId = params.get('edit');
        if (guestDraft && scope !== 'guest') {
            window.consultSession.saveDraft(guestDraft.payload, scope);
            window.consultSession.clearDraft('guest');
        }
        restoring = true;
        if (draft) {
            apply(draft.payload); touched = true;
            status('已恢复草稿，可继续填写。');
        } else {
            apply({}); touched = false; status('');
        }
        if (!editId) { restoring = false; return; }
        touched = true;
        if (scope === 'guest') {
            status('登录后可载入这次问事的原始条件。'); restoring = false; return;
        }
        status('正在载入本次问事条件…');
        var loadingFields = Array.from(form.querySelectorAll('input, textarea, select')).filter(function (field) { return !field.disabled; });
        loadingFields.forEach(function (field) { field.disabled = true; });
        try {
            var response = await window.apiClient.get('/api/auth/history/' + encodeURIComponent(editId));
            if (current !== generation) { return; }
            apply(window.consultSession.editablePayload(response.data.item));
            window.consultSession.saveDraft(read(), scope);
            status('已载入原始条件，修改后可重新分析。');
            // Consume the edit command so a later refresh restores edits instead of overwriting them.
            params.delete('edit');
            window.history.replaceState(null, '', window.consultSession.url('index.html', Object.fromEntries(params)));
        } catch (error) {
            if (current === generation) { status('条件载入失败：' + error.message); }
        } finally {
            loadingFields.forEach(function (field) { field.disabled = false; });
            if (current === generation) { restoring = false; }
        }
    }
    function initialize() {
        form = document.getElementById('consultForm');
        if (!form) { return; }
        var params = new URLSearchParams(window.location.search);
        if (params.get('new') === '1') {
            // Delay clearing the account draft until auth has identified its owner.
            window.addEventListener('auth-session-changed', function clearNew() {
                window.consultSession.clearDraft();
                params.delete('new');
                window.history.replaceState(null, '', window.consultSession.url('index.html', Object.fromEntries(params)));
                window.removeEventListener('auth-session-changed', clearNew);
            });
        } else { restore(); }
        form.addEventListener('input', save);
        form.addEventListener('change', save);
        window.addEventListener('pagehide', save);
        window.addEventListener('auth-session-changed', function (event) { restore(event.detail.reason); });
        document.getElementById('undoClearConsultBtn').addEventListener('click', function () {
            if (!previousClear) { return; }
            apply(previousClear); previousClear = null; this.hidden = true; save();
            status('已撤销清空，恢复刚才填写的条件。');
        });
    }
    window.consultFormState = {
        initialize: initialize, read: read, save: save, apply: apply,
        selectScenario: function (question) {
            node('question').value = question;
            delete extras.purpose; delete extras.matter_type;
            save();
        },
        ready: function () { return !restoring; },
        canApplyDefault: function () { return !!form && !touched && !restoring && !new URLSearchParams(window.location.search).has('edit'); },
        clear: function () {
            previousClear = read(); apply({}); save();
            document.getElementById('undoClearConsultBtn').hidden = false;
            status('已清空表单，可撤销恢复。');
        }
    };
})();
