(function () {
    function getBaseUrl() {
        if (window.APP_CONFIG && window.APP_CONFIG.API_BASE_URL) {
            return window.APP_CONFIG.API_BASE_URL;
        }
        return window.location.protocol + '//' + window.location.hostname + ':8002';
    }

    function buildUrl(path, query) {
        var base = getBaseUrl();
        var normalizedPath = path.charAt(0) === '/' ? path : '/' + path;
        var url = new URL(base + normalizedPath);

        if (query) {
            Object.keys(query).forEach(function (key) {
                var value = query[key];
                if (value !== undefined && value !== null) {
                    url.searchParams.set(key, String(value));
                }
            });
        }

        return url.toString();
    }

    async function request(path, options) {
        var opts = options || {};
        var method = opts.method || 'GET';
        var headers = Object.assign({}, opts.headers || {});
        var body = opts.body;

        if (opts.json !== undefined) {
            headers['Content-Type'] = 'application/json';
            body = JSON.stringify(opts.json);
        }

        var response = await fetch(buildUrl(path, opts.query), {
            method: method,
            headers: headers,
            body: body
        });

        var payload = null;
        try {
            payload = await response.json();
        } catch (_err) {
            payload = null;
        }

        if (!response.ok) {
            var structured = payload && payload.error ? payload.error : null;
            var detail = structured
                ? (structured.message || structured.detail)
                : (payload && (payload.detail || payload.message));
            var err = new Error(detail || ('API请求失败 (' + response.status + ')'));
            if (structured && structured.code) {
                err.code = structured.code;
            }
            throw err;
        }

        return payload;
    }

    window.apiClient = {
        request: request,
        get: function (path, query) {
            return request(path, { method: 'GET', query: query });
        },
        post: function (path, query) {
            return request(path, { method: 'POST', query: query });
        },
        postJson: function (path, json) {
            return request(path, { method: 'POST', json: json });
        }
    };
})();
