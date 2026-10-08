(function () {
    var initialized = false, generation = 0, activeId = null, busy = false, followups = [];
    function status(message) {
        var target = document.getElementById('resultLoadStatus');
        target.textContent = message || '';
        target.hidden = !message;
    }
    function displayFollowups(items) {
        followups = items;
        var target = document.getElementById('followupMessages');
        target.innerHTML = items.map(function (item) {
            return '<article class="followup-message"><h3>' + window.escapeHtml(item.question) + '</h3>' +
                window.renderMarkdownSimple(item.answer, '#173a34') + '<small>' +
                window.escapeHtml(new Date(item.created_at).toLocaleString()) + '</small></article>';
        }).join('');
    }
    async function load() {
        var current = ++generation;
        activeId = null;
        var workspace = document.getElementById('consultResultWorkspace');
        var empty = document.getElementById('consultResultEmpty');
        workspace.style.display = 'none'; empty.style.display = 'none';
        var query = new URLSearchParams(window.location.search);
        var id = query.get('id') || query.get('history');
        if (!id) {
            id = window.consultSession.resultId(window.consultPanel.readLatestConsultation());
            if (id) { window.history.replaceState(null, '', window.consultSession.url('consult-result.html', { id: id })); }
        }
        if (!id) { status(''); empty.style.display = ''; return; }
        if (!window.authClient.isAuthenticated()) {
            status('登录后可查看这份结果并继续追问。'); return;
        }
        status('正在载入问事结果…');
        try {
            var response = await window.apiClient.get('/api/auth/history/' + encodeURIComponent(id));
            if (current !== generation) { return; }
            var item = response.data.item;
            var data = item.consultation || item;
            data.legacy_record = !item.consultation;
            data.history_id = id; data.created_at = item.created_at;
            window.consultPanel.renderWorkspaceResult(data);
            activeId = id;
            document.getElementById('resultEditLink').href = window.consultSession.url('index.html', { edit: id });
            document.getElementById('resultBackLink').href = window.consultSession.url('index.html', { new: 1 });
            displayFollowups(item.followups || []);
            status(item.consultation ? '' : '这是一份早期记录：原始结论与摘要已保留，当时未保存的计算细节无法恢复。');
        } catch (error) {
            if (current !== generation) { return; }
            status(error.status === 404 ? '这份结果不存在，或不属于当前账号。请从账号历史重新打开。' : '载入失败：' + error.message);
            var retry = document.createElement('button');
            retry.type = 'button'; retry.textContent = '重新载入';
            retry.addEventListener('click', load);
            document.getElementById('resultLoadStatus').appendChild(retry);
        }
    }
    function initialize() {
        if (initialized || !document.getElementById('consultResultWorkspace')) { return; }
        initialized = true;
        window.addEventListener('auth-session-changed', function () {
            document.getElementById('followupQuestion').value = '';
            document.getElementById('followupStatus').textContent = '';
            displayFollowups([]);
            load();
        });
        document.getElementById('followupForm').addEventListener('submit', async function (event) {
            event.preventDefault();
            if (busy || !activeId) { return; }
            var input = document.getElementById('followupQuestion');
            var button = document.getElementById('followupSubmitBtn');
            var feedback = document.getElementById('followupStatus');
            var question = input.value.trim();
            if (!question) { feedback.textContent = '请填写要追问的问题。'; input.focus(); return; }
            busy = true; button.disabled = true; input.readOnly = true;
            feedback.textContent = '正在结合本次结果和之前的追问生成回答…';
            var id = activeId, current = generation, owner = window.consultSession.owner();
            var kind = 'followup:' + id;
            var requestId = window.consultSession.requestId(kind, question);
            try {
                var response = await window.apiClient.postJson('/api/system/consult/' + encodeURIComponent(id) + '/followups', {
                    question: question, request_id: requestId
                }, { timeoutMs: 180000 });
                window.consultSession.clearRequestId(kind, owner);
                if (current !== generation) { return; }
                var saved = response.data.followup;
                var updated = followups.filter(function (item) { return item.followup_id !== saved.followup_id; });
                updated.push(saved); displayFollowups(updated); input.value = '';
                feedback.textContent = '回答已保存到本次问事记录。'; input.focus();
            } catch (error) {
                if (current === generation) { feedback.textContent = '追问失败：' + error.message + ' 已保留问题内容。'; }
            } finally {
                busy = false; button.disabled = false; input.readOnly = false;
            }
        });
        load();
    }
    window.consultWorkspace = { initialize: initialize };
})();
