(function () {
    // Unified consult entry: submit, fallback, assemble view-model, and hydrate page sections.
    var renderers = window.commonRenderers || {};
    var esc = renderers.esc || function (value) { return String(value ?? ''); };

    function renderMarkdown(text) {
        return window.renderMarkdownSimple(text, '#173a34');
    }

    function readOptionalInt(id) {
        var field = document.getElementById(id);
        var value = field ? field.value : '';
        return value === '' ? null : parseInt(value, 10);
    }

    function moduleNameLabel(moduleName) {
        var labels = {
            bazi: '八字底盘',
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
                        detail: answer,
                        inputs: { answer: answer },
                        rule: '把兼容模式结果呈现给用户',
                        outputs: { answer: answer },
                        evidence: ['兼容模式回退输出']
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
            detail: answer,
            inputs: { answer: answer },
            rule: '把最终答案返回给前端',
            outputs: { answer: answer },
            evidence: ['结果可回看']
        });

        var mermaidLines = [
            'flowchart TD',
            '  input["输入问题"] --> intent["意图识别"]',
            '  intent --> router["模块编排"]'
        ];
        modules.forEach(function (moduleName) {
            mermaidLines.push('  router --> ' + moduleName + '["' + esc(moduleNameLabel(moduleName)) + '"]');
            mermaidLines.push('  ' + moduleName + ' --> synthesis["统一综合"]');
        });
        if (!modules.length) {
            mermaidLines.push('  router --> synthesis["统一综合"]');
        }
        mermaidLines.push('  synthesis --> answer["结果输出"]');

        return {
            steps: steps,
            mermaid: mermaidLines.join('\n')
        };
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
