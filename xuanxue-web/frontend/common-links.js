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
        applyNavLink('[data-ai-guide-link]', '../../AI配置指南.md');
    };
})();
