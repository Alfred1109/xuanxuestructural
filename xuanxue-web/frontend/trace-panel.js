(function () {
    // Trace renderer: Mermaid diagram + expandable step evidence blocks.
    var renderers = window.commonRenderers || {};
    var esc = renderers.esc || function (value) { return String(value ?? ''); };
    var prettyJson = renderers.prettyJson || function (value) { return String(value ?? ''); };
    var renderTraceText = renderers.renderTraceText || function (value) { return prettyJson(value); };
    var renderTraceFieldBlock = renderers.renderTraceFieldBlock || function () { return ''; };
    var mermaidInitialized = false;
    var traceDiagramModal = null;

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

    function closeTraceDiagramModal() {
        if (!traceDiagramModal) {
            return;
        }
        traceDiagramModal.classList.remove('is-open');
        traceDiagramModal.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('trace-diagram-modal-open');
    }

    function ensureTraceDiagramModal() {
        if (traceDiagramModal) {
            return traceDiagramModal;
        }

        var modal = document.createElement('div');
        modal.className = 'trace-diagram-modal';
        modal.setAttribute('aria-hidden', 'true');
        modal.innerHTML = [
            '<div class="trace-diagram-modal-backdrop" data-trace-diagram-close></div>',
            '<div class="trace-diagram-modal-dialog" role="dialog" aria-modal="true" aria-label="计算流程放大预览">',
            '  <div class="trace-diagram-modal-head">',
            '    <div class="trace-diagram-modal-copy">',
            '      <strong>计算流程</strong>',
            '      <span>点击遮罩、右上角按钮或按 Esc 关闭</span>',
            '    </div>',
            '    <button type="button" class="trace-diagram-modal-close" aria-label="关闭放大预览" data-trace-diagram-close>关闭</button>',
            '  </div>',
            '  <div class="trace-diagram-modal-body"></div>',
            '</div>'
        ].join('');

        modal.addEventListener('click', function (event) {
            if (event.target && event.target.hasAttribute('data-trace-diagram-close')) {
                closeTraceDiagramModal();
            }
        });

        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape' && traceDiagramModal && traceDiagramModal.classList.contains('is-open')) {
                closeTraceDiagramModal();
            }
        });

        document.body.appendChild(modal);
        traceDiagramModal = modal;
        return modal;
    }

    function openTraceDiagramModal(svgMarkup) {
        if (!svgMarkup) {
            return;
        }

        var modal = ensureTraceDiagramModal();
        var body = modal.querySelector('.trace-diagram-modal-body');
        body.innerHTML = svgMarkup;
        modal.classList.add('is-open');
        modal.setAttribute('aria-hidden', 'false');
        document.body.classList.add('trace-diagram-modal-open');
    }

    function bindTraceDiagramPreview(mountEl, svgMarkup) {
        var svgEl = mountEl.querySelector('svg');
        mountEl.classList.remove('is-interactive');
        mountEl.removeAttribute('role');
        mountEl.removeAttribute('tabindex');
        mountEl.removeAttribute('aria-label');
        mountEl.removeAttribute('title');
        mountEl.onclick = null;
        mountEl.onkeydown = null;

        if (!svgEl || !svgMarkup) {
            return;
        }

        mountEl.classList.add('is-interactive');
        mountEl.setAttribute('role', 'button');
        mountEl.setAttribute('tabindex', '0');
        mountEl.setAttribute('aria-label', '点击放大查看计算流程图');
        mountEl.setAttribute('title', '点击放大查看');
        mountEl.onclick = function () {
            openTraceDiagramModal(svgMarkup);
        };
        mountEl.onkeydown = function (event) {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                openTraceDiagramModal(svgMarkup);
            }
        };
    }

    async function renderTraceDiagram(trace, mountEl) {
        var source = trace && trace.mermaid ? String(trace.mermaid) : '';
        bindTraceDiagramPreview(mountEl, '');
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
            bindTraceDiagramPreview(mountEl, rendered.svg);
        } catch (_error) {
            mountEl.innerHTML = '<pre class="trace-fallback">' + esc(source) + '</pre>';
        }
    }

    function renderTraceSteps(trace, mountEl) {
        var steps = Array.isArray(trace && trace.steps) ? trace.steps : [];
        mountEl.innerHTML = steps.map(function (step, index) {
            var fields = [];
            if (step.inputs && Object.keys(step.inputs).length) {
                fields.push(renderTraceFieldBlock('输入', renderTraceText(step.inputs), ''));
            }
            if (Array.isArray(step.formulas) && step.formulas.length) {
                fields.push(renderTraceFieldBlock('公式', step.formulas.join('\n'), 'formula'));
            }
            if (step.rule) {
                fields.push(renderTraceFieldBlock('规则', step.rule, ''));
            }
            if (step.derivation && Object.keys(step.derivation).length) {
                fields.push(renderTraceFieldBlock('推导', renderTraceText(step.derivation), ''));
            }
            if (step.outputs && Object.keys(step.outputs).length) {
                fields.push(renderTraceFieldBlock('输出', renderTraceText(step.outputs), ''));
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
