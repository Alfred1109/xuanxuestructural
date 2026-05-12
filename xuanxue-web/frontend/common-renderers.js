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
        var contentClass = className === 'formula' ? 'trace-field-content formula-block' : 'trace-field-content';
        return [
            '<div class="trace-field">',
            '  <div class="field-title' + (className ? ' ' + className : '') + '">' + esc(title) + '</div>',
            '  <div class="' + contentClass + '">' + esc(value) + '</div>',
            '</div>'
        ].join('');
    }

    function formatTraceValue(value, label) {
        if (value === null || value === undefined || value === '') {
            return '';
        }

        if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
            return label ? (label + '：' + String(value)) : String(value);
        }

        if (Array.isArray(value)) {
            var items = value
                .map(function (item) { return formatTraceValue(item, ''); })
                .filter(Boolean);
            if (!items.length) {
                return '';
            }
            return label ? (label + '：' + items.join('；')) : items.join('；');
        }

        if (typeof value === 'object') {
            if (looksLikeBirth(value)) {
                return (label ? label + '：' : '') + formatBirth(value);
            }

            var lines = [];
            Object.keys(value).forEach(function (key) {
                var line = formatTraceValue(value[key], humanizeKey(key));
                if (line) {
                    lines.push(line);
                }
            });
            if (!lines.length) {
                return '';
            }
            return label ? (label + '：\n' + lines.join('\n')) : lines.join('\n');
        }

        return label ? (label + '：' + String(value)) : String(value);
    }

    function renderTraceText(value) {
        return formatTraceValue(value, '');
    }

    function humanizeKey(key) {
        var labels = {
            question: '问题',
            profile: '用户画像',
            birth: '出生信息',
            gender: '性别',
            location: '地点',
            matter_type: '事项类型',
            purpose: '用途',
            modules: '命中模块',
            summary: '摘要',
            answer: '结果',
            ai_enabled: 'AI 开关',
            ai: 'AI 状态',
            question_text: '问题',
            day_master: '日主',
            tiangan: '天干',
            pillars: '四柱',
            year_pillar: '年柱',
            month_pillar: '月柱',
            day_pillar: '日柱',
            hour_pillar: '时柱',
            wuxing_count: '五行统计',
            shishen: '十神',
            dayun: '大运',
            strong_element: '偏旺五行',
            weak_element: '偏弱五行',
            balance_advice: '平衡建议',
            pattern_type: '格局',
            strength_level: '强弱',
            bengua: '本卦',
            hugua: '互卦',
            biangua: '变卦',
            dongyao: '动爻',
            moving_line: '动爻',
            method: '起卦方式',
            tiyong: '体用',
            relation: '关系',
            chart: '九宫盘',
            best_direction: '最佳方位',
            best_fortune: '方位吉凶',
            matter_fortune: '事项吉凶',
            matter_advice: '事项建议',
            jianxing: '建星',
            shier_shen: '十二神',
            huangdao_type: '黄黑道',
            level: '等级',
            score: '评分',
            suitable: '宜',
            avoid: '忌',
            candidate_days: '候选日期',
            module_summaries: '模块摘要',
            modifiers: '修正项',
            signals: '决策信号',
            decision_kernel: '决策内核',
            effective_weights: '有效权重',
            arbitration: '仲裁结果',
            world_model: '世界模型',
            environment: '环境修正',
            recommendation: '行动建议',
            entropy: '熵值',
            weights: '权重',
            decision_type: '决策类型'
        };
        return labels[key] || String(key).replace(/_/g, ' ');
    }

    function looksLikeBirth(value) {
        return value && typeof value === 'object'
            && ('year' in value || 'month' in value || 'day' in value || 'hour' in value || 'minute' in value);
    }

    function formatBirth(value) {
        return [
            value.year ? value.year + '年' : '',
            value.month ? value.month + '月' : '',
            value.day ? value.day + '日' : '',
            value.hour !== undefined && value.hour !== null ? value.hour + '时' : '',
            value.minute !== undefined && value.minute !== null ? value.minute + '分' : ''
        ].filter(Boolean).join(' ');
    }

    window.commonRenderers = {
        esc: esc,
        prettyJson: prettyJson,
        renderTraceText: renderTraceText,
        renderDecisionCard: renderDecisionCard,
        renderMetricBar: renderMetricBar,
        renderTraceFieldBlock: renderTraceFieldBlock
    };
})();
