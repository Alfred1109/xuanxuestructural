(function () {
    // Decision kernel renderer: focuses on arbitration cards and metric bars only.
    var renderers = window.commonRenderers || {};
    var esc = renderers.esc || function (value) { return String(value ?? ''); };
    var renderMetricBar = renderers.renderMetricBar || function () { return ''; };
    var renderDecisionCard = renderers.renderDecisionCard || function () { return ''; };
    var translateStringValue = renderers.translateStringValue || function (value) { return String(value ?? ''); };
    var formatOneDecimal = renderers.formatOneDecimal || function (value) {
        var numeric = Number(value);
        return Number.isFinite(numeric) ? numeric.toFixed(1) : String(value ?? '');
    };

    function formatWeight(value) {
        var numeric = Number(value);
        return Number.isFinite(numeric) ? numeric.toFixed(1) : String(value ?? '');
    }

    function renderDecisionPanel(payload, mountEl) {
        if (!mountEl) {
            return;
        }

        var decisionKernel = (payload && payload.decision_kernel) || {};
        var arbitration = decisionKernel.arbitration || {};
        var environment = decisionKernel.environment || {};
        var worldModel = decisionKernel.world_model || {};
        var weightedScores = arbitration.weighted_scores || {};
        var recommendation = arbitration.recommendation || {};
        var entropy = arbitration.entropy || {};
        var signals = Array.isArray(worldModel.signals) ? worldModel.signals : [];
        var weights = arbitration.weights || {};
        var modifiers = Array.isArray(environment.modifiers) ? environment.modifiers : [];
        var metricBars = [
            renderMetricBar('承载力', weightedScores.baseline_strength || 0),
            renderMetricBar('时机窗', weightedScores.timing_window || 0),
            renderMetricBar('外部助力', weightedScores.external_support || 0),
            renderMetricBar('风险暴露', weightedScores.risk_exposure || 0)
        ].join('');

        mountEl.innerHTML = [
            renderDecisionCard(
                '决策类型',
                '类型：' + (decisionKernel.decision_type || 'balanced')
                + '\n行动等级：' + translateStringValue(recommendation.action_level || 'wait')
                + '\n决策期望值：' + formatOneDecimal(recommendation.decision_expectancy || 0)
                + '\n日志编号：' + (((payload || {}).decision_log || {}).log_id || '暂无')
            ),
            renderDecisionCard(
                '熵值',
                '熵值：' + formatOneDecimal(entropy.score || 0)
                + '\n等级：' + translateStringValue(entropy.label || 'unknown')
                + '\n说明：' + (entropy.reason || '暂无')
            ),
            renderDecisionCard(
                '统一信号',
                '内部阻力：' + formatOneDecimal(weightedScores.internal_resistance || 0)
                + '\n确定性：' + formatOneDecimal(weightedScores.certainty || 0)
                + '\n可执行性：' + formatOneDecimal(weightedScores.actionability || 0)
                + '\n方向分：' + formatOneDecimal(weightedScores.direction_score || 0),
                '<div class="metric-bars">' + metricBars + '</div>'
            ),
            renderDecisionCard(
                '风险对冲',
                Array.isArray(recommendation.risk_hedges) && recommendation.risk_hedges.length
                    ? recommendation.risk_hedges.join('\n')
                    : '暂无'
            ),
            renderDecisionCard(
                '模块权重',
                signals.length
                    ? ['当前有效先验：'].concat(signals.map(function (signal) {
                        return signal.module + ': ' + formatWeight(weights[signal.module] || 0);
                    })).join('\n')
                    : '暂无'
            ),
            renderDecisionCard(
                '环境修正',
                modifiers.length
                    ? modifiers.map(function (modifier) {
                        return modifier.name + ': ' + modifier.reason;
                    }).join('\n')
                    : '暂无环境修正项'
            ),
            renderDecisionCard(
                '冲突与一致',
                [
                    (Array.isArray(arbitration.consensus) && arbitration.consensus.length
                        ? ['一致项：'].concat(arbitration.consensus)
                        : ['一致项：暂无']).join('\n'),
                    '',
                    (Array.isArray(arbitration.conflicts) && arbitration.conflicts.length
                        ? ['冲突项：'].concat(arbitration.conflicts)
                        : ['冲突项：暂无']).join('\n')
                ].join('\n')
            )
        ].join('');
    }

    window.decisionPanel = {
        render: renderDecisionPanel,
        esc: esc
    };
})();
