(function () {
    // Trace renderer: Mermaid diagram + expandable step evidence blocks.
    var renderers = window.commonRenderers || {};
    var esc = renderers.esc || function (value) { return String(value ?? ''); };
    var prettyJson = renderers.prettyJson || function (value) { return String(value ?? ''); };
    var renderTraceFieldBlock = renderers.renderTraceFieldBlock || function () { return ''; };
    var mermaidInitialized = false;

    function ensureMermaid() {
        if (!window.mermaid) {
            return false;
        }
        if (!mermaidInitialized) {
            window.mermaid.initialize({
                startOnLoad: false,
                securityLevel: 'strict',
                theme: 'base',
                themeVariables: {
                    primaryColor: '#f4efe5',
                    primaryTextColor: '#173a34',
                    primaryBorderColor: '#94b3a7',
                    lineColor: '#7c958b',
                    secondaryColor: '#fff5e5',
                    tertiaryColor: '#ffffff',
                    fontFamily: 'PingFang SC, Microsoft YaHei, sans-serif'
                }
            });
            mermaidInitialized = true;
        }
        return true;
    }

    async function renderTraceDiagram(trace, mountEl) {
        var source = trace && trace.mermaid ? String(trace.mermaid) : '';
        mountEl.innerHTML = '';
        if (!source) {
            mountEl.innerHTML = '<p class="trace-fallback">暂无计算流程。</p>';
            return;
        }

        if (!ensureMermaid()) {
            mountEl.innerHTML = '<pre class="trace-fallback">' + esc(source) + '</pre>';
            return;
        }

        try {
            var diagramId = 'consult-trace-' + Date.now();
            var rendered = await window.mermaid.render(diagramId, source);
            mountEl.innerHTML = rendered.svg;
        } catch (_error) {
            mountEl.innerHTML = '<pre class="trace-fallback">' + esc(source) + '</pre>';
        }
    }

    function renderTraceSteps(trace, mountEl) {
        var steps = Array.isArray(trace && trace.steps) ? trace.steps : [];
        mountEl.innerHTML = steps.map(function (step, index) {
            var fields = [];
            if (step.inputs && Object.keys(step.inputs).length) {
                fields.push(renderTraceFieldBlock('输入', prettyJson(step.inputs), ''));
            }
            if (Array.isArray(step.formulas) && step.formulas.length) {
                fields.push(renderTraceFieldBlock('公式', step.formulas.join('\n'), 'formula'));
            }
            if (step.rule) {
                fields.push(renderTraceFieldBlock('规则', step.rule, ''));
            }
            if (step.derivation && Object.keys(step.derivation).length) {
                fields.push(renderTraceFieldBlock('推导', prettyJson(step.derivation), ''));
            }
            if (step.outputs && Object.keys(step.outputs).length) {
                fields.push(renderTraceFieldBlock('输出', prettyJson(step.outputs), ''));
            }
            if (Array.isArray(step.evidence) && step.evidence.length) {
                fields.push(renderTraceFieldBlock('证据', step.evidence.join('\n'), ''));
            }
            return [
                '<details class="trace-step" ' + (index === 0 ? 'open' : '') + '>',
                '  <summary class="trace-step-summary">',
                '    <span class="trace-step-index">' + String(index + 1).padStart(2, '0') + '</span>',
                '    <span class="trace-step-copy">',
                '      <span class="label">' + esc(step.label || step.id || '步骤') + '</span>',
                '      <span class="summary">' + esc(step.detail || '') + '</span>',
                '    </span>',
                '    <span class="trace-step-state"></span>',
                '  </summary>',
                '  <div class="trace-step-body">' + fields.join('') + '</div>',
                '</details>'
            ].join('');
        }).join('');
    }

    window.tracePanel = {
        renderDiagram: renderTraceDiagram,
        renderSteps: renderTraceSteps
    };
})();
