(function () {
    function getConfig() {
        return window.APP_CONFIG || {};
    }

    function isEmbedMode() {
        try {
            return new URLSearchParams(window.location.search).get('embed') === '1';
        } catch (_err) {
            return false;
        }
    }

    function currentPageName() {
        var path = String(window.location.pathname || '');
        var page = path.split('/').pop();
        return page || 'index.html';
    }

    function createProductNavigation() {
        if (isEmbedMode() || document.getElementById('productNav')) {
            return;
        }

        var title = document.querySelector('.unified-header .site-title');
        if (!title) {
            return;
        }

        var page = currentPageName();
        var toolPages = ['ziwei.html', 'liuyao.html', 'meihua.html', 'qimen.html', 'zeri.html', 'fengshui.html', 'ai-chat.html'];
        var nav = document.createElement('nav');
        nav.id = 'productNav';
        nav.className = 'product-nav';
        nav.setAttribute('aria-label', '主导航');
        nav.innerHTML = [
            '<a class="product-nav-link' + (page === 'index.html' ? ' is-active' : '') + '" href="index.html"' + (page === 'index.html' ? ' aria-current="page"' : '') + '>发起问事</a>',
            '<a class="product-nav-link' + (page === 'consult-result.html' ? ' is-active' : '') + '" href="consult-result.html"' + (page === 'consult-result.html' ? ' aria-current="page"' : '') + '>结果工作台</a>',
            '<details class="product-nav-tools' + (toolPages.indexOf(page) !== -1 ? ' is-active' : '') + '">',
            '  <summary>工具箱</summary>',
            '  <div class="product-nav-menu">',
            '    <a href="ziwei.html">紫微</a><a href="liuyao.html">六爻</a><a href="meihua.html">梅花易数</a>',
            '    <a href="qimen.html">奇门遁甲</a><a href="zeri.html">择日</a><a href="fengshui.html">风水</a><a href="ai-chat.html">AI 解读</a>',
            '  </div>',
            '</details>',
            '<a class="product-nav-link' + (page === 'account.html' ? ' is-active' : '') + '" href="account.html"' + (page === 'account.html' ? ' aria-current="page"' : '') + '>我的档案</a>'
        ].join('');
        title.insertAdjacentElement('afterend', nav);
    }

    function applyNavLink(selector, fallbackUrl) {
        var node = document.querySelector(selector);
        if (!node) {
            return;
        }

        var href = fallbackUrl;
        if (selector === '[data-ai-guide-link]') {
            href = getConfig().AI_GUIDE_URL || fallbackUrl;
        }

        node.setAttribute('href', href);
    }

    window.applyCommonLinks = function () {
        if (isEmbedMode() && document.body) {
            document.body.classList.add('embed-page');
        }
        createProductNavigation();
        applyNavLink('[data-ai-guide-link]', '../../AI配置指南.md');
        // Preserve local/proxied API configuration through ordinary navigation and embedded tools.
        document.querySelectorAll('a[href], iframe[src]').forEach(function (node) {
            var attr = node.tagName === 'IFRAME' ? 'src' : 'href';
            var raw = node.getAttribute(attr);
            if (!raw || raw.charAt(0) === '#') { return; }
            var target = new URL(raw, window.location.href);
            if (target.origin !== window.location.origin || !target.pathname.endsWith('.html')) { return; }
            var current = new URLSearchParams(window.location.search);
            ['apiBase', 'guideUrl'].forEach(function (name) {
                if (current.has(name)) { target.searchParams.set(name, current.get(name)); }
            });
            node.setAttribute(attr, target.toString());
        });
    };
})();
