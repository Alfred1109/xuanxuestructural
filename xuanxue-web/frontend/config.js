(function () {
    var params = new URLSearchParams(window.location.search);
    var queryBase = params.get('apiBase');
    var isMountedUnderXuanxue = window.location.pathname === '/xuanxue' ||
        window.location.pathname.indexOf('/xuanxue/') === 0;
    var defaultBase = isMountedUnderXuanxue
        ? window.location.origin + '/xuanxue-api'
        : window.location.origin;
    var queryGuideUrl = params.get('guideUrl');

    window.APP_CONFIG = {
        API_BASE_URL: queryBase || defaultBase,
        API_BASE_URL_FROM_QUERY: Boolean(queryBase),
        AI_GUIDE_URL: queryGuideUrl || '../../AI配置指南.md'
    };
})();
