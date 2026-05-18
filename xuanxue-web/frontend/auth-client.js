(function () {
    var AUTH_TOKEN_KEY = 'xuanxue_auth_token';
    var currentUser = null;
    var initialized = false;
    var consultPresets = [];
    var moduleLabels = {
        bazi: '八字底盘',
        ziwei: '紫微命盘',
        fengshui: '风水空间',
        visual: '视觉观察',
        liuyao: '六爻问事',
        meihua: '梅花起卦',
        qimen: '奇门时空',
        zeri: '择日择时'
    };

    function esc(value) {
        return window.escapeHtml ? window.escapeHtml(value) : String(value || '');
    }

    function formatRequestError(prefix, error) {
        var message = error && error.message ? error.message : '请求失败';
        if (window.isConnectivityError && window.isConnectivityError(error)) {
            return prefix + '：无法连接后端服务。请确认当前站点的后端代理已启动，并强制刷新页面后重试。';
        }
        return prefix + '：' + message;
    }

    function getToken() {
        try {
            return window.localStorage.getItem(AUTH_TOKEN_KEY) || '';
        } catch (_err) {
            return '';
        }
    }

    function setToken(token) {
        try {
            if (token) {
                window.localStorage.setItem(AUTH_TOKEN_KEY, token);
            } else {
                window.localStorage.removeItem(AUTH_TOKEN_KEY);
            }
        } catch (_err) {
            // Ignore storage failures.
        }
    }

    function moduleLabel(name) {
        return moduleLabels[name] || name || '模块';
    }

    function isAccountPage() {
        try {
            return window.location.pathname.endsWith('/account.html') || window.location.pathname.endsWith('account.html');
        } catch (_err) {
            return false;
        }
    }

    function openAccountCenter() {
        if (isAccountPage()) {
            var target = document.getElementById('accountCenter');
            if (target) {
                window.setTimeout(function () {
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }, 80);
            }
            return;
        }
        try {
            window.location.href = new URL('account.html', window.location.href).toString();
        } catch (_err) {
            window.location.href = 'account.html';
        }
    }

    function renderHeader() {
        var loginBtn = document.getElementById('openAuthModalBtn');
        var accountBtn = document.getElementById('openAccountCenterBtn');
        var logoutBtn = document.getElementById('logoutBtn');
        var nameEl = document.getElementById('headerAccountName');
        var metaEl = document.getElementById('headerAccountMeta');

        if (!nameEl || !metaEl) {
            return;
        }

        if (currentUser) {
            if (loginBtn) {
                loginBtn.style.display = 'none';
            }
            if (accountBtn) {
                accountBtn.style.display = isAccountPage() ? 'none' : '';
            }
            if (logoutBtn) {
                logoutBtn.style.display = '';
            }
            nameEl.textContent = currentUser.display_name || currentUser.email || '已登录';
            metaEl.textContent = currentUser.email || '登录中';
        } else {
            if (loginBtn) {
                loginBtn.style.display = '';
            }
            if (accountBtn) {
                accountBtn.style.display = isAccountPage() ? 'none' : '';
            }
            if (logoutBtn) {
                logoutBtn.style.display = 'none';
            }
            nameEl.textContent = '未登录';
            metaEl.textContent = '请先登录，统一问事功能仅对账号开放';
        }
    }

    function renderConsultPresetGrid() {
        var grid = document.getElementById('savedPresetGrid');
        if (!grid) {
            return;
        }

        if (!currentUser) {
            grid.innerHTML = '<div class="saved-preset-empty">登录后保存过的常用问事条件，会显示在这里。</div>';
            return;
        }

        if (!consultPresets.length) {
            grid.innerHTML = '<div class="saved-preset-empty">你还没有保存常用条件。填好一次问事基础信息后，点“保存当前条件”即可复用。</div>';
            return;
        }

        grid.innerHTML = consultPresets.map(function (item) {
            var meta = [
                item.question ? '问题：' + item.question : '',
                item.year ? '生辰：' + [item.year, item.month, item.day, item.hour].filter(Boolean).join('-') : '',
                item.gender ? '性别：' + item.gender : '',
                item.location ? '地点：' + item.location : ''
            ].filter(Boolean).join(' · ');
            return [
                '<div class="saved-preset-item" data-preset-id="' + esc(item.preset_id) + '">',
                '  <button type="button" class="danger-btn" data-delete-preset="' + esc(item.preset_id) + '" aria-label="删除常用条件">×</button>',
                '  <div class="title">' + esc(item.name || '未命名条件') + '</div>',
                '  <div class="meta">' + esc(meta || '已保存基础条件') + '</div>',
                '  <div class="actions">',
                '    <button type="button" class="mini-btn" data-apply-preset="' + esc(item.preset_id) + '">一键套用</button>',
                '    <button type="button" class="mini-btn default ' + (item.is_default ? 'active' : '') + '" data-default-preset="' + esc(item.preset_id) + '">' + (item.is_default ? '默认条件' : '设为默认') + '</button>',
                '  </div>',
                '</div>'
            ].join('');
        }).join('');
    }

    function renderAccount() {
        var gate = document.getElementById('accountGuestGate');
        var content = document.getElementById('accountAuthedContent');
        var title = document.getElementById('accountTitleText');
        var meta = document.getElementById('accountTitleMeta');
        var emailPill = document.getElementById('accountEmailPill');

        if (!gate || !content || !title || !meta || !emailPill) {
            return;
        }

        if (!currentUser) {
            gate.style.display = '';
            content.style.display = 'none';
            title.textContent = '登录后才能使用统一问事';
            meta.textContent = '账号用于开启系统问事、保存资料，并回看个人历史记录。';
            emailPill.textContent = '统一问事仅对已登录账号开放';
            renderHistoryList([]);
            renderHistoryDetail(null);
            renderConsultPresetGrid();
            return;
        }

        gate.style.display = 'none';
        content.style.display = '';
        title.textContent = currentUser.display_name || '我的账号';
        meta.textContent = '维护资料，并回看自己的完整问事结论。';
        emailPill.textContent = currentUser.email || '账号已登录';

        var profile = currentUser.profile || {};
        var birth = profile.birth || {};
        document.getElementById('profileDisplayName').value = currentUser.display_name || '';
        document.getElementById('profileGender').value = profile.gender || '';
        document.getElementById('profileLocation').value = profile.location || '';
        document.getElementById('profileYear').value = birth.year || '';
        document.getElementById('profileMonth').value = birth.month || '';
        document.getElementById('profileDay').value = birth.day || '';
        document.getElementById('profileHour').value = birth.hour || '';
        document.getElementById('profileMinute').value = birth.minute || '';
        document.getElementById('profileCurrentPassword').value = '';
        document.getElementById('profileNewPassword').value = '';
        renderConsultPresetGrid();
    }

    function renderHistoryList(items) {
        var listEl = document.getElementById('historyList');
        var countEl = document.getElementById('historyCountPill');
        if (!listEl) {
            return;
        }

        if (!currentUser) {
            if (countEl) {
                countEl.textContent = '未登录';
            }
            listEl.innerHTML = '<div class="history-empty">请先登录账号。登录后才能发起统一问事，并在这里查看自己的历史记录。</div>';
            return;
        }

        if (!items.length) {
            if (countEl) {
                countEl.textContent = '0 条记录';
            }
            listEl.innerHTML = '<div class="history-empty">还没有问事历史。登录后使用统一问事，就会自动保存在这里。</div>';
            return;
        }

        if (countEl) {
            countEl.textContent = items.length + ' 条记录';
        }

        listEl.innerHTML = items.map(function (item) {
            var modules = Array.isArray(item.modules) ? item.modules : [];
            return [
                '<button type="button" class="history-item" data-history-id="' + esc(item.history_id) + '">',
                '  <div class="history-item-head">',
                '    <span class="history-item-time">' + esc(item.created_at || '') + '</span>',
                '    <span class="history-item-tag">' + esc(item.matter_type || '通用') + '</span>',
                '  </div>',
                '  <div class="history-item-question">' + esc(item.question || '未命名问题') + '</div>',
                '  <div class="history-item-answer">' + esc(item.brief_answer || '已生成结论') + '</div>',
                '  <div class="history-chip-row">' + modules.map(function (moduleName) {
                    return '<span class="history-chip">' + esc(moduleLabel(moduleName)) + '</span>';
                }).join('') + '</div>',
                '</button>'
            ].join('');
        }).join('');
    }

    function renderHistoryDetail(item) {
        var detailEl = document.getElementById('historyDetail');
        if (!detailEl) {
            return;
        }

        if (!currentUser) {
            detailEl.innerHTML = '<div class="history-empty">登录后可查看完整问事结论与模块摘要。</div>';
            return;
        }

        if (!item) {
            detailEl.innerHTML = '<div class="history-empty">选择左侧一条历史记录，右侧查看详细内容。</div>';
            return;
        }

        var summaries = item.module_summaries || {};
        var modules = Array.isArray(item.intent && item.intent.modules) ? item.intent.modules : [];
        detailEl.innerHTML = [
            '<div class="history-detail-top">',
            '  <div class="history-detail-time">' + esc(item.created_at || '') + '</div>',
            '  <h3>' + esc(item.question || '问事记录') + '</h3>',
            '  <div class="history-chip-row">' + modules.map(function (moduleName) {
                return '<span class="history-chip">' + esc(moduleLabel(moduleName)) + '</span>';
            }).join('') + '</div>',
            '</div>',
            '<div class="history-detail-answer">' + (window.renderMarkdownSimple ? window.renderMarkdownSimple(item.answer || '', '#173a34') : esc(item.answer || '')) + '</div>',
            '<div class="history-summary-block">',
            '  <div class="history-summary-title">模块摘要</div>',
            '  <div class="history-summary-grid">' + Object.keys(summaries).map(function (key) {
                var raw = summaries[key];
                var body = typeof raw === 'string' ? raw : JSON.stringify(raw, null, 2);
                return [
                    '<div class="history-summary-card">',
                    '  <div class="title">' + esc(moduleLabel(key)) + '</div>',
                    '  <div class="body">' + esc(body) + '</div>',
                    '</div>'
                ].join('');
            }).join('') + '</div>',
            '</div>'
        ].join('');
    }

    async function refreshSession() {
        if (!getToken()) {
            currentUser = null;
            consultPresets = [];
            renderHeader();
            renderAccount();
            return null;
        }

        try {
            var response = await window.apiClient.get('/api/auth/me');
            currentUser = response.data && response.data.user ? response.data.user : null;
        } catch (_err) {
            setToken('');
            currentUser = null;
            consultPresets = [];
        }

        renderHeader();
        renderAccount();
        return currentUser;
    }

    async function refreshConsultPresets() {
        if (!currentUser) {
            consultPresets = [];
            renderConsultPresetGrid();
            return [];
        }

        var response = await window.apiClient.get('/api/auth/consult-presets');
        consultPresets = response.data && Array.isArray(response.data.items) ? response.data.items : [];
        renderConsultPresetGrid();
        return consultPresets;
    }

    async function saveConsultPreset(payload) {
        if (!currentUser) {
            throw new Error('请先登录');
        }
        var response = await window.apiClient.postJson('/api/auth/consult-presets', payload);
        consultPresets = response.data && Array.isArray(response.data.items) ? response.data.items : [];
        renderConsultPresetGrid();
        return consultPresets;
    }

    async function deleteConsultPreset(presetId) {
        if (!currentUser) {
            throw new Error('请先登录');
        }
        var response = await window.apiClient.request('/api/auth/consult-presets/' + encodeURIComponent(presetId), {
            method: 'DELETE'
        });
        consultPresets = response.data && Array.isArray(response.data.items) ? response.data.items : [];
        renderConsultPresetGrid();
        return consultPresets;
    }

    function getConsultPresets() {
        return consultPresets.slice();
    }

    function getDefaultConsultPreset() {
        for (var i = 0; i < consultPresets.length; i += 1) {
            if (consultPresets[i] && consultPresets[i].is_default) {
                return consultPresets[i];
            }
        }
        return null;
    }

    async function refreshHistory(options) {
        var opts = options || {};
        if (!currentUser) {
            renderHistoryList([]);
            renderHistoryDetail(null);
            return;
        }

        var response = await window.apiClient.get('/api/auth/history', { limit: 30 });
        var items = response.data && Array.isArray(response.data.items) ? response.data.items : [];
        renderHistoryList(items);

        if (opts.openLatest && items.length) {
            await openHistoryDetail(items[0].history_id);
        } else if (!opts.preserveDetail) {
            renderHistoryDetail(null);
        }
    }

    async function openHistoryDetail(historyId) {
        if (!currentUser || !historyId) {
            return;
        }
        var response = await window.apiClient.get('/api/auth/history/' + encodeURIComponent(historyId));
        var listEl = document.getElementById('historyList');
        if (listEl) {
            Array.prototype.forEach.call(listEl.querySelectorAll('[data-history-id]'), function (node) {
                node.classList.toggle('active', node.getAttribute('data-history-id') === historyId);
            });
        }
        renderHistoryDetail(response.data && response.data.item ? response.data.item : null);
    }

    function toggleAuthModal(show, tab) {
        var modal = document.getElementById('authModal');
        if (!modal) {
            return;
        }
        modal.classList.toggle('show', !!show);
        if (show) {
            switchTab(tab || 'login');
        }
    }

    function switchTab(tab) {
        var loginTab = document.getElementById('authTabLogin');
        var registerTab = document.getElementById('authTabRegister');
        var loginPanel = document.getElementById('authLoginPanel');
        var registerPanel = document.getElementById('authRegisterPanel');
        var isLogin = tab !== 'register';
        if (!loginTab || !registerTab || !loginPanel || !registerPanel) {
            return;
        }
        loginTab.classList.toggle('active', isLogin);
        registerTab.classList.toggle('active', !isLogin);
        loginPanel.style.display = isLogin ? '' : 'none';
        registerPanel.style.display = isLogin ? 'none' : '';
    }

    function optionalInt(id) {
        var node = document.getElementById(id);
        if (!node || node.value === '') {
            return null;
        }
        return parseInt(node.value, 10);
    }

    function parseCoordinate(raw) {
        if (typeof raw !== 'number' || !isFinite(raw)) {
            return '';
        }
        return raw.toFixed(5);
    }

    function buildApproxLocationLabel(position) {
        if (!position || !position.coords) {
            return '';
        }
        var latitude = parseCoordinate(position.coords.latitude);
        var longitude = parseCoordinate(position.coords.longitude);
        if (!latitude || !longitude) {
            return '';
        }
        return '定位坐标(' + latitude + ', ' + longitude + ')';
    }

    async function resolveHumanReadableLocation(position) {
        var fallback = buildApproxLocationLabel(position);
        if (!position || !position.coords || !window.apiClient || !window.apiClient.postJson) {
            return fallback;
        }

        try {
            var response = await window.apiClient.postJson('/api/location/reverse-geocode', {
                latitude: position.coords.latitude,
                longitude: position.coords.longitude
            });
            var data = response && response.data ? response.data : {};
            return data.human_readable || data.formatted_address || fallback;
        } catch (_error) {
            return fallback;
        }
    }

    function requestCurrentLocation(targetInputId) {
        var input = document.getElementById(targetInputId);
        if (!input) {
            return;
        }
        if (!navigator.geolocation) {
            if (window.showToast) {
                window.showToast('当前浏览器不支持地理定位。', 'warn');
            }
            return;
        }

        navigator.geolocation.getCurrentPosition(async function (position) {
            var suggested = await resolveHumanReadableLocation(position);
            if (!suggested) {
                if (window.showToast) {
                    window.showToast('定位成功，但未能生成可用地点描述。', 'warn');
                }
                return;
            }

            input.value = suggested;
            input.focus();
            if (window.showToast) {
                if (suggested.indexOf('定位坐标(') === 0) {
                    window.showToast('已获取定位坐标。若配置逆地理编码服务，可自动转成城市/街区名称。你也可以继续手动补充。', 'success');
                } else {
                    window.showToast('已填入可读地点名称，你仍可以继续手动补充到更精确的位置描述。', 'success');
                }
            }
        }, function (error) {
            var message = '定位失败';
            if (error && error.code === 1) {
                message = '你拒绝了定位权限，请允许浏览器定位后再试。';
            } else if (error && error.code === 2) {
                message = '无法获取当前位置，请检查网络或系统定位设置。';
            } else if (error && error.code === 3) {
                message = '定位超时，请稍后再试。';
            }
            if (window.showToast) {
                window.showToast(message, 'warn');
            }
        }, {
            enableHighAccuracy: false,
            timeout: 10000,
            maximumAge: 300000
        });
    }

    function bindEvents() {
        var loginBtn = document.getElementById('openAuthModalBtn');
        var accountBtn = document.getElementById('openAccountCenterBtn');
        var logoutBtn = document.getElementById('logoutBtn');
        var guestLoginBtn = document.getElementById('accountGuestLoginBtn');
        var detectProfileLocationBtn = document.getElementById('detectProfileLocationBtn');
        var modal = document.getElementById('authModal');
        var closeBtn = document.getElementById('authModalClose');
        var loginTab = document.getElementById('authTabLogin');
        var registerTab = document.getElementById('authTabRegister');
        var historyList = document.getElementById('historyList');
        var savedPresetGrid = document.getElementById('savedPresetGrid');

        if (loginBtn) {
            loginBtn.addEventListener('click', function () {
                toggleAuthModal(true, 'login');
            });
        }
        if (accountBtn) {
            accountBtn.addEventListener('click', function () {
                if (accountBtn.tagName === 'A') {
                    return;
                }
                openAccountCenter();
            });
        }
        if (logoutBtn) {
            logoutBtn.addEventListener('click', async function () {
                try {
                    await window.apiClient.post('/api/auth/logout');
                } catch (_err) {
                    // Ignore server logout errors.
                }
                setToken('');
                currentUser = null;
                consultPresets = [];
                renderHeader();
                renderAccount();
                renderHistoryList([]);
                renderHistoryDetail(null);
                renderConsultPresetGrid();
                if (window.showToast) {
                    window.showToast('已退出登录。', 'success');
                }
            });
        }
        if (guestLoginBtn) {
            guestLoginBtn.addEventListener('click', function () {
                toggleAuthModal(true, 'login');
            });
        }
        if (detectProfileLocationBtn) {
            detectProfileLocationBtn.addEventListener('click', function () {
                requestCurrentLocation('profileLocation');
            });
        }
        if (closeBtn) {
            closeBtn.addEventListener('click', function () {
                toggleAuthModal(false);
            });
        }
        if (modal) {
            modal.addEventListener('click', function (event) {
                if (event.target === modal) {
                    toggleAuthModal(false);
                }
            });
        }
        if (loginTab) {
            loginTab.addEventListener('click', function () {
                switchTab('login');
            });
        }
        if (registerTab) {
            registerTab.addEventListener('click', function () {
                switchTab('register');
            });
        }
        if (historyList) {
            historyList.addEventListener('click', function (event) {
                var target = event.target.closest('[data-history-id]');
                if (!target) {
                    return;
                }
                openHistoryDetail(target.getAttribute('data-history-id')).catch(function (error) {
                    if (window.showToast) {
                        window.showToast('读取历史失败：' + error.message, 'error');
                    }
                });
            });
        }
        if (savedPresetGrid) {
            savedPresetGrid.addEventListener('click', function (event) {
                var applyTarget = event.target.closest('[data-apply-preset]');
                if (applyTarget && window.consultPanel && window.consultPanel.applySavedCondition) {
                    window.consultPanel.applySavedCondition(applyTarget.getAttribute('data-apply-preset'));
                    return;
                }
                var defaultTarget = event.target.closest('[data-default-preset]');
                if (defaultTarget) {
                    var selected = defaultTarget.getAttribute('data-default-preset');
                    var preset = consultPresets.find(function (item) { return item.preset_id === selected; });
                    if (!preset) {
                        return;
                    }
                    saveConsultPreset({
                        preset_id: preset.preset_id,
                        name: preset.name,
                        question: preset.question,
                        year: preset.year,
                        month: preset.month,
                        day: preset.day,
                        hour: preset.hour,
                        minute: preset.minute,
                        gender: preset.gender,
                        location: preset.location,
                        is_default: true
                    }).then(function () {
                        if (window.showToast) {
                            window.showToast('已设为默认条件。', 'success');
                        }
                    }).catch(function (error) {
                        if (window.showToast) {
                            window.showToast('设置默认失败：' + error.message, 'error');
                        }
                    });
                    return;
                }
                var deleteTarget = event.target.closest('[data-delete-preset]');
                if (deleteTarget) {
                    deleteConsultPreset(deleteTarget.getAttribute('data-delete-preset')).then(function () {
                        if (window.showToast) {
                            window.showToast('常用条件已删除。', 'success');
                        }
                    }).catch(function (error) {
                        if (window.showToast) {
                            window.showToast('删除失败：' + error.message, 'error');
                        }
                    });
                }
            });
        }

        var loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', async function (event) {
                event.preventDefault();
                try {
                    var response = await window.apiClient.postJson('/api/auth/login', {
                        email: document.getElementById('loginEmail').value.trim(),
                        password: document.getElementById('loginPassword').value
                    });
                    setToken(response.data.token);
                    currentUser = response.data.user;
                    renderHeader();
                    renderAccount();
                    toggleAuthModal(false);
                    await refreshHistory();
                    await refreshConsultPresets();
                    openAccountCenter();
                    if (window.showToast) {
                        window.showToast('登录成功。', 'success');
                    }
                } catch (error) {
                    if (window.showToast) {
                        window.showToast(formatRequestError('登录失败', error), 'error');
                    }
                }
            });
        }

        var registerForm = document.getElementById('registerForm');
        if (registerForm) {
            registerForm.addEventListener('submit', async function (event) {
                event.preventDefault();
                try {
                    var response = await window.apiClient.postJson('/api/auth/register', {
                        email: document.getElementById('registerEmail').value.trim(),
                        password: document.getElementById('registerPassword').value,
                        display_name: document.getElementById('registerDisplayName').value.trim()
                    });
                    setToken(response.data.token);
                    currentUser = response.data.user;
                    renderHeader();
                    renderAccount();
                    toggleAuthModal(false);
                    await refreshHistory();
                    await refreshConsultPresets();
                    openAccountCenter();
                    if (window.showToast) {
                        window.showToast('注册成功，已自动登录。', 'success');
                    }
                } catch (error) {
                    if (window.showToast) {
                        window.showToast(formatRequestError('注册失败', error), 'error');
                    }
                }
            });
        }

        var profileForm = document.getElementById('accountProfileForm');
        if (profileForm) {
            profileForm.addEventListener('submit', async function (event) {
                event.preventDefault();
                if (!currentUser) {
                    toggleAuthModal(true, 'login');
                    return;
                }
                try {
                    var response = await window.apiClient.request('/api/auth/profile', {
                        method: 'PATCH',
                        json: {
                            display_name: document.getElementById('profileDisplayName').value.trim(),
                            gender: document.getElementById('profileGender').value || null,
                            location: document.getElementById('profileLocation').value.trim(),
                            year: optionalInt('profileYear'),
                            month: optionalInt('profileMonth'),
                            day: optionalInt('profileDay'),
                            hour: optionalInt('profileHour'),
                            minute: optionalInt('profileMinute'),
                            current_password: document.getElementById('profileCurrentPassword').value,
                            new_password: document.getElementById('profileNewPassword').value
                        }
                    });
                    currentUser = response.data.user;
                    renderHeader();
                    renderAccount();
                    renderConsultPresetGrid();
                    if (window.showToast) {
                        window.showToast('账号资料已保存。', 'success');
                    }
                } catch (error) {
                    if (window.showToast) {
                        window.showToast('保存失败：' + error.message, 'error');
                    }
                }
            });
        }
    }

    async function initialize() {
        if (initialized) {
            return;
        }
        initialized = true;
        bindEvents();
        renderHeader();
        renderAccount();
        renderHistoryList([]);
        renderHistoryDetail(null);
        renderConsultPresetGrid();
        switchTab('login');
        await refreshSession();
        if (currentUser) {
            await refreshHistory();
            await refreshConsultPresets();
            if (window.consultPanel && window.consultPanel.applyDefaultSavedCondition) {
                window.consultPanel.applyDefaultSavedCondition();
            }
        }
    }

    window.authClient = {
        initialize: initialize,
        refreshSession: refreshSession,
        refreshHistory: refreshHistory,
        refreshConsultPresets: refreshConsultPresets,
        saveConsultPreset: saveConsultPreset,
        getConsultPresets: getConsultPresets,
        getDefaultConsultPreset: getDefaultConsultPreset,
        getCurrentUserProfile: function () {
            return currentUser && currentUser.profile ? currentUser.profile : null;
        },
        isAuthenticated: function () {
            return !!currentUser;
        },
        openAuthModal: function (tab) {
            toggleAuthModal(true, tab || 'login');
        }
    };
})();
