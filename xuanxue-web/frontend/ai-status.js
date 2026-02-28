(function () {
    function normalizeStatus(data) {
        if (data && data.status) {
            return data.status;
        }
        if (data && data.available) {
            return "available";
        }
        return "unconfigured";
    }

    function setStatusUI(opts, state, data, previous) {
        var banner = document.getElementById(opts.bannerId);
        var dot = document.getElementById(opts.dotId);
        var text = document.getElementById(opts.textId);
        var detail = opts.detailId ? document.getElementById(opts.detailId) : null;
        if (!banner || !dot || !text) {
            return;
        }

        if (typeof opts.renderStatus === "function") {
            opts.renderStatus(state, data || {}, previous || "unknown", {
                banner: banner,
                dot: dot,
                text: text,
                detail: detail
            });
            return;
        }

        banner.className = "ai-status-banner " + state;
        dot.className = "ai-status-dot";

        if (state === "available") {
            text.textContent = "AI服务正常";
            if (detail) {
                detail.textContent = data && data.model ? ("模型: " + data.model) : "模型信息不可用";
            }
        } else if (state === "degraded") {
            text.textContent = "AI服务波动中";
            if (detail) {
                detail.textContent = data && data.message ? data.message : "系统将自动回退基础解读";
            }
        } else if (state === "unconfigured") {
            text.textContent = "AI服务未配置";
            if (detail) {
                detail.textContent = "请配置ARK_API_KEY";
            }
        } else {
            text.textContent = "后端连接异常";
            if (detail) {
                detail.textContent = "请检查后端服务与端口";
            }
        }
    }

    function createAIStatusMonitor(options) {
        var opts = options || {};
        var currentState = "unknown";
        var timer = null;

        function applyState(state, data) {
            var previous = currentState;
            currentState = state;
            setStatusUI(opts, state, data || {}, previous);
            if (typeof opts.onTransition === "function" && previous !== state) {
                opts.onTransition(state, previous, data || {});
            }
        }

        async function refresh() {
            try {
                var result = await window.apiClient.get("/api/ai/status");
                var data = result && result.data ? result.data : {};
                applyState(normalizeStatus(data), data);
            } catch (_err) {
                applyState("offline", {});
            }
        }

        function start() {
            refresh();
            var interval = opts.intervalMs || 30000;
            timer = setInterval(refresh, interval);
        }

        function stop() {
            if (timer) {
                clearInterval(timer);
                timer = null;
            }
        }

        return {
            start: start,
            stop: stop,
            refresh: refresh,
            applyState: applyState,
            getState: function () {
                return currentState;
            }
        };
    }

    window.createAIStatusMonitor = createAIStatusMonitor;
})();
