(function () {
    // Unified consult entry: submit, fallback, assemble view-model, and hydrate page sections.
    var renderers = window.commonRenderers || {};
    var esc = renderers.esc || function (value) { return String(value ?? ''); };

    function renderMarkdown(text) {
        return window.renderMarkdownSimple(text, '#173a34');
    }

    function buildBriefAnswer(answer) {
        var text = String(answer || '').trim();
        if (!text) {
            return '已生成综合结论，请查看上方完整结果。';
        }

        var lines = text.split('\n').map(function (line) {
            return line.trim();
        }).filter(Boolean);

        for (var i = 0; i < lines.length; i += 1) {
            var normalized = lines[i].replace(/^[#*\-\d.\s]+/, '').trim();
            if (!normalized) {
                continue;
            }
            if (normalized.length <= 60) {
                return normalized;
            }
            return normalized.slice(0, 60).replace(/[，,;；:：\s]+$/, '') + '...';
        }

        return '已生成综合结论，请查看上方完整结果。';
    }

    function readOptionalInt(id) {
        var field = document.getElementById(id);
        var value = field ? field.value : '';
        return value === '' ? null : parseInt(value, 10);
    }

    function moduleNameLabel(moduleName) {
        var labels = {
            bazi: '八字底盘',
            ziwei: '紫微命盘',
            fengshui: '风水空间',
            liuyao: '六爻问事',
            meihua: '梅花起卦',
            qimen: '奇门时空',
            zeri: '择日择时'
        };
        return labels[moduleName] || moduleName;
    }

    function formatModuleSummary(moduleName, summary) {
        if (!summary) {
            return '暂无摘要';
        }
        if (moduleName === 'bazi') {
            return [
                summary.summary,
                summary.pattern_type ? '格局：' + summary.pattern_type : '',
                summary.strength_level ? '日主：' + summary.strength_level : '',
                (summary.strong_element || summary.weak_element) ? ('强弱：旺' + (summary.strong_element || '未知') + '，弱' + (summary.weak_element || '未知')) : '',
                summary.balance_advice ? '建议：' + summary.balance_advice : ''
            ].filter(Boolean).join('\n');
        }
        if (moduleName === 'liuyao') {
            return [
                '本卦：' + (summary.bengua || '未知'),
                summary.biangua ? '变卦：' + summary.biangua : '',
                Array.isArray(summary.dongyao) && summary.dongyao.length ? ('动爻：' + summary.dongyao.join('、')) : '动爻：无',
                summary.summary,
                summary.advice,
                summary.timing
            ].filter(Boolean).join('\n');
        }
        if (moduleName === 'ziwei') {
            return [
                summary.summary,
                summary.minggong ? '命宫：' + summary.minggong : '',
                summary.shengong ? '身宫：' + summary.shengong : '',
                summary.minggong_focus ? '命宫主轴：' + summary.minggong_focus : '',
                Array.isArray(summary.major_stars) && summary.major_stars.length ? ('主星：' + summary.major_stars.join('、')) : '',
                summary.career_vector ? '事业：' + summary.career_vector : '',
                summary.relationship_vector ? '关系：' + summary.relationship_vector : '',
                summary.wealth_vector ? '财务：' + summary.wealth_vector : '',
                summary.health_vector ? '健康：' + summary.health_vector : '',
                summary.mutagen_summary ? '四化：' + summary.mutagen_summary : '',
                summary.current_decadal && summary.current_decadal.palace ? ('当前大限：' + summary.current_decadal.palace + ' ' + ((summary.current_decadal.range || []).join('-'))) : '',
                summary.advice ? '建议：' + summary.advice : ''
            ].filter(Boolean).join('\n');
        }
        if (moduleName === 'fengshui') {
            return [
                summary.summary,
                summary.location ? '地点：' + summary.location : '',
                summary.scene_type ? '场景：' + summary.scene_type : '',
                summary.orientation ? '朝向：' + summary.orientation : '',
                summary.recommended_direction ? '宜：' + summary.recommended_direction : '',
                summary.avoid_direction ? '忌：' + summary.avoid_direction : '',
                typeof summary.space_support === 'number' ? '空间支持：' + summary.space_support + '分' : '',
                typeof summary.layout_risk === 'number' ? '布局风险：' + summary.layout_risk + '分' : '',
                summary.adjustment_advice ? '调整：' + summary.adjustment_advice : ''
            ].filter(Boolean).join('\n');
        }
        if (moduleName === 'meihua') {
            return [
                '起卦方式：' + (summary.method || 'time'),
                '本卦：' + (summary.bengua || '未知'),
                summary.hugua ? '互卦：' + summary.hugua : '',
                summary.biangua ? '变卦：' + summary.biangua : '',
                summary.moving_line ? ('动爻：第' + summary.moving_line + '爻') : '',
                summary.relation ? '体用：' + summary.relation : '',
                summary.summary,
                summary.advice,
                summary.timing
            ].filter(Boolean).join('\n');
        }
        if (moduleName === 'qimen') {
            return [
                '事项：' + (summary.matter_type || '通用'),
                summary.matter_fortune ? '局势：' + summary.matter_fortune : '',
                summary.best_direction ? ('方位：' + summary.best_direction + '（' + (summary.best_fortune || '未知') + '）') : '',
                summary.matter_advice
            ].filter(Boolean).join('\n');
        }
        if (moduleName === 'zeri') {
            var candidates = Array.isArray(summary.candidate_days) && summary.candidate_days.length
                ? '候选日：' + summary.candidate_days.map(function (item) {
                    return '' + item.date + (item.weekday || '');
                }).join('、')
                : '';
            return [
                '用途：' + (summary.purpose || '通用'),
                '' + (summary.date || '') + (summary.weekday ? ' ' + summary.weekday : ''),
                summary.level ? ('吉凶：' + summary.level + '（' + (summary.score || 0) + '分）') : '',
                summary.fortune_advice,
                candidates
            ].filter(Boolean).join('\n');
        }
        return JSON.stringify(summary, null, 2);
    }

    function buildConsultFallbackContext(payload) {
        var birthParts = [];
        if (payload.year !== null && payload.year !== undefined) birthParts.push('年：' + payload.year);
        if (payload.month !== null && payload.month !== undefined) birthParts.push('月：' + payload.month);
        if (payload.day !== null && payload.day !== undefined) birthParts.push('日：' + payload.day);
        if (payload.hour !== null && payload.hour !== undefined) birthParts.push('时：' + payload.hour);
        if (payload.minute !== null && payload.minute !== undefined) birthParts.push('分：' + payload.minute);
        if (payload.gender) birthParts.push('性别：' + payload.gender);

        return [
            '你是一个审慎的玄学辅助顾问。',
            '请只基于用户输入给出简洁、可执行的建议，避免绝对化表述。',
            '问题：' + payload.question,
            birthParts.length ? ('出生信息：' + birthParts.join('，')) : '出生信息：未提供',
            payload.matter_type ? ('事项类型：' + payload.matter_type) : '',
            payload.purpose ? ('用途：' + payload.purpose) : '',
            '输出格式：先给总判断，再给建议。'
        ].filter(Boolean).join('\n');
    }

    function buildFallbackConsultation(payload, answer) {
        var hasBirth = payload.year !== null && payload.year !== undefined
            && payload.month !== null && payload.month !== undefined
            && payload.day !== null && payload.day !== undefined
            && payload.hour !== null && payload.hour !== undefined
            && payload.gender;
        var briefAnswer = buildBriefAnswer(answer);

        return {
            question: payload.question,
            profile: {
                has_birth: hasBirth,
                gender: payload.gender || null,
                birth: hasBirth ? {
                    year: payload.year,
                    month: payload.month,
                    day: payload.day,
                    hour: payload.hour,
                    minute: payload.minute
                } : null,
                purpose: payload.purpose || '通用',
                matter_type: payload.matter_type || '通用',
                location: ''
            },
            intent: {
                modules: hasBirth ? ['bazi', 'liuyao', 'qimen'] : ['liuyao', 'qimen'],
                matter_type: payload.matter_type || '通用',
                purpose: payload.purpose || '通用'
            },
            modules: {},
            module_summaries: {},
            answer: answer,
            trace: {
                mermaid: [
                    'flowchart TD',
                    '  input["输入问题"] --> ai["AI 对话兼容模式"]',
                    '  ai --> answer["结果输出"]'
                ].join('\n'),
                steps: [
                    {
                        id: 'input',
                        label: '输入问题',
                        detail: payload.question,
                        inputs: {
                            question: payload.question,
                            birth: hasBirth ? {
                                year: payload.year,
                                month: payload.month,
                                day: payload.day,
                                hour: payload.hour,
                                minute: payload.minute
                            } : null
                        },
                        rule: '原始输入进入前端兼容流程',
                        outputs: { question: payload.question }
                    },
                    {
                        id: 'fallback',
                        label: '兼容模式',
                        detail: '当前后端尚未加载统一问事接口，使用 AI 对话完成分析。',
                        inputs: { ai_enabled: true },
                        rule: '调用旧版 AI 对话接口进行补位',
                        outputs: { answer: answer }
                    },
                    {
                        id: 'answer',
                        label: '结果输出',
                        detail: briefAnswer,
                        inputs: { summary: briefAnswer },
                        rule: '把兼容模式结果呈现给用户',
                        outputs: { summary: briefAnswer },
                        evidence: ['完整结论已在上方结果区展示']
                    }
                ]
            },
            ai: {
                enabled: true,
                synthesized: true,
                fallback: true
            }
        };
    }

    function buildSyntheticTrace(payload) {
        var modules = Array.isArray(payload && payload.intent && payload.intent.modules)
            ? payload.intent.modules
            : [];
        var summaries = payload.module_summaries || {};
        var answer = payload.answer || '';
        var briefAnswer = buildBriefAnswer(answer);
        var steps = [
            {
                id: 'input',
                label: '输入问题',
                detail: payload.question || '用户问题',
                inputs: {
                    question: payload.question || '',
                    birth: payload.profile && payload.profile.birth ? payload.profile.birth : null,
                    gender: payload.profile ? payload.profile.gender : null
                },
                rule: '原始输入进入统一引擎',
                outputs: { question: payload.question || '', profile: payload.profile || {} }
            },
            {
                id: 'intent',
                label: '意图识别',
                detail: [
                    payload.intent && payload.intent.matter_type ? '事项：' + payload.intent.matter_type : '',
                    payload.intent && payload.intent.purpose ? '用途：' + payload.intent.purpose : ''
                ].filter(Boolean).join('；') || '识别问题类型与用途',
                inputs: { question: payload.question || '', profile: payload.profile || {} },
                rule: '根据关键词和出生信息推断事项、用途与可用模块',
                outputs: {
                    matter_type: payload.intent && payload.intent.matter_type ? payload.intent.matter_type : '通用',
                    purpose: payload.intent && payload.intent.purpose ? payload.intent.purpose : '通用',
                    modules: modules
                }
            },
            {
                id: 'router',
                label: '模块编排',
                detail: modules.length ? modules.map(moduleNameLabel).join(' → ') : '按问题特征选择模块',
                inputs: {
                    matter_type: payload.intent && payload.intent.matter_type,
                    purpose: payload.intent && payload.intent.purpose
                },
                rule: '按问题类型路由到对应模块',
                outputs: { modules: modules },
                evidence: modules.map(function (moduleName) { return '命中模块：' + moduleNameLabel(moduleName); })
            }
        ];

        modules.forEach(function (moduleName) {
            var summary = summaries[moduleName] || {};
            steps.push({
                id: moduleName,
                label: moduleNameLabel(moduleName),
                detail: moduleNameLabel(moduleName) + ' 模块完成推演并生成摘要。',
                inputs: { summary: summary },
                rule: moduleNameLabel(moduleName) + ' 结果由对应模块解析后汇总',
                outputs: { summary: summary },
                evidence: Object.values(summary).filter(function (item) {
                    return typeof item === 'string' && item;
                })
            });
        });

        steps.push({
            id: 'synthesis',
            label: '统一综合',
            detail: payload.ai && payload.ai.synthesized ? 'AI 综合输出' : '规则化回退输出',
            inputs: { module_summaries: summaries, question: payload.question || '' },
            rule: '将模块摘要整合成最终建议',
            outputs: { answer: answer, ai: payload.ai || {} },
            evidence: ['模块摘要已汇总', '综合层完成']
        });

        steps.push({
            id: 'answer',
            label: '结果输出',
            detail: briefAnswer,
            inputs: { summary: briefAnswer },
            rule: '把最终答案返回给前端',
            outputs: { summary: briefAnswer },
            evidence: ['完整结论已在上方结果区展示']
        });

        return {
            steps: steps,
            mermaid: buildArchitectureMermaid(steps, modules, !!(payload.ai && payload.ai.enabled), !!(payload.ai && payload.ai.fallback))
        };
    }

    function buildArchitectureMermaid(steps, modules, aiEnabled, useFallback) {
        var labels = {};
        var ids = {};
        var defaultLabels = {
            input: '输入问题',
            intent: '意图识别',
            router: '模块编排',
            module_bus: '统一问事总线',
            bazi_year: '八字定年柱',
            bazi_month: '八字定月柱',
            bazi_day: '八字定日柱',
            bazi_hour: '八字定时柱',
            bazi_wuxing: '八字计五行',
            bazi_shishen: '八字判十神',
            bazi_dayun: '八字排大运',
            bazi_judge: '八字综合判读',
            ziwei_mingpan: '紫微排盘',
            ziwei_minggong: '紫微定命身宫',
            ziwei_sihua: '紫微排四化',
            ziwei_judge: '紫微综合判读',
            fengshui_orientation: '风水定朝向',
            fengshui_layout: '风水看布局',
            fengshui_judge: '风水综合判断',
            liuyao_cast: '六爻起卦',
            liuyao_judge: '六爻解读',
            meihua_cast: '梅花起卦',
            meihua_judge: '梅花判体用',
            qimen_dun: '奇门定阴阳遁与局数',
            qimen_chart: '奇门布九宫',
            qimen_judge: '奇门判断',
            zeri_jianxing: '择日定建星',
            zeri_shier: '择日定十二神',
            zeri_score: '择日综合评分',
            zeri_candidates: '候选日期',
            environment: '环境修正',
            world_model: '统一世界模型',
            arbitration: '仲裁引擎',
            synthesis: '统一综合',
            fallback: '兼容模式',
            answer: '结果输出'
        };
        (steps || []).forEach(function (step) {
            labels[step.id] = step.label;
            ids[step.id] = true;
        });

        function nodeLabel(id, fallback) {
            return esc(labels[id] || defaultLabels[id] || fallback);
        }

        function addNode(lines, id, fallback, indent) {
            lines.push(indent + id + '["' + nodeLabel(id, fallback) + '"]');
        }

        var moduleConfigs = {
            bazi: {
                title: '八字命理线',
                chain: ['bazi_year', 'bazi_month', 'bazi_day', 'bazi_hour', 'bazi_wuxing', 'bazi_shishen', 'bazi_dayun', 'bazi_judge']
            },
            ziwei: {
                title: '紫微斗数线',
                chain: ['ziwei_mingpan', 'ziwei_minggong', 'ziwei_sihua', 'ziwei_judge']
            },
            fengshui: {
                title: '风水空间线',
                chain: ['fengshui_orientation', 'fengshui_layout', 'fengshui_judge']
            },
            liuyao: {
                title: '六爻占断线',
                chain: ['liuyao_cast', 'liuyao_judge']
            },
            meihua: {
                title: '梅花易数线',
                chain: ['meihua_cast', 'meihua_judge']
            },
            qimen: {
                title: '奇门遁甲线',
                chain: ['qimen_dun', 'qimen_chart', 'qimen_judge']
            },
            zeri: {
                title: '择日择时线',
                chain: ['zeri_jianxing', 'zeri_shier', 'zeri_score', 'zeri_candidates']
            }
        };

        var mermaidLines = [
            'flowchart TD',
            '  subgraph control["统一问事总控层"]',
            '    direction TB',
            '    input["' + nodeLabel('input', '输入问题') + '"]',
            '    intent["' + nodeLabel('intent', '意图识别') + '"]',
            '    router["' + nodeLabel('router', '模块编排') + '"]',
            '    module_bus["统一问事总线"]',
            '    input --> intent --> router --> module_bus',
            '  end',
            '  subgraph module_layer["术数模块执行层"]',
            '    direction LR'
        ];

        Object.keys(moduleConfigs).forEach(function (moduleName) {
            var config = moduleConfigs[moduleName];
            mermaidLines.push('    subgraph ' + moduleName + '_lane["' + esc(config.title) + '"]');
            mermaidLines.push('      direction TB');
            config.chain.forEach(function (id) {
                addNode(mermaidLines, id, id, '      ');
            });
            for (var i = 0; i < config.chain.length - 1; i += 1) {
                mermaidLines.push('      ' + config.chain[i] + ' --> ' + config.chain[i + 1]);
            }
            mermaidLines.push('    end');
        });
        mermaidLines.push('  end');
        Object.keys(moduleConfigs).forEach(function (moduleName) {
            mermaidLines.push('  module_bus --> ' + moduleConfigs[moduleName].chain[0]);
        });

        mermaidLines.push('  subgraph decision["统一决策集成层"]');
        mermaidLines.push('    direction TB');
        addNode(mermaidLines, 'environment', '环境修正', '    ');
        addNode(mermaidLines, 'world_model', '统一世界模型', '    ');
        addNode(mermaidLines, 'arbitration', '仲裁引擎', '    ');
        addNode(mermaidLines, 'synthesis', '统一综合', '    ');
        addNode(mermaidLines, 'fallback', '兼容模式', '    ');
        addNode(mermaidLines, 'answer', '结果输出', '    ');
        mermaidLines.push('  end');

        mermaidLines.push('  intent --> environment');
        Object.keys(moduleConfigs).forEach(function (moduleName) {
            var sink = moduleConfigs[moduleName].chain[moduleConfigs[moduleName].chain.length - 1];
            mermaidLines.push('  ' + sink + ' --> world_model');
        });
        mermaidLines.push('  environment --> world_model --> arbitration --> synthesis');
        mermaidLines.push('  synthesis --> fallback --> answer');

        var activeNodes = {};
        Object.keys(ids).forEach(function (id) {
            activeNodes[id] = true;
        });
        activeNodes.module_bus = true;
        if (!ids.fallback) {
            delete activeNodes.fallback;
        }

        var allNodes = [
            'input', 'intent', 'router', 'module_bus',
            'bazi_year', 'bazi_month', 'bazi_day', 'bazi_hour', 'bazi_wuxing', 'bazi_shishen', 'bazi_dayun', 'bazi_judge',
            'ziwei_mingpan', 'ziwei_minggong', 'ziwei_sihua', 'ziwei_judge',
            'fengshui_orientation', 'fengshui_layout', 'fengshui_judge',
            'liuyao_cast', 'liuyao_judge',
            'meihua_cast', 'meihua_judge',
            'qimen_dun', 'qimen_chart', 'qimen_judge',
            'zeri_jianxing', 'zeri_shier', 'zeri_score', 'zeri_candidates',
            'environment', 'world_model', 'arbitration', 'synthesis', 'fallback', 'answer'
        ];
        var inactiveNodes = allNodes.filter(function (id) { return !activeNodes[id]; });

        mermaidLines.push('  classDef inactive fill:#eef1ef,stroke:#c9d2cd,color:#8a968f,stroke-width:1px;');
        mermaidLines.push('  classDef active fill:#f7efe1,stroke:#2c5b4f,color:#173a34,stroke-width:2px;');
        if (inactiveNodes.length) {
            mermaidLines.push('  class ' + inactiveNodes.join(',') + ' inactive;');
        }
        mermaidLines.push('  class ' + Object.keys(activeNodes).sort().join(',') + ' active;');

        return mermaidLines.join('\n');
    }

    function buildTraceSummary(trace) {
        var steps = Array.isArray(trace && trace.steps) ? trace.steps : [];
        if (!steps.length) {
            return '<span class="trace-summary-chip"><strong>0</strong>暂无流程</span>';
        }

        var chips = steps.slice(0, 5).map(function (step, index) {
            return [
                '<span class="trace-summary-chip">',
                '  <strong>' + String(index + 1).padStart(2, '0') + '</strong>',
                '  <span>' + esc(step.label || step.id || '步骤') + '</span>',
                '</span>'
            ].join('');
        });

        if (steps.length > 5) {
            chips.push([
                '<span class="trace-summary-chip">',
                '  <strong>+' + (steps.length - 5) + '</strong>',
                '  <span>后续</span>',
                '</span>'
            ].join(''));
        }

        return chips.join('');
    }

    async function requestConsultation(payload) {
        try {
            return await window.apiClient.postJson('/api/system/consult', payload);
        } catch (error) {
            if (error && (error.status === 404 || error.message === 'Not Found')) {
                var context = buildConsultFallbackContext(payload);
                var legacyResponse = await window.apiClient.postJson('/api/ai/chat', {
                    question: payload.question,
                    context: context
                });
                return {
                    data: buildFallbackConsultation(payload, legacyResponse.data && legacyResponse.data.answer ? legacyResponse.data.answer : '系统暂未生成结论。')
                };
            }
            throw error;
        }
    }

    function renderConsultation(data, elements) {
        var payload = data || {};
        var summaries = payload.module_summaries || {};
        var intent = payload.intent || {};
        var trace = payload.trace && payload.trace.mermaid ? payload.trace : buildSyntheticTrace(payload);

        elements.consultAnswer.innerHTML = renderMarkdown(payload.answer || '系统暂未生成结论。');
        elements.consultMeta.innerHTML = []
            .concat((intent.modules || []).map(function (moduleName) {
                return '<span class="result-chip">' + esc(moduleNameLabel(moduleName)) + '</span>';
            }))
            .concat(intent.matter_type ? ['<span class="result-chip">事项：' + esc(intent.matter_type) + '</span>'] : [])
            .concat(intent.purpose ? ['<span class="result-chip">用途：' + esc(intent.purpose) + '</span>'] : [])
            .concat(payload.ai && payload.ai.fallback ? ['<span class="result-chip">兼容模式</span>'] : [])
            .concat([payload.ai && payload.ai.synthesized ? '<span class="result-chip">AI 已综合</span>' : '<span class="result-chip">基础综合</span>'])
            .filter(Boolean)
            .join('');
        if (elements.consultTraceSummary) {
            elements.consultTraceSummary.innerHTML = buildTraceSummary(trace);
        }

        var summaryKeys = Object.keys(summaries);
        elements.consultModuleGrid.innerHTML = summaryKeys.length
            ? summaryKeys.map(function (moduleName) {
                return [
                    '<div class="module-summary-card">',
                    '  <div class="title">' + esc(moduleNameLabel(moduleName)) + '</div>',
                    '  <div class="body">' + esc(formatModuleSummary(moduleName, summaries[moduleName])) + '</div>',
                    '</div>'
                ].join('');
            }).join('')
            : [
                '<div class="module-summary-card">',
                '  <div class="title">兼容模式</div>',
                '  <div class="body">' + esc(payload.ai && payload.ai.fallback ? '当前后端尚未加载统一问事接口，已自动切换到 AI 对话兼容模式。' : '暂无模块摘要。') + '</div>',
                '</div>'
            ].join('');

        if (window.decisionPanel) {
            window.decisionPanel.render(payload, elements.consultDecisionGrid);
        }
        if (window.tracePanel) {
            window.tracePanel.renderDiagram(trace, elements.consultTraceDiagram);
            window.tracePanel.renderSteps(trace, elements.consultTraceSteps);
        }
        elements.consultResult.classList.add('show');
        elements.consultResult.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function initializeConsultPanel() {
        var consultForm = document.getElementById('consultForm');
        if (!consultForm) {
            return;
        }

        var elements = {
            consultLoading: document.getElementById('consultLoading'),
            consultResult: document.getElementById('consultResult'),
            consultAnswer: document.getElementById('consultAnswer'),
            consultMeta: document.getElementById('consultMeta'),
            consultDecisionGrid: document.getElementById('consultDecisionGrid'),
            consultModuleGrid: document.getElementById('consultModuleGrid'),
            consultTraceDiagram: document.getElementById('consultTraceDiagram'),
            consultTraceSteps: document.getElementById('consultTraceSteps'),
            consultTraceSummary: document.getElementById('consultTraceSummary')
        };

        consultForm.addEventListener('submit', async function (event) {
            event.preventDefault();
            var question = document.getElementById('consultQuestion').value.trim();
            if (!question) {
                showToast('请先输入你想问的事情。', 'warn');
                return;
            }

            var payload = {
                question: question,
                year: readOptionalInt('consultYear'),
                month: readOptionalInt('consultMonth'),
                day: readOptionalInt('consultDay'),
                hour: readOptionalInt('consultHour'),
                minute: readOptionalInt('consultMinute'),
                gender: document.getElementById('consultGender').value || null
            };

            elements.consultLoading.classList.add('show');
            elements.consultResult.classList.remove('show');

            try {
                var response = await requestConsultation(payload);
                renderConsultation(response.data, elements);
            } catch (error) {
                showToast('系统分析失败：' + error.message, 'error');
            } finally {
                elements.consultLoading.classList.remove('show');
            }
        });

        document.getElementById('fillDemoBtn').addEventListener('click', function () {
            document.getElementById('consultQuestion').value = '我现在适合换工作吗？应该怎么做更稳？';
            document.getElementById('consultYear').value = '1990';
            document.getElementById('consultMonth').value = '1';
            document.getElementById('consultDay').value = '1';
            document.getElementById('consultHour').value = '12';
            document.getElementById('consultMinute').value = '0';
            document.getElementById('consultGender').value = '男';
        });

        document.getElementById('clearConsultBtn').addEventListener('click', function () {
            consultForm.reset();
            elements.consultResult.classList.remove('show');
        });
    }

    window.consultPanel = {
        initialize: initializeConsultPanel,
        buildSyntheticTrace: buildSyntheticTrace,
        moduleNameLabel: moduleNameLabel
    };
})();
