(function () {
    function escapeHtml(value) {
        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function ensureToastStyles() {
        if (document.getElementById('global-toast-style')) {
            return;
        }

        var style = document.createElement('style');
        style.id = 'global-toast-style';
        style.textContent = [
            '.global-toast-wrap {',
            '  position: fixed;',
            '  top: 16px;',
            '  right: 16px;',
            '  z-index: 9999;',
            '  display: flex;',
            '  flex-direction: column;',
            '  gap: 10px;',
            '  max-width: min(92vw, 460px);',
            '}',
            '.global-toast {',
            '  color: #fff;',
            '  border-radius: 10px;',
            '  padding: 12px 14px;',
            '  font-size: 14px;',
            '  line-height: 1.5;',
            '  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.22);',
            '  white-space: pre-line;',
            '  animation: toastIn 0.2s ease-out;',
            '}',
            '.global-toast.error { background: #d32f2f; }',
            '.global-toast.warn { background: #ed6c02; }',
            '.global-toast.info { background: #0288d1; }',
            '.global-toast.success { background: #2e7d32; }',
            '@keyframes toastIn {',
            '  from { opacity: 0; transform: translateY(-8px); }',
            '  to { opacity: 1; transform: translateY(0); }',
            '}'
        ].join('');

        document.head.appendChild(style);
    }

    function getToastWrap() {
        var wrap = document.getElementById('global-toast-wrap');
        if (!wrap) {
            wrap = document.createElement('div');
            wrap.id = 'global-toast-wrap';
            wrap.className = 'global-toast-wrap';
            document.body.appendChild(wrap);
        }
        return wrap;
    }

    function showToast(message, type, duration) {
        ensureToastStyles();
        var wrap = getToastWrap();
        var toast = document.createElement('div');
        var toastType = type || 'info';
        var ttl = Number.isFinite(duration) ? duration : 4500;

        toast.className = 'global-toast ' + toastType;
        toast.textContent = message || '';
        wrap.appendChild(toast);

        window.setTimeout(function () {
            if (toast && toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, ttl);
    }

    window.showToast = showToast;
    window.escapeHtml = escapeHtml;
})();
