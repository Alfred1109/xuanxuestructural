(function () {
    var params = new URLSearchParams(window.location.search);
    var queryBase = params.get('apiBase');
    var defaultBase = window.location.protocol + '//' + window.location.hostname + ':8002';

    window.APP_CONFIG = {
        API_BASE_URL: queryBase || defaultBase
    };
})();
