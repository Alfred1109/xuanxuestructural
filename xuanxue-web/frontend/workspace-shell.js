(function () {
    // Workspace shell: sidebar-driven view switching for overview and embedded module pages.
    var WORKSPACE_VIEWS = {
        overview: {
            title: '总览',
            desc: '在左侧切换模块，右侧统一查看对应页面与分析内容。',
            pill: '总览',
            mode: 'overview'
        },
        bazi: {
            title: '八字排盘',
            desc: '定位到出生信息录入区，继续查看命盘、五行、十神与大运分析。',
            pill: '八字',
            mode: 'overview',
            scrollTarget: 'baziForm'
        },
        ziwei: {
            title: '紫微斗数',
            desc: '补充命宫、身宫、主星与四化视角，强化长期结构判断。',
            pill: '紫微',
            mode: 'frame',
            url: 'ziwei.html?embed=1'
        },
        fengshui: {
            title: '风水 / 空间',
            desc: '从朝向、布局与场景结构评估空间支持度与风险点。',
            pill: '风水',
            mode: 'frame',
            url: 'fengshui.html?embed=1'
        },
        liuyao: {
            title: '六爻占卜',
            desc: '围绕单一问题做即时起卦与结构解读。',
            pill: '六爻',
            mode: 'frame',
            url: 'liuyao.html?embed=1'
        },
        meihua: {
            title: '梅花易数',
            desc: '通过时间或数字快速起卦，适合灵感式、轻量级即时问事。',
            pill: '梅花',
            mode: 'frame',
            url: 'meihua.html?embed=1'
        },
        qimen: {
            title: '奇门遁甲',
            desc: '观察时空盘局、九宫信息与方向策略。',
            pill: '奇门',
            mode: 'frame',
            url: 'qimen.html?embed=1'
        },
        zeri: {
            title: '择日学',
            desc: '查看今日运势并检索适合不同用途的时间。',
            pill: '择日',
            mode: 'frame',
            url: 'zeri.html?embed=1'
        },
        'ai-chat': {
            title: 'AI助手',
            desc: '把各模块结果串起来，做统一问答与辅助解释。',
            pill: 'AI',
            mode: 'frame',
            url: 'ai-chat.html?embed=1'
        }
    };

    function syncViewQuery(view) {
        var url = new URL(window.location.href);
        url.searchParams.set('view', view);
        window.history.replaceState({}, '', url.toString());
    }

    function initializeWorkspaceShell() {
        var overviewPanel = document.getElementById('overviewPanel');
        var moduleFrame = document.getElementById('moduleFrame');
        var viewTitleEl = document.getElementById('viewTitle');
        var viewDescEl = document.getElementById('viewDesc');
        var viewPillEl = document.getElementById('viewPill');
        var sidebarButtons = Array.from(document.querySelectorAll('#sidebarNav .sidebar-item'));

        if (!overviewPanel || !moduleFrame || !viewTitleEl || !viewDescEl || !viewPillEl || !sidebarButtons.length) {
            return;
        }

        function markActiveView(view) {
            sidebarButtons.forEach(function (button) {
                button.classList.toggle('active', button.dataset.view === view);
            });
        }

        function openWorkspaceView(view, options) {
            var resolvedView = WORKSPACE_VIEWS[view] ? view : 'overview';
            var config = WORKSPACE_VIEWS[resolvedView];
            var shouldSync = !options || options.syncHistory !== false;

            markActiveView(resolvedView);
            viewTitleEl.textContent = config.title;
            viewDescEl.textContent = config.desc;
            viewPillEl.textContent = config.pill;

            if (config.mode === 'frame') {
                overviewPanel.classList.add('hide');
                moduleFrame.classList.add('show');
                if (moduleFrame.getAttribute('src') !== config.url) {
                    moduleFrame.setAttribute('src', config.url);
                }
            } else {
                overviewPanel.classList.remove('hide');
                moduleFrame.classList.remove('show');
                if (config.scrollTarget) {
                    window.setTimeout(function () {
                        var target = document.getElementById(config.scrollTarget);
                        if (target) {
                            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        }
                    }, 80);
                }
            }

            if (shouldSync) {
                syncViewQuery(resolvedView);
            }
        }

        sidebarButtons.forEach(function (button) {
            button.addEventListener('click', function () {
                openWorkspaceView(button.dataset.view);
            });
        });

        openWorkspaceView(new URLSearchParams(window.location.search).get('view') || 'overview', {
            syncHistory: false
        });

        window.workspaceShell = {
            openWorkspaceView: openWorkspaceView,
            views: WORKSPACE_VIEWS
        };
    }

    window.initializeWorkspaceShell = initializeWorkspaceShell;
})();
