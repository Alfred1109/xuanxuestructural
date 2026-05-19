(function () {
    function esc(value) {
        return window.escapeHtml ? window.escapeHtml(value ?? '') : String(value ?? '');
    }

    function prettyJson(value) {
        return esc(JSON.stringify(value ?? {}, null, 2));
    }

    function isNumericLike(value) {
        return typeof value === 'number'
            || (typeof value === 'string' && value.trim() !== '' && !Number.isNaN(Number(value)));
    }

    function formatOneDecimal(value) {
        var numeric = Number(value);
        if (!Number.isFinite(numeric)) {
            return String(value ?? '');
        }
        return numeric.toFixed(1);
    }

    function translateToken(token) {
        var labels = {
            wood: '木',
            fire: '火',
            earth: '土',
            metal: '金',
            water: '水',
            yang: '阳',
            yin: '阴',
            same: '同',
            different: '异',
            high: '高',
            medium: '中',
            low: '低',
            unknown: '未知',
            balanced: '平衡型',
            strategic: '战略型',
            tactical: '战术型',
            timing: '择时型',
            wait: '等待',
            go: '行动',
            cautious: '谨慎推进',
            hold: '暂缓',
            space: '空间',
            palm: '手相',
            face: '面相',
            bundle: '多图组合',
            micro: '微观参考',
            support: '支持度',
            risk: '风险',
            actionability: '可执行性',
            certainty_hint: '确定性提示',
            clarity: '清晰度',
            confidence: '可信度',
            jia: '甲',
            yi: '乙',
            bing: '丙',
            ding: '丁',
            wu: '戊',
            ji: '己',
            geng: '庚',
            xin: '辛',
            ren: '壬',
            gui: '癸',
            zi: '子',
            chou: '丑',
            yin: '寅',
            mao: '卯',
            chen: '辰',
            si: '巳',
            wu_zhi: '午',
            wei: '未',
            shen: '申',
            you: '酉',
            xu: '戌',
            hai: '亥',
            qian: '乾',
            dui: '兑',
            li: '离',
            zhen: '震',
            xun: '巽',
            kan: '坎',
            gen: '艮',
            kun: '坤'
        };
        return labels[token] || token;
    }

    function translateStringValue(value) {
        if (typeof value !== 'string') {
            return value;
        }

        var exactLabels = {
            unknown: '未知',
            high: '高',
            medium: '中',
            low: '低',
            none: '无',
            light: '轻度',
            heavy: '重度',
            balanced: '平衡型',
            strategic: '战略型',
            tactical: '战术型',
            timing: '择时型',
            temporal: '时序型',
            baseline: '基础层',
            window: '窗口层',
            probe: '试探推进',
            wait: '等待',
            go: '行动',
            cautious: '谨慎推进',
            hold: '暂缓',
            space: '空间',
            palm: '手相',
            face: '面相',
            bundle: '多图组合',
            home: '住宅',
            office: '办公室',
            generic: '通用',
            supported: '有靠',
            neutral: '中性',
            exposed: '暴露',
            wood: '木',
            fire: '火',
            earth: '土',
            metal: '金',
            water: '水',
            yang: '阳',
            yin: '阴',
            bazi: '八字',
            ziwei: '紫微斗数',
            qimen: '奇门遁甲',
            liuyao: '六爻',
            meihua: '梅花易数',
            zeri: '择日',
            fengshui: '风水',
            location_context: '地点上下文',
            purpose_specificity: '用途明确度'
        };
        if (exactLabels[value]) {
            return exactLabels[value];
        }

        var normalized = value.trim().toLowerCase();
        if (exactLabels[normalized]) {
            return exactLabels[normalized];
        }

        var ganzhiPinyin = {
            jia: '甲', yi: '乙', bing: '丙', ding: '丁', wu: '戊', ji: '己', geng: '庚', xin: '辛', ren: '壬', gui: '癸',
            zi: '子', chou: '丑', yin: '寅', mao: '卯', chen: '辰', si: '巳', wei: '未', shen: '申', you: '酉', xu: '戌', hai: '亥'
        };
        if (ganzhiPinyin[normalized]) {
            return ganzhiPinyin[normalized];
        }
        if (normalized === 'wu') {
            return value === 'wu' ? '戊' : value;
        }

        return value
            .replace(/month index/gi, '月序')
            .replace(/month gan index/gi, '月干索引')
            .replace(/month zhi index/gi, '月支索引')
            .replace(/hour zhi index/gi, '时支索引')
            .replace(/hour gan index/gi, '时干索引')
            .replace(/hour gan base/gi, '起始时干索引')
            .replace(/day gan index/gi, '日干索引')
            .replace(/gan index/gi, '天干索引')
            .replace(/zhi index/gi, '地支索引')
            .replace(/year pillar/gi, '年柱')
            .replace(/month pillar/gi, '月柱')
            .replace(/day pillar/gi, '日柱')
            .replace(/hour pillar/gi, '时柱')
            .replace(/birth time/gi, '出生时间')
            .replace(/base date/gi, '基准日期')
            .replace(/days diff/gi, '相差天数')
            .replace(/year for ganzhi/gi, '用于取干支的年份')
            .replace(/day master/gi, '日主')
            .replace(/year yinyang/gi, '年干阴阳')
            .replace(/age range/gi, '年龄区间')
            .replace(/prev jie/gi, '前一节气')
            .replace(/next jie/gi, '后一节气')
            .replace(/delta days/gi, '相差天数')
            .replace(/start age formula/gi, '起运公式')
            .replace(/wuxing count/gi, '五行统计')
            .replace(/boundaries/gi, '节气边界')
            .replace(/comparison/gi, '比较')
            .replace(/symbol/gi, '符号')
            .replace(/weight/gi, '权重')
            .replace(/module/gi, '模块')
            .replace(/layer/gi, '层级')
            .replace(/raw/gi, '原始数据')
            .replace(/reason/gi, '原因')
            .replace(/effect/gi, '影响')
            .replace(/name/gi, '名称')
            .replace(/log id/gi, '日志编号')
            .replace(/aggregate effect/gi, '汇总影响')
            .replace(/weighted scores/gi, '加权得分')
            .replace(/baseline strength/gi, '承载力')
            .replace(/timing window/gi, '时机窗')
            .replace(/external support/gi, '外部助力')
            .replace(/internal resistance/gi, '内部阻力')
            .replace(/risk exposure/gi, '风险暴露')
            .replace(/direction score/gi, '方向分')
            .replace(/decision expectancy/gi, '决策期望值')
            .replace(/action level/gi, '行动等级')
            .replace(/risk hedges/gi, '风险对冲')
            .replace(/\bbirth_time\b/gi, '出生时间')
            .replace(/\bbase_date\b/gi, '基准日期')
            .replace(/\bdays_diff\b/gi, '相差天数')
            .replace(/\byear_for_ganzhi\b/gi, '用于取干支的年份')
            .replace(/\bmonth_index\b/gi, '月序')
            .replace(/\bmonth_gan_index\b/gi, '月干索引')
            .replace(/\bmonth_zhi_index\b/gi, '月支索引')
            .replace(/\bhour_zhi_index\b/gi, '时支索引')
            .replace(/\bhour_gan_index\b/gi, '时干索引')
            .replace(/\bhour_gan_base\b/gi, '起始时干索引')
            .replace(/\bday_gan_index\b/gi, '日干索引')
            .replace(/\bgan_index\b/gi, '天干索引')
            .replace(/\bzhi_index\b/gi, '地支索引')
            .replace(/\byear_gan\b/gi, '年干')
            .replace(/\bday_gan\b/gi, '日干')
            .replace(/\bboundaries\b/gi, '节气边界')
            .replace(/\bterm\b/gi, '节气')
            .replace(/\bdate\b/gi, '日期')
            .replace(/\bcomparison\b/gi, '比较')
            .replace(/\bresult\b/gi, '结果')
            .replace(/\bsource\b/gi, '来源')
            .replace(/\binput\b/gi, '输入')
            .replace(/\bfinal\b/gi, '最终结果')
            .replace(/\bquality\b/gi, '质量评估')
            .replace(/\bkind\b/gi, '类型')
            .replace(/\bsteps\b/gi, '步骤')
            .replace(/\bage_range\b/gi, '年龄区间')
            .replace(/\bprev_jie\b/gi, '前一节气')
            .replace(/\bnext_jie\b/gi, '后一节气')
            .replace(/\bdelta_days\b/gi, '相差天数')
            .replace(/\bstart_age_formula\b/gi, '起运公式')
            .replace(/\bmonth_pillar\b/gi, '月柱')
            .replace(/\byear_pillar\b/gi, '年柱')
            .replace(/\bday_pillar\b/gi, '日柱')
            .replace(/\bhour_pillar\b/gi, '时柱')
            .replace(/\bwuxing_count\b/gi, '五行统计')
            .replace(/\bday_master\b/gi, '日主')
            .replace(/\byear_yinyang\b/gi, '年干阴阳')
            .replace(/\bdirection\b/gi, '方向')
            .replace(/\blog_id\b/gi, '日志编号')
            .replace(/\baggregate_effect\b/gi, '汇总影响')
            .replace(/\bweighted_scores\b/gi, '加权得分')
            .replace(/\bbaseline_strength\b/gi, '承载力')
            .replace(/\btiming_window\b/gi, '时机窗')
            .replace(/\bexternal_support\b/gi, '外部助力')
            .replace(/\binternal_resistance\b/gi, '内部阻力')
            .replace(/\brisk_exposure\b/gi, '风险暴露')
            .replace(/\bdirection_score\b/gi, '方向分')
            .replace(/\bdecision_expectancy\b/gi, '决策期望值')
            .replace(/\baction_level\b/gi, '行动等级')
            .replace(/\brisk_hedges\b/gi, '风险对冲')
            .replace(/\blocation_context\b/gi, '地点上下文')
            .replace(/\bpurpose_specificity\b/gi, '用途明确度')
            .replace(/\b(jia|yi|bing|ding|wu|ji|geng|xin|ren|gui)\b/gi, function (match) {
                return ganzhiPinyin[match.toLowerCase()] || match;
            })
            .replace(/\b(zi|chou|yin|mao|chen|si|wei|shen|you|xu|hai)\b/gi, function (match) {
                return ganzhiPinyin[match.toLowerCase()] || match;
            })
            .replace(/\b(qian|dui|li|zhen|xun|kan|gen|kun)\b/gi, function (match) {
                return translateToken(match.toLowerCase());
            })
            .replace(/\b(wood|fire|earth|metal|water|yang|yin|high|medium|low|unknown|space|palm|face|bundle|none|light|heavy|home|office|generic|supported|neutral|exposed)\b/gi, function (match) {
                return translateToken(match.toLowerCase());
            })
            .replace(/\b(bazi|ziwei|qimen|liuyao|meihua|zeri|fengshui|strategic|tactical|timing|temporal|baseline|window|wait|go|cautious|hold|probe|location_context|purpose_specificity)\b/gi, function (match) {
                return translateToken(match.toLowerCase());
            });
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

    function renderInfoCard(className, title, value, meta) {
        var cardClass = className || 'info-card';
        return [
            '<div class="' + esc(cardClass) + '">',
            '  <div class="kicker">' + esc(meta || '') + '</div>',
            '  <div class="title">' + esc(title || '未命名') + '</div>',
            '  <div class="meta">' + esc(value || '') + '</div>',
            '</div>'
        ].join('');
    }

    function renderTraceItem(title, body) {
        return [
            '<div class="trace-item">',
            '  <h4>' + esc(title || '未命名') + '</h4>',
            '  <div class="trace-body">' + esc(body || '') + '</div>',
            '</div>'
        ].join('');
    }

    function renderTraceItems(items) {
        return (Array.isArray(items) ? items : [])
            .map(function (item) {
                return renderTraceItem(item && item.title, item && item.body);
            })
            .join('');
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

        if (typeof value === 'number') {
            var numericValue = formatOneDecimal(value);
            return label ? (label + '：' + numericValue) : numericValue;
        }

        if (typeof value === 'string') {
            var translated = translateStringValue(value);
            return label ? (label + '：' + translated) : translated;
        }

        if (typeof value === 'boolean') {
            return label ? (label + '：' + (value ? '是' : '否')) : (value ? '是' : '否');
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

    function normalizeKeyName(key) {
        return String(key ?? '')
            .replace(/([a-z0-9])([A-Z])/g, '$1_$2')
            .replace(/[\s.\-\/]+/g, '_')
            .replace(/_+/g, '_')
            .replace(/^_+|_+$/g, '')
            .toLowerCase();
    }

    function prettifyFallbackKey(key) {
        var normalized = normalizeKeyName(key);
        if (!normalized) {
            return '';
        }

        var translated = translateStringValue(normalized);
        if (translated !== normalized) {
            return translated.replace(/_/g, ' ');
        }

        return String(key ?? '')
            .replace(/([a-z0-9])([A-Z])/g, '$1 $2')
            .replace(/[_./-]+/g, ' ')
            .replace(/\s+/g, ' ')
            .trim();
    }

    function humanizeKey(key) {
        var labels = {
            question: '问题',
            profile: '用户画像',
            birth: '出生信息',
            gender: '性别',
            location: '地点',
            visual_context: '视觉上下文',
            matter_type: '事项类型',
            purpose: '用途',
            modules: '命中模块',
            summary: '摘要',
            answer: '结果',
            ai_enabled: 'AI 开关',
            ai: 'AI 状态',
            aggregate: '汇总',
            rationale: '依据',
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
            weekday: '星期',
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
            decision_type: '决策类型',
            module: '模块',
            layer: '层级',
            raw: '原始数据',
            reason: '原因',
            effect: '影响',
            name: '名称',
            symbol: '符号',
            weight: '权重',
            log_id: '日志编号',
            gan: '天干',
            zhi: '地支',
            wuxing: '五行',
            yinyang: '阴阳',
            items: '明细',
            totals: '汇总',
            contributions: '贡献项',
            source: '来源',
            aggregate_effect: '汇总影响',
            weighted_scores: '加权得分',
            result: '结果',
            input: '输入',
            final: '最终结果',
            quality: '质量评估',
            kind: '类型',
            base: '基础值',
            adjustments: '调整项',
            support: '支持度',
            risk: '风险',
            actionability: '可执行性',
            certainty_hint: '确定性提示',
            confidence: '可信度',
            clarity: '清晰度',
            baseline_strength: '承载力',
            timing_window: '时机窗',
            external_support: '外部助力',
            internal_resistance: '内部阻力',
            risk_exposure: '风险暴露',
            direction_score: '方向分',
            decision_expectancy: '决策期望值',
            action_level: '行动等级',
            risk_hedges: '风险对冲',
            earthly_branch: '地支',
            five_elements_class: '五行局',
            solar_input: '阳历输入',
            lunar_output: '农历结果',
            chinese_date: '中文日期',
            solar_date: '阳历日期',
            lunar_date: '农历日期',
            time_range: '时辰范围',
            current_decadal: '当前大限',
            fortune_cycle: '运程周期',
            ranges: '区间',
            fortune_advice: '运势建议',
            image_quality: '图像质量',
            lighting: '光照',
            occlusion: '遮挡',
            seat_backing: '靠山',
            face_shape: '脸型',
            sign: '星座',
            zodiac: '生肖'
        };
        var rawKey = String(key ?? '');
        var normalizedKey = normalizeKeyName(rawKey);
        return labels[rawKey] || labels[normalizedKey] || prettifyFallbackKey(rawKey);
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
        renderInfoCard: renderInfoCard,
        renderMetricBar: renderMetricBar,
        renderTraceItem: renderTraceItem,
        renderTraceItems: renderTraceItems,
        renderTraceFieldBlock: renderTraceFieldBlock,
        formatOneDecimal: formatOneDecimal,
        translateStringValue: translateStringValue,
        humanizeKey: humanizeKey,
        isNumericLike: isNumericLike
    };
})();
