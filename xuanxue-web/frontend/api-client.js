(function () {
    var AUTH_TOKEN_KEY = 'xuanxue_auth_token';

    function isMountedUnderXuanxue() {
        var path = String(window.location.pathname || '');
        return path === '/xuanxue' || path.indexOf('/xuanxue/') === 0;
    }

    function getBaseUrl() {
        var config = window.APP_CONFIG || {};
        if (isMountedUnderXuanxue() && !config.API_BASE_URL_FROM_QUERY) {
            return window.location.origin + '/xuanxue-api';
        }
        return config.API_BASE_URL || window.location.origin;
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
        var token = '';
        var timeoutMs = Number.isFinite(opts.timeoutMs) ? opts.timeoutMs : 45000;
        var controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
        var timedOut = false;
        var timeoutId = null;
        var abortRelay = null;

        try {
            token = window.localStorage.getItem(AUTH_TOKEN_KEY) || '';
        } catch (_err) {
            token = '';
        }

        if (opts.json !== undefined) {
            headers['Content-Type'] = 'application/json';
            body = JSON.stringify(opts.json);
        }

        if (token && !headers.Authorization && !headers.authorization) {
            headers.Authorization = 'Bearer ' + token;
        }

        if (controller && opts.signal) {
            if (opts.signal.aborted) {
                controller.abort();
            } else {
                abortRelay = function () { controller.abort(); };
                opts.signal.addEventListener('abort', abortRelay, { once: true });
            }
        }
        if (controller && timeoutMs > 0) {
            timeoutId = window.setTimeout(function () {
                timedOut = true;
                controller.abort();
            }, timeoutMs);
        }

        var response;
        try {
            response = await fetch(buildUrl(path, opts.query), {
                method: method,
                headers: headers,
                body: body,
                signal: controller ? controller.signal : opts.signal
            });
        } catch (error) {
            if (timedOut) {
                var timeoutError = new Error('请求超时，请检查网络后重试');
                timeoutError.code = 'request_timeout';
                throw timeoutError;
            }
            if (error && error.name === 'AbortError') {
                var abortError = new Error('请求已取消');
                abortError.code = 'request_aborted';
                throw abortError;
            }
            throw error;
        } finally {
            if (timeoutId) {
                window.clearTimeout(timeoutId);
            }
            if (abortRelay && opts.signal) {
                opts.signal.removeEventListener('abort', abortRelay);
            }
        }

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
            err.status = response.status;
            err.payload = payload;
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
        post: function (path, data, options) {
            if (data !== undefined) {
                return request(path, Object.assign({}, options || {}, { method: 'POST', json: data }));
            }
            return request(path, Object.assign({}, options || {}, { method: 'POST' }));
        },
        postJson: function (path, json, options) {
            return request(path, Object.assign({}, options || {}, { method: 'POST', json: json }));
        }
    };
})();
