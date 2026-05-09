(function () {
    var params = new URLSearchParams(window.location.search);
    var queryBase = params.get('apiBase');
    var defaultBase = window.location.protocol + '//' + window.location.hostname + ':8002';
    var defaultDocsBase = window.location.protocol + '//' + window.location.hostname + ':8004';
    var queryDocsBase = params.get('docsBase');
    var queryGuideUrl = params.get('guideUrl');

    window.APP_CONFIG = {
        API_BASE_URL: queryBase || defaultBase,
        DOCS_BASE_URL: queryDocsBase || defaultDocsBase,
        AI_GUIDE_URL: queryGuideUrl || '../../AI配置指南.md'
    };
})();
