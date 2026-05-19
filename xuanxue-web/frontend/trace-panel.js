(function () {
    // Trace renderer: Mermaid diagram + expandable step evidence blocks.
    var renderers = window.commonRenderers || {};
    var esc = renderers.esc || function (value) { return String(value ?? ''); };
    var prettyJson = renderers.prettyJson || function (value) { return String(value ?? ''); };
    var renderTraceText = renderers.renderTraceText || function (value) { return prettyJson(value); };
    var renderTraceFieldBlock = renderers.renderTraceFieldBlock || function () { return ''; };
    var mermaidInitialized = false;
    var traceDiagramModal = null;
    var currentTraceSvgMarkup = '';
    var traceViewportState = {
        scale: 1,
        minScale: 0.5,
        maxScale: 3.5,
        translateX: 0,
        translateY: 0,
        dragging: false,
        lastX: 0,
        lastY: 0
    };

    function clamp(value, min, max) {
        return Math.min(max, Math.max(min, value));
    }

    function getTraceViewportParts() {
        if (!traceDiagramModal) {
            return {};
        }
        return {
            body: traceDiagramModal.querySelector('.trace-diagram-modal-body'),
            viewport: traceDiagramModal.querySelector('.trace-diagram-modal-viewport'),
            canvas: traceDiagramModal.querySelector('.trace-diagram-modal-canvas'),
            scaleLabel: traceDiagramModal.querySelector('[data-trace-diagram-scale]')
        };
    }

    function updateTraceViewportTransform() {
        var parts = getTraceViewportParts();
        if (!parts.canvas) {
            return;
        }
        parts.canvas.style.transform = 'translate(' + traceViewportState.translateX + 'px, ' + traceViewportState.translateY + 'px) scale(' + traceViewportState.scale + ')';
        if (parts.scaleLabel) {
            parts.scaleLabel.textContent = Math.round(traceViewportState.scale * 100) + '%';
        }
        if (parts.viewport) {
            parts.viewport.classList.toggle('is-grabbing', !!traceViewportState.dragging);
            parts.viewport.classList.toggle('is-zoomed', traceViewportState.scale > 1.001);
        }
    }

    function resetTraceViewport() {
        traceViewportState.scale = 1;
        traceViewportState.translateX = 0;
        traceViewportState.translateY = 0;
        traceViewportState.dragging = false;
        updateTraceViewportTransform();
    }

    function zoomTraceViewport(nextScale, anchorX, anchorY) {
        var parts = getTraceViewportParts();
        if (!parts.viewport || !parts.canvas) {
            return;
        }
        var rect = parts.viewport.getBoundingClientRect();
        var clampedScale = clamp(nextScale, traceViewportState.minScale, traceViewportState.maxScale);
        var prevScale = traceViewportState.scale;
        if (clampedScale === prevScale) {
            return;
        }

        var localX = anchorX - rect.left;
        var localY = anchorY - rect.top;
        var contentX = (localX - traceViewportState.translateX) / prevScale;
        var contentY = (localY - traceViewportState.translateY) / prevScale;

        traceViewportState.scale = clampedScale;
        traceViewportState.translateX = localX - contentX * clampedScale;
        traceViewportState.translateY = localY - contentY * clampedScale;
        updateTraceViewportTransform();
    }

    function fitTraceViewportToPoint(targetScale, anchorX, anchorY) {
        var parts = getTraceViewportParts();
        if (!parts.viewport) {
            return;
        }
        var rect = parts.viewport.getBoundingClientRect();
        var fallbackX = rect.left + rect.width / 2;
        var fallbackY = rect.top + rect.height / 2;
        zoomTraceViewport(targetScale, anchorX || fallbackX, anchorY || fallbackY);
    }

    function bindTraceViewportInteractions() {
        var parts = getTraceViewportParts();
        if (!parts.viewport || !parts.canvas || parts.viewport.dataset.bound === 'true') {
            updateTraceViewportTransform();
            return;
        }

        parts.viewport.dataset.bound = 'true';

        parts.viewport.addEventListener('wheel', function (event) {
            event.preventDefault();
            var step = event.ctrlKey ? 1.06 : 1.14;
            var delta = event.deltaY < 0 ? step : 1 / step;
            zoomTraceViewport(traceViewportState.scale * delta, event.clientX, event.clientY);
        }, { passive: false });

        parts.viewport.addEventListener('dblclick', function (event) {
            event.preventDefault();
            var targetScale = traceViewportState.scale < 1.6 ? 2 : 1;
            if (targetScale === 1) {
                resetTraceViewport();
                return;
            }
            fitTraceViewportToPoint(targetScale, event.clientX, event.clientY);
        });

        parts.viewport.addEventListener('pointerdown', function (event) {
            if (event.button !== 0) {
                return;
            }
            traceViewportState.dragging = true;
            traceViewportState.lastX = event.clientX;
            traceViewportState.lastY = event.clientY;
            if (parts.viewport.setPointerCapture) {
                parts.viewport.setPointerCapture(event.pointerId);
            }
            updateTraceViewportTransform();
        });

        parts.viewport.addEventListener('pointermove', function (event) {
            if (!traceViewportState.dragging) {
                return;
            }
            traceViewportState.translateX += event.clientX - traceViewportState.lastX;
            traceViewportState.translateY += event.clientY - traceViewportState.lastY;
            traceViewportState.lastX = event.clientX;
            traceViewportState.lastY = event.clientY;
            updateTraceViewportTransform();
        });

        function stopDragging(event) {
            if (!traceViewportState.dragging) {
                return;
            }
            traceViewportState.dragging = false;
            if (parts.viewport.releasePointerCapture && event && event.pointerId !== undefined) {
                try {
                    parts.viewport.releasePointerCapture(event.pointerId);
                } catch (_error) {}
            }
            updateTraceViewportTransform();
        }

        parts.viewport.addEventListener('pointerup', stopDragging);
        parts.viewport.addEventListener('pointercancel', stopDragging);
        parts.viewport.addEventListener('pointerleave', stopDragging);

        updateTraceViewportTransform();
    }

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
        resetTraceViewport();
        traceDiagramModal.classList.remove('is-open');
        traceDiagramModal.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('trace-diagram-modal-open');
    }

    function downloadTraceDiagram() {
        if (!currentTraceSvgMarkup) {
            return;
        }
        try {
            var blob = new Blob([currentTraceSvgMarkup], { type: 'image/svg+xml;charset=utf-8' });
            var url = URL.createObjectURL(blob);
            var link = document.createElement('a');
            link.href = url;
            link.download = 'consult-trace-diagram.svg';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.setTimeout(function () {
                URL.revokeObjectURL(url);
            }, 0);
        } catch (_error) {
            // Ignore download errors silently; preview remains usable.
        }
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
            '    <div class="trace-diagram-modal-actions">',
            '      <span class="trace-diagram-modal-scale" data-trace-diagram-scale>100%</span>',
            '      <button type="button" class="trace-diagram-modal-reset" aria-label="重置缩放" data-trace-diagram-reset>重置</button>',
            '      <button type="button" class="trace-diagram-modal-download" aria-label="下载流程图" data-trace-diagram-download>下载 SVG</button>',
            '      <button type="button" class="trace-diagram-modal-close" aria-label="关闭放大预览" data-trace-diagram-close>关闭</button>',
            '    </div>',
            '  </div>',
            '  <div class="trace-diagram-modal-body">',
            '    <div class="trace-diagram-modal-viewport">',
            '      <div class="trace-diagram-modal-canvas"></div>',
            '    </div>',
            '  </div>',
            '</div>'
        ].join('');

        modal.addEventListener('click', function (event) {
            if (event.target && event.target.hasAttribute('data-trace-diagram-reset')) {
                resetTraceViewport();
                return;
            }
            if (event.target && event.target.hasAttribute('data-trace-diagram-download')) {
                downloadTraceDiagram();
                return;
            }
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
        bindTraceViewportInteractions();
        return modal;
    }

    function openTraceDiagramModal(svgMarkup) {
        if (!svgMarkup) {
            return;
        }

        currentTraceSvgMarkup = svgMarkup;
        var modal = ensureTraceDiagramModal();
        var canvas = modal.querySelector('.trace-diagram-modal-canvas');
        if (!canvas) {
            return;
        }
        canvas.innerHTML = svgMarkup;
        resetTraceViewport();
        modal.classList.add('is-open');
        modal.setAttribute('aria-hidden', 'false');
        document.body.classList.add('trace-diagram-modal-open');
        updateTraceViewportTransform();
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
