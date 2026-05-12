(function () {
    function esc(value) {
        return window.escapeHtml ? window.escapeHtml(value ?? '') : String(value ?? '');
    }

    function prettyJson(value) {
        return esc(JSON.stringify(value ?? {}, null, 2));
    }

    function renderMetricBar(label, value) {
        var numeric = Math.max(0, Math.min(100, Number(value) || 0));
        return [
            '<div class="metric-bar">',
            '  <div class="row"><span>' + esc(label) + '</span><span>' + numeric.toFixed(1) + '</span></div>',
            '  <div class="track"><div class="fill" style="width: ' + numeric + '%;"></div></div>',
            '</div>'
        ].join('');
    }

    function renderDecisionCard(title, body, extra) {
        return [
            '<div class="decision-card">',
            '  <div class="title">' + esc(title) + '</div>',
            '  <div class="body">' + esc(body) + '</div>',
            extra || '',
            '</div>'
        ].join('');
    }

    function renderTraceFieldBlock(title, value, className) {
        return [
            '<div class="trace-field">',
            '  <div class="field-title' + (className ? ' ' + className : '') + '">' + esc(title) + '</div>',
            '  <pre' + (className === 'formula' ? ' class="formula-block"' : '') + '>' + esc(value) + '</pre>',
            '</div>'
        ].join('');
    }

    window.commonRenderers = {
        esc: esc,
        prettyJson: prettyJson,
        renderDecisionCard: renderDecisionCard,
        renderMetricBar: renderMetricBar,
        renderTraceFieldBlock: renderTraceFieldBlock
    };
})();
