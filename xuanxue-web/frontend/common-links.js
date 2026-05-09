(function () {
    function getConfig() {
        return window.APP_CONFIG || {};
    }

    function applyNavLink(selector, fallbackUrl) {
        var node = document.querySelector(selector);
        if (!node) {
            return;
        }

        var href = fallbackUrl;
        if (selector === '[data-docs-link]') {
            href = getConfig().DOCS_BASE_URL || fallbackUrl;
        } else if (selector === '[data-ai-guide-link]') {
            href = getConfig().AI_GUIDE_URL || fallbackUrl;
        }

        node.setAttribute('href', href);
    }

    window.applyCommonLinks = function () {
        applyNavLink('[data-docs-link]', 'http://localhost:8004');
        applyNavLink('[data-ai-guide-link]', '../../AI配置指南.md');
    };
})();
