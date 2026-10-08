(function () {
    // Unified consult submission and shared result rendering.
    var renderers = window.commonRenderers || {};
    var esc = renderers.esc || function (value) { return String(value ?? ''); };
    var VISUAL_CONTEXT_STORAGE_KEY = 'xuanxue_visual_context';
    var CONSULT_RESULT_STORAGE_KEY = 'xuanxue_latest_consult_result';
    var CONSULT_RESULT_TIMESTAMP_KEY = 'xuanxue_latest_consult_result_at';
    var CONSULT_RESULT_URL = 'consult-result.html';
    var presetModalLastFocus = null;

    function renderMarkdown(text) {
        return window.renderMarkdownSimple(text, '#173a34');
    }

    function buildConsultResultUrl(data) {
        try {
            return window.consultSession.url(CONSULT_RESULT_URL, { id: window.consultSession.resultId(data) });
        } catch (_error) {
            return CONSULT_RESULT_URL;
        }
    }

    function saveLatestConsultation(data, owner) {
        try {
            window.sessionStorage.setItem(CONSULT_RESULT_STORAGE_KEY + ':' + (owner || window.consultSession.owner()), JSON.stringify(data || {}));
            window.sessionStorage.setItem(CONSULT_RESULT_TIMESTAMP_KEY + ':' + (owner || window.consultSession.owner()), new Date().toISOString());
        } catch (_error) {
            // Ignore storage failures and let the result page handle the empty state.
        }
    }

    function readLatestConsultation() {
        try {
            var raw = window.sessionStorage.getItem(CONSULT_RESULT_STORAGE_KEY + ':' + window.consultSession.owner());
            return raw ? JSON.parse(raw) : null;
        } catch (_error) {
            return null;
        }
    }

    function readLatestConsultationTimestamp() {
        try {
            return window.sessionStorage.getItem(CONSULT_RESULT_TIMESTAMP_KEY + ':' + window.consultSession.owner()) || '';
        } catch (_error) {
            return '';
        }
    }

    function readVisualContext() {
        if (window.visualContextStore && window.visualContextStore.readManifest) {
            return window.visualContextStore.readManifest();
        }
        try {
            var raw = window.localStorage.getItem(VISUAL_CONTEXT_STORAGE_KEY);
            if (!raw) {
                return null;
            }
            return JSON.parse(raw);
        } catch (_error) {
            return null;
        }
    }

    async function resolveVisualContextForConsult(signal, onProgress) {
        var manifest = readVisualContext();
        if (!manifest) {
            return null;
        }
        if (manifest.kind !== 'draft') {
            return manifest;
        }
        if (!window.visualContextStore || !window.visualContextStore.loadDraft) {
            throw new Error('本地拍照条件草稿不可用，请重新上传图片后再试');
        }

        var cacheKey = 'xuanxue_visual_resolved:' + window.consultSession.owner();
        var signature = JSON.stringify(manifest);
        try {
            var cached = JSON.parse(window.sessionStorage.getItem(cacheKey) || 'null');
            if (cached && cached.signature === signature) { return cached.value; }
        } catch (_error) { /* unavailable storage */ }
        var draft = await window.visualContextStore.loadDraft();
        if (!draft || !Array.isArray(draft.items) || !draft.items.length) {
            throw new Error('未找到可用的拍照条件，请重新上传图片后再试');
        }

        async function analyzeDraftItem(item) {
            var mode = item.mode;
            var files = mode === 'space'
                ? (draft.files && Array.isArray(draft.files.space) ? draft.files.space : [])
                : (draft.files ? draft.files[mode] : null);
            var formData = new FormData();
            formData.append('mode', mode);
            formData.append('question', item.question || '');
            formData.append('location', item.location || '');
            formData.append('scene_type', item.scene_type || 'generic');
            formData.append('consent', draft.consent_required ? 'true' : 'false');

            if (Array.isArray(files)) {
                if (!files.length) {
                    throw new Error('缺少' + (item.mode_label || mode) + '图片，请重新上传后再试');
                }
                files.forEach(function (file) {
                    formData.append('images', file);
                });
            } else {
                if (!files) {
                    throw new Error('缺少' + (item.mode_label || mode) + '图片，请重新上传后再试');
                }
                formData.append('image', files);
            }

            return window.apiClient.request('/api/ai/visual-insight', {
                method: 'POST',
                body: formData,
                signal: signal,
                timeoutMs: 110000
            }).then(function (response) {
                return response.data || {};
            });
        }

        var completed = 0;
        var total = draft.items.length;
        var resolvedItems = await Promise.all(draft.items.map(function (item) {
            return analyzeDraftItem(item).then(function (result) {
                completed += 1;
                if (typeof onProgress === 'function') {
                    onProgress(completed, total);
                }
                return result;
            });
        }));

        var resolved = {
            mode: 'bundle',
            mode_label: '多维视觉观察',
            summary: '已纳入 ' + resolvedItems.length + ' 类图片识别结果。',
            location: draft.location || '',
            scene_type: draft.scene_type || 'generic',
            image_name: resolvedItems.map(function (item) {
                return item.mode_label || item.mode || '观察';
            }).join(' / '),
            disclaimer: draft.disclaimer || '',
            items: resolvedItems.map(function (item) {
                return {
                    mode: item.mode,
                    mode_label: item.mode_label,
                    question: item.question || '',
                    location: item.location || '',
                    scene_type: item.scene_type || 'generic',
                    image_name: item.image_name || '',
                    analysis: item.analysis || '',
                    disclaimer: item.disclaimer || '',
                    structure: item.structure || {},
                    rule_scores: item.rule_scores || {}
                };
            })
        };
        try { window.sessionStorage.setItem(cacheKey, JSON.stringify({ signature: signature, value: resolved })); } catch (_error) { /* unavailable storage */ }
        return resolved;
    }

    function buildBriefAnswer(answer) {
        var text = String(answer || '').trim();
        if (!text) {
            return '已生成综合结论，请查看上方完整结果。';
        }

        var lines = text.split('\n').filter(function (line) {
            return !/^\s*#{1,6}\s+/.test(line) && !/^\s*\*\*[^*]{1,20}\*\*[:：]?\s*$/.test(line);
        }).map(function (line) {
            return line.trim();
        }).filter(Boolean);

        for (var i = 0; i < lines.length; i += 1) {
            var normalized = lines[i].replace(/^[#*\-\d.\s]+/, '').replace(/\*\*/g, '').trim();
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

    var scenarioPresets = {
        career_switch: {
            question: '我现在适合换工作吗？应该怎么做更稳？'
        },
        relationship: {
            question: '我和现在这段感情还有继续发展的可能吗？接下来应该主动还是先观察？'
        },
        startup_date: {
            question: '我准备在近期启动新项目，现在适合推进吗？如果要开始，应该注意哪些时机和风险？'
        },
        exam: {
            question: '我这次考试能顺利通过吗？接下来复习重点应该放在哪里？'
        },
        investment: {
            question: '我最近这笔投资适合继续加码吗？应该偏稳守还是阶段性获利了结？'
        },
        relocation: {
            question: '我最近适合搬家吗？这次搬动对我的生活和运势是提升还是消耗？'
        }
    };

    function applyScenarioPreset(scenarioKey) {
        var preset = scenarioPresets[scenarioKey];
        if (!preset) {
            return;
        }

        window.consultFormState.selectScenario(preset.question);
        document.getElementById('consultQuestion').focus();

        Array.prototype.forEach.call(document.querySelectorAll('[data-scenario]'), function (button) {
            button.classList.toggle('active', button.getAttribute('data-scenario') === scenarioKey);
        });
    }

    function readConsultFormState() {
        return window.consultFormState.read();
    }

    function applyConsultCondition(condition) {
        window.consultFormState.apply(condition || {});
        window.consultFormState.save();
        Array.prototype.forEach.call(document.querySelectorAll('[data-scenario]'), function (button) {
            button.classList.remove('active');
        });
    }

    function fillPersonalProfile() {
        if (!window.authClient || !window.authClient.isAuthenticated || !window.authClient.isAuthenticated()) {
            showToast('请先登录后再一键填入个人信息。', 'warn');
            if (window.authClient && window.authClient.openAuthModal) {
                window.authClient.openAuthModal('login');
            }
            return;
        }

        var profile = window.authClient.getCurrentUserProfile ? window.authClient.getCurrentUserProfile() : null;
        var birth = profile && profile.birth ? profile.birth : null;
        var hasAnyValue = false;

        if (profile && profile.gender) {
            document.getElementById('consultGender').value = profile.gender;
            hasAnyValue = true;
        }
        if (profile && profile.location) {
            document.getElementById('consultLocation').value = profile.location;
            hasAnyValue = true;
        }
        if (birth) {
            if (birth.year !== null && birth.year !== undefined) {
                document.getElementById('consultYear').value = birth.year;
                hasAnyValue = true;
            }
            if (birth.month !== null && birth.month !== undefined) {
                document.getElementById('consultMonth').value = birth.month;
                hasAnyValue = true;
            }
            if (birth.day !== null && birth.day !== undefined) {
                document.getElementById('consultDay').value = birth.day;
                hasAnyValue = true;
            }
            if (birth.hour !== null && birth.hour !== undefined) {
                document.getElementById('consultHour').value = birth.hour;
                hasAnyValue = true;
            }
            if (birth.minute !== null && birth.minute !== undefined) {
                document.getElementById('consultMinute').value = birth.minute;
                hasAnyValue = true;
            }
        }

        if (!hasAnyValue) {
            showToast('你的账号资料里还没有可填入的个人信息。', 'warn');
            return;
        }

        Array.prototype.forEach.call(document.querySelectorAll('[data-scenario]'), function (button) {
            button.classList.remove('active');
        });
        showToast('已填入你的个人资料。', 'success');
        if (window.consultFormState) { window.consultFormState.save(); }
    }

    function detectConsultLocation() {
        if (window.authClient && window.authClient.requestCurrentLocation) {
            window.authClient.requestCurrentLocation('consultLocation');
            return;
        }
        showToast('当前页面尚未加载定位能力，请稍后刷新后再试。', 'warn');
    }

    function togglePresetSaveModal(show, suggestedName) {
        var modal = document.getElementById('presetSaveModal');
        var input = document.getElementById('presetNameInput');
        var defaultInput = document.getElementById('presetDefaultInput');
        if (!modal || !input || !defaultInput) {
            return;
        }
        if (show) {
            presetModalLastFocus = document.activeElement;
        }
        modal.classList.toggle('show', !!show);
        modal.setAttribute('aria-hidden', show ? 'false' : 'true');
        document.body.classList.toggle('modal-open', !!show);
        if (show) {
            input.value = suggestedName || '';
            defaultInput.checked = false;
            input.focus();
            input.select();
        } else if (presetModalLastFocus && typeof presetModalLastFocus.focus === 'function') {
            presetModalLastFocus.focus();
            presetModalLastFocus = null;
        }
    }

    function moduleNameLabel(moduleName) {
        var labels = {
            bazi: '八字底盘',
            ziwei: '紫微命盘',
            fengshui: '风水空间',
            visual: '视觉观察',
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
        if (moduleName === 'visual') {
            if (summary.mode === 'bundle' && Array.isArray(summary.items)) {
                return [
                    '模式：多维视觉观察',
                    summary.summary || '',
                    summary.items.map(function (item) {
                        return (item.mode_label || item.mode || '观察') + '：' + (item.summary || '已纳入');
                    }).join('\n')
                ].filter(Boolean).join('\n');
            }
            var structure = summary.structure || {};
            var structureHints = [];
            if (summary.mode === 'space') {
                if (structure.lighting && structure.lighting.level) {
                    structureHints.push('采光：' + structure.lighting.level);
                }
                if (structure.clutter_level && structure.clutter_level.level) {
                    structureHints.push('杂物：' + structure.clutter_level.level);
                }
                if (structure.seat_backing && structure.seat_backing.level) {
                    structureHints.push('背靠：' + structure.seat_backing.level);
                }
                if (structure.compression_feeling && structure.compression_feeling.level) {
                    structureHints.push('压迫感：' + structure.compression_feeling.level);
                }
            } else {
                if (structure.image_quality && structure.image_quality.clarity) {
                    structureHints.push('清晰度：' + structure.image_quality.clarity);
                }
                if (structure.confidence !== undefined && structure.confidence !== null && structure.confidence !== '') {
                    structureHints.push('结构可信度：' + structure.confidence);
                }
            }
            return [
                summary.mode_label ? '模式：' + summary.mode_label : '',
                summary.location ? '地点：' + summary.location : '',
                summary.scene_type ? '场景：' + summary.scene_type : '',
                summary.summary || '',
                structureHints.length ? ('结构提取：' + structureHints.join(' ｜ ')) : '',
                summary.disclaimer ? '说明：' + summary.disclaimer : ''
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

        if (summaries.visual) {
            var visualSummary = summaries.visual || {};
            if (visualSummary.mode === 'bundle' && Array.isArray(visualSummary.items)) {
                steps.push({
                    id: 'visual_structure',
                    label: '视觉结构提取',
                    detail: '对风水图、手相图、面相图分别做结构提取并汇总。',
                    inputs: { visual: visualSummary.items },
                    rule: '多类图片先拆开提取可见特征，再统一汇总进视觉上下文。',
                    outputs: { items: visualSummary.items.map(function (item) { return item.structure || {}; }) },
                    evidence: ['已纳入 ' + visualSummary.items.length + ' 类图片条件']
                });
                steps.push({
                    id: 'visual_score',
                    label: '视觉规则吸收',
                    detail: '将结构提取结果映射为环境支持度、风险或参考可信度。',
                    inputs: { visual: visualSummary.items },
                    rule: '空间图进入环境层；手相和面相进入微观文化参考层。',
                    outputs: { summary: visualSummary.summary || '' },
                    evidence: ['视觉规则分已并入统一问事上下文']
                });
                steps.push({
                    id: 'visual_observe',
                    label: '视觉观察补充',
                    detail: visualSummary.summary || '已纳入图片观察结果。',
                    inputs: { visual: visualSummary.items },
                    rule: '将图片中可见的空间与微观线索并入统一问事。',
                    outputs: { summary: visualSummary.summary || '' },
                    evidence: (visualSummary.items || []).map(function (item) {
                        return (item.mode_label || item.mode || '观察') + '：' + (item.summary || '已纳入');
                    })
                });
            } else {
                steps.push({
                    id: 'visual_structure',
                    label: '视觉结构提取',
                    detail: '对图片做结构化可见特征提取。',
                    inputs: { visual: visualSummary },
                    rule: '先提取空间/手掌/面部中的稳定结构特征。',
                    outputs: { structure: visualSummary.structure || {} },
                    evidence: ['视觉结构字段已生成']
                });
                steps.push({
                    id: 'visual_score',
                    label: '视觉规则吸收',
                    detail: '将结构提取结果映射成规则分表。',
                    inputs: { visual: visualSummary.structure || {} },
                    rule: '结构提取结果会转为空间支持度、风险或参考可信度。',
                    outputs: { rule_scores: visualSummary.rule_scores || {} },
                    evidence: ['视觉规则分已生成']
                });
                steps.push({
                    id: 'visual_observe',
                    label: '视觉观察补充',
                    detail: visualSummary.summary || '已纳入图片观察结果。',
                    inputs: { visual: visualSummary },
                    rule: '将图片中可见的空间线索或微观文化参考信息并入统一问事上下文。',
                    outputs: { summary: visualSummary.summary || '' },
                    evidence: [visualSummary.summary || '已纳入图片观察结果。']
                });
            }
        }

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
            visual_structure: '视觉结构提取',
            visual_score: '视觉规则吸收',
            visual_observe: '视觉观察补充',
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
            visual: {
                title: '视觉观察线',
                chain: ['visual_structure', 'visual_score', 'visual_observe']
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
            if (moduleName === 'bazi') {
                mermaidLines.push('      subgraph bazi_pillars["四柱"]');
                mermaidLines.push('        direction LR');
                ['bazi_year', 'bazi_month', 'bazi_day', 'bazi_hour'].forEach(function (id) {
                    addNode(mermaidLines, id, id, '        ');
                });
                mermaidLines.push('      end');
                ['bazi_wuxing', 'bazi_shishen', 'bazi_dayun', 'bazi_judge'].forEach(function (id) {
                    addNode(mermaidLines, id, id, '      ');
                });
                mermaidLines.push('      bazi_year --> bazi_wuxing');
                mermaidLines.push('      bazi_month --> bazi_wuxing');
                mermaidLines.push('      bazi_day --> bazi_wuxing');
                mermaidLines.push('      bazi_hour --> bazi_wuxing');
                mermaidLines.push('      bazi_wuxing --> bazi_shishen --> bazi_dayun --> bazi_judge');
            } else {
                config.chain.forEach(function (id) {
                    addNode(mermaidLines, id, id, '      ');
                });
                for (var i = 0; i < config.chain.length - 1; i += 1) {
                    mermaidLines.push('      ' + config.chain[i] + ' --> ' + config.chain[i + 1]);
                }
            }
            mermaidLines.push('    end');
        });
        mermaidLines.push('  end');
        Object.keys(moduleConfigs).forEach(function (moduleName) {
            if (moduleName === 'bazi') {
                ['bazi_year', 'bazi_month', 'bazi_day', 'bazi_hour'].forEach(function (stepId) {
                    mermaidLines.push('  module_bus --> ' + stepId);
                });
            } else {
                mermaidLines.push('  module_bus --> ' + moduleConfigs[moduleName].chain[0]);
            }
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
            'visual_structure', 'visual_score', 'visual_observe',
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

    async function requestConsultation(payload, signal) {
        return window.apiClient.postJson('/api/system/consult', payload, { timeoutMs: 180000, signal: signal });
    }

    function renderConsultation(data, elements) {
        var payload = data || {};
        var summaries = payload.module_summaries || {};
        var intent = payload.intent || {};
        var aiSynthesized = Boolean(payload.ai && payload.ai.synthesized);
        var trace = payload.trace && payload.trace.mermaid ? payload.trace : payload.legacy_record ? null : buildSyntheticTrace(payload);

        if (!elements || !elements.consultAnswer || !elements.consultMeta || !elements.consultModuleGrid) {
            return;
        }

        if (elements.consultAnswerTitle) {
            elements.consultAnswerTitle.textContent = aiSynthesized ? 'AI 综合解读' : '系统结论';
        }
        if (elements.consultAnswerSource) {
            elements.consultAnswerSource.textContent = aiSynthesized
                ? 'AI 基于本次模块结果生成'
                : '基于规则与模块结果综合';
        }
        elements.consultAnswer.innerHTML = renderMarkdown(payload.answer || '系统暂未生成结论。');
        elements.consultMeta.innerHTML = []
            .concat((intent.modules || []).map(function (moduleName) {
                return '<span class="result-chip">' + esc(moduleNameLabel(moduleName)) + '</span>';
            }))
            .concat(intent.matter_type ? ['<span class="result-chip">事项：' + esc(intent.matter_type) + '</span>'] : [])
            .concat(intent.purpose ? ['<span class="result-chip">用途：' + esc(intent.purpose) + '</span>'] : [])
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
                '  <div class="title">模块依据</div>',
                '  <div class="body">' + esc('这份记录没有保存模块摘要。') + '</div>',
                '</div>'
            ].join('');

        if (window.decisionPanel && elements.consultDecisionGrid) {
            window.decisionPanel.render(payload, elements.consultDecisionGrid);
        }
        if (!trace && elements.consultTraceDiagram) {
            elements.consultTraceDiagram.textContent = '这份早期记录未保存计算流程。';
            elements.consultTraceSteps.textContent = '';
        }
        if (trace && window.tracePanel && elements.consultTraceDiagram && elements.consultTraceSteps) {
            window.tracePanel.renderDiagram(trace, elements.consultTraceDiagram);
            window.tracePanel.renderSteps(trace, elements.consultTraceSteps);
        }
        if (elements.consultResult && elements.consultResult.classList) {
            elements.consultResult.classList.add('show');
        }
        if (elements.consultResult && elements.consultResult.scrollIntoView) {
            elements.consultResult.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }

    function renderResultHeader(data, elements) {
        var payload = data || {};
        var intent = payload.intent || {};
        var profile = payload.profile || {};
        var birth = profile.birth || {};
        var summaryNode = elements.resultSummary;
        var questionNode = elements.resultQuestion;
        var chipsNode = elements.resultChips;
        var timestampNode = elements.resultTimestamp;
        var backLink = elements.resultBackLink;

        if (questionNode) {
            questionNode.textContent = payload.question || '本次统一问事结果';
        }

        if (summaryNode) {
            summaryNode.textContent = buildBriefAnswer(payload.answer || '');
        }

        if (chipsNode) {
            chipsNode.innerHTML = []
                .concat((intent.modules || []).map(function (moduleName) {
                    return '<span class="result-chip">' + esc(moduleNameLabel(moduleName)) + '</span>';
                }))
                .concat(intent.matter_type ? ['<span class="result-chip">事项：' + esc(intent.matter_type) + '</span>'] : [])
                .concat(intent.purpose ? ['<span class="result-chip">用途：' + esc(intent.purpose) + '</span>'] : [])
                .concat(profile.location ? ['<span class="result-chip">地点：' + esc(profile.location) + '</span>'] : [])
                .concat(birth.year ? ['<span class="result-chip">生辰：' + esc([birth.year, birth.month, birth.day, birth.hour].filter(function (value) { return value != null; }).join('-')) + '</span>'] : [])
                .filter(Boolean)
                .join('');
        }

        if (timestampNode) {
            var timestamp = payload.created_at || readLatestConsultationTimestamp();
            timestampNode.textContent = timestamp ? ('生成时间：' + new Date(timestamp).toLocaleString()) : '';
        }

        if (backLink) {
            backLink.setAttribute('href', window.consultSession.url('index.html', { new: 1 }));
        }
    }

    function activateResultTab(tabId, tabsRoot, panelsRoot) {
        if (!tabsRoot || !panelsRoot) {
            return;
        }

        tabsRoot.setAttribute('role', 'tablist');
        Array.prototype.forEach.call(tabsRoot.querySelectorAll('[data-result-tab]'), function (button) {
            button.id = 'result-tab-' + button.getAttribute('data-result-tab');
            button.setAttribute('role', 'tab');
            var isActive = button.getAttribute('data-result-tab') === tabId;
            button.classList.toggle('active', isActive);
            button.setAttribute('aria-selected', isActive ? 'true' : 'false');
            button.tabIndex = isActive ? 0 : -1;
            button.setAttribute('aria-controls', 'result-panel-' + button.getAttribute('data-result-tab'));
        });

        Array.prototype.forEach.call(panelsRoot.querySelectorAll('[data-result-panel]'), function (panel) {
            var isActive = panel.getAttribute('data-result-panel') === tabId;
            panel.id = 'result-panel-' + panel.getAttribute('data-result-panel');
            panel.setAttribute('role', 'tabpanel');
            panel.setAttribute('aria-labelledby', 'result-tab-' + panel.getAttribute('data-result-panel'));
            panel.classList.toggle('active', isActive);
            panel.hidden = !isActive;
        });
    }

    function renderWorkspaceResult(data) {
        var workspace = document.getElementById('consultResultWorkspace');
        if (!workspace) {
            return;
        }

        var emptyState = document.getElementById('consultResultEmpty');
        var tabsRoot = document.getElementById('resultTabs');
        var panelsRoot = document.getElementById('resultPanels');
        var elements = {
            consultResult: workspace,
            consultAnswer: document.getElementById('consultAnswer'),
            consultAnswerTitle: document.getElementById('consultAnswerTitle'),
            consultAnswerSource: document.getElementById('consultAnswerSource'),
            consultMeta: document.getElementById('consultMeta'),
            consultDecisionGrid: document.getElementById('consultDecisionGrid'),
            consultModuleGrid: document.getElementById('consultModuleGrid'),
            consultTraceDiagram: document.getElementById('consultTraceDiagram'),
            consultTraceSteps: document.getElementById('consultTraceSteps'),
            consultTraceSummary: document.getElementById('consultTraceSummary'),
            resultSummary: document.getElementById('resultHeroSummary'),
            resultQuestion: document.getElementById('resultHeroQuestion'),
            resultChips: document.getElementById('resultHeroChips'),
            resultTimestamp: document.getElementById('resultHeroTimestamp'),
            resultBackLink: document.getElementById('resultBackLink')
        };

        if (!data) {
            workspace.style.display = 'none';
            if (emptyState) {
                emptyState.style.display = '';
            }
            return;
        }

        if (emptyState) {
            emptyState.style.display = 'none';
        }
        workspace.style.display = '';
        renderResultHeader(data, elements);
        renderConsultation(data, elements);

        if (tabsRoot && panelsRoot) {
            Array.prototype.forEach.call(tabsRoot.querySelectorAll('[data-result-tab]'), function (button) {
                button.onclick = function () {
                    var tab = button.getAttribute('data-result-tab');
                    activateResultTab(tab, tabsRoot, panelsRoot);
                    var url = new URL(window.location.href); url.searchParams.set('tab', tab);
                    window.history.replaceState(null, '', url);
                };
                button.onkeydown = function (event) {
                    var buttons = Array.from(tabsRoot.querySelectorAll('[data-result-tab]'));
                    var index = buttons.indexOf(button), target;
                    if (event.key === 'ArrowRight') { target = buttons[(index + 1) % buttons.length]; }
                    if (event.key === 'ArrowLeft') { target = buttons[(index + buttons.length - 1) % buttons.length]; }
                    if (event.key === 'Home') { target = buttons[0]; }
                    if (event.key === 'End') { target = buttons[buttons.length - 1]; }
                    if (target) { event.preventDefault(); target.click(); target.focus(); }
                };
            });
            var selected = new URLSearchParams(window.location.search).get('tab');
            activateResultTab(['summary', 'decision', 'modules', 'trace'].includes(selected) ? selected : 'summary', tabsRoot, panelsRoot);
        }
    }

    function initializeResultWorkspace() {
        window.consultWorkspace.initialize();
    }

    function initializeConsultPanel() {
        var consultForm = document.getElementById('consultForm');
        if (!consultForm) {
            return;
        }

        window.consultFormState.initialize();
        var submitting = false;
        var submitButton = consultForm.querySelector('button[type=submit]');
        function refreshSubmitHint() {
            var hint = document.getElementById('consultSubmitHint');
            if (hint && !submitting) { hint.textContent = window.authClient.isAuthenticated() ? '' : '登录后即可分析，已填写的内容会保留。'; }
        }
        window.addEventListener('auth-session-changed', refreshSubmitHint);
        refreshSubmitHint();
        function keepFocusedFieldVisible() {
            var field = document.activeElement;
            if (window.innerWidth > 768 || !field || !consultForm.contains(field) || !field.matches('input, textarea, select')) { return; }
            var rect = field.getBoundingClientRect();
            var footerTop = consultForm.querySelector('.consult-actions').getBoundingClientRect().top;
            var top = window.visualViewport ? window.visualViewport.offsetTop : 0;
            var bottom = Math.min(footerTop - 16, top + (window.visualViewport ? window.visualViewport.height : window.innerHeight));
            if (rect.bottom > bottom || rect.top < top) {
                window.scrollBy({ top: rect.top - Math.max(top + 12, (top + bottom - rect.height) / 2), behavior: 'smooth' });
            }
        }
        consultForm.addEventListener('focusin', function () { requestAnimationFrame(keepFocusedFieldVisible); });
        if (window.visualViewport) { window.visualViewport.addEventListener('resize', keepFocusedFieldVisible); }
        document.getElementById('consultQuestion').addEventListener('keydown', function (event) {
            if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) { event.preventDefault(); consultForm.requestSubmit(); }
        });

        var elements = {
            consultLoading: document.getElementById('consultLoading'),
            consultLoadingFill: document.getElementById('consultLoadingFill'),
            consultLoadingPercent: document.getElementById('consultLoadingPercent'),
            consultLoadingText: document.getElementById('consultLoadingText'),
            consultLoadingLabel: document.getElementById('consultLoadingLabel'),
            consultResult: document.getElementById('consultResult'),
            consultAnswer: document.getElementById('consultAnswer'),
            consultAnswerTitle: document.getElementById('consultAnswerTitle'),
            consultAnswerSource: document.getElementById('consultAnswerSource'),
            consultMeta: document.getElementById('consultMeta'),
            consultDecisionGrid: document.getElementById('consultDecisionGrid'),
            consultModuleGrid: document.getElementById('consultModuleGrid'),
            consultTraceDiagram: document.getElementById('consultTraceDiagram'),
            consultTraceSteps: document.getElementById('consultTraceSteps'),
            consultTraceSummary: document.getElementById('consultTraceSummary')
        };

        var visualContextBanner = document.createElement('div');
        visualContextBanner.className = 'visual-context-banner';
        visualContextBanner.id = 'visualContextBanner';
        consultForm.insertBefore(visualContextBanner, consultForm.firstChild);

        var consultLoadingTimer = null, activeConsultController = null;
        function showConsultLoading() {
            elements.consultLoading.classList.add('show');
            elements.consultLoading.setAttribute('aria-hidden', 'false');
            var cancelBtn = document.getElementById('cancelConsultBtn');
            if (cancelBtn) { cancelBtn.hidden = false; cancelBtn.disabled = false; cancelBtn.textContent = '停止等待'; }
            elements.consultLoadingLabel.textContent = '正在分析，请稍候';
            elements.consultLoadingText.textContent = '正在结合问题和补充条件生成结果，完成后将自动打开工作台。';
            var started = Date.now();
            var elapsed = document.getElementById('consultLoadingElapsed');
            function update() { if (elapsed) { elapsed.textContent = '已等待 ' + Math.floor((Date.now() - started) / 1000) + ' 秒'; } }
            update();
            consultLoadingTimer = window.setInterval(update, 1000);
        }
        function hideConsultLoading() {
            window.clearInterval(consultLoadingTimer);
            elements.consultLoading.classList.remove('show');
            elements.consultLoading.setAttribute('aria-hidden', 'true');
            var cancelBtn = document.getElementById('cancelConsultBtn');
            if (cancelBtn) { cancelBtn.hidden = true; }
        }

        function renderVisualContextBanner() {
            var context = readVisualContext();
            if (!context) {
                visualContextBanner.innerHTML = '';
                visualContextBanner.classList.remove('show');
                return;
            }
            visualContextBanner.classList.add('show');
            var modePill = context.mode === 'bundle'
                ? ('已纳入 ' + ((context.items && context.items.length) || 0) + ' 类图片')
                : (context.mode_label || '视觉观察');
            var title = context.mode === 'bundle'
                ? '本次问事将自动带入已保存的多类图片条件'
                : '本次问事将自动带入最近一次图片观察结果';
            var summaryText = context.summary || '已带入最近一次图片分析结果';
            if (context.kind === 'draft') {
                summaryText = context.summary || '已保存图片条件，提交统一问事时会自动完成视觉识别。';
            }
            var meta = '';
            if (context.mode === 'bundle' && Array.isArray(context.items)) {
                meta = context.items.map(function (item) {
                    return (item.mode_label || item.mode || '观察') + ' · ' + (item.image_name || '未命名图片');
                }).join(' ｜ ');
            } else {
                meta = (context.location ? ('地点：' + context.location + ' · ') : '') + (context.image_name || '未命名图片');
            }
            visualContextBanner.innerHTML = [
                '<div class="visual-context-head">',
                '  <span class="visual-context-kicker">Visual Context</span>',
                '  <span class="visual-context-pill">' + esc(modePill) + '</span>',
                '</div>',
                '<div class="visual-context-title">' + esc(title) + '</div>',
                '<div class="visual-context-meta">' + esc(summaryText) + '</div>',
                '<div class="visual-context-meta">' + esc(meta) + '</div>',
                '<div class="visual-context-actions">',
                '  <button type="button" class="visual-context-btn" id="reopenVisualContextBtn">继续拍照/上传</button>',
                '  <button type="button" class="visual-context-btn" id="clearVisualContextBtn">移除图片上下文</button>',
                '  </div>',
            ].join('');
            var reopenBtn = document.getElementById('reopenVisualContextBtn');
            var clearBtn = document.getElementById('clearVisualContextBtn');
            if (reopenBtn) {
                reopenBtn.addEventListener('click', function () {
                    openVisualInsightModal();
                });
            }
            if (clearBtn) {
                clearBtn.addEventListener('click', function () {
                    Promise.resolve(
                        window.visualContextStore && window.visualContextStore.clear
                            ? window.visualContextStore.clear()
                            : (function () {
                                try {
                                    window.localStorage.removeItem(VISUAL_CONTEXT_STORAGE_KEY);
                                } catch (_error) {}
                            })()
                    ).finally(function () {
                        renderVisualContextBanner();
                        showToast('已移除本次问事的图片上下文。', 'success');
                    });
                });
            }
        }

        var visualInsightModal = document.getElementById('visualInsightModal');
        var visualInsightFrame = document.getElementById('visualInsightFrame');
        var closeVisualInsightModalBtn = document.getElementById('closeVisualInsightModalBtn');
        var openVisualInsightModalBtn = document.getElementById('openVisualInsightModalBtn');
        var visualInsightLastFocus = null;

        function openVisualInsightModal() {
            if (!visualInsightModal) {
                return;
            }
            visualInsightLastFocus = document.activeElement;
            if (visualInsightFrame && !visualInsightFrame.getAttribute('src')) {
                var source = visualInsightFrame.getAttribute('data-src');
                if (source) {
                    visualInsightFrame.setAttribute('src', source);
                }
            }
            visualInsightModal.classList.add('show');
            visualInsightModal.setAttribute('aria-hidden', 'false');
            document.body.classList.add('modal-open');
            window.setTimeout(function () {
                if (closeVisualInsightModalBtn) {
                    closeVisualInsightModalBtn.focus();
                }
            }, 0);
        }

        function closeVisualInsightModal() {
            if (!visualInsightModal) {
                return;
            }
            visualInsightModal.classList.remove('show');
            visualInsightModal.setAttribute('aria-hidden', 'true');
            document.body.classList.remove('modal-open');
            if (visualInsightLastFocus && typeof visualInsightLastFocus.focus === 'function') {
                visualInsightLastFocus.focus();
                visualInsightLastFocus = null;
            }
            renderVisualContextBanner();
        }

        if (openVisualInsightModalBtn) {
            openVisualInsightModalBtn.addEventListener('click', function () {
                openVisualInsightModal();
            });
        }
        if (closeVisualInsightModalBtn) {
            closeVisualInsightModalBtn.addEventListener('click', function () {
                closeVisualInsightModal();
            });
        }
        if (visualInsightModal) {
            visualInsightModal.addEventListener('click', function (event) {
                if (event.target === visualInsightModal) {
                    closeVisualInsightModal();
                }
            });
        }
        window.addEventListener('message', function (event) {
            if (event.origin !== window.location.origin) {
                return;
            }
            var data = event && event.data ? event.data : {};
            if (data.type === 'visual-context-updated') {
                renderVisualContextBanner();
                return;
            }
            if (data.type === 'visual-context-close') {
                closeVisualInsightModal();
            }
        });
        function trapModalFocus(modal, event) {
            var focusable = Array.prototype.slice.call(modal.querySelectorAll('button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), iframe, a[href]'))
                .filter(function (node) { return node.offsetParent !== null; });
            if (!focusable.length || event.key !== 'Tab') {
                return;
            }
            var first = focusable[0];
            var last = focusable[focusable.length - 1];
            if (event.shiftKey && document.activeElement === first) {
                event.preventDefault();
                last.focus();
            } else if (!event.shiftKey && document.activeElement === last) {
                event.preventDefault();
                first.focus();
            }
        }

        document.addEventListener('keydown', function (event) {
            if (visualInsightModal && visualInsightModal.classList.contains('show')) {
                if (event.key === 'Escape') {
                    event.preventDefault();
                    closeVisualInsightModal();
                    return;
                }
                trapModalFocus(visualInsightModal, event);
                return;
            }
            if (presetModal && presetModal.classList.contains('show')) {
                if (event.key === 'Escape') {
                    event.preventDefault();
                    togglePresetSaveModal(false);
                    return;
                }
                trapModalFocus(presetModal, event);
            }
        });

        renderVisualContextBanner();

        consultForm.addEventListener('submit', async function (event) {
            event.preventDefault();
            if (submitting) { return; }
            if (!window.consultFormState.ready()) { showToast('正在恢复条件，请稍候再提交。', 'info'); return; }
            if (!window.authClient || !window.authClient.isAuthenticated || !window.authClient.isAuthenticated()) {
                showToast('统一问事需要先登录账号。', 'warn');
                if (window.authClient && window.authClient.openAuthModal) {
                    window.authClient.openAuthModal('login');
                }
                return;
            }
            var question = document.getElementById('consultQuestion').value.trim();
            if (!question) {
                showToast('请先输入你想问的事情。', 'warn');
                document.getElementById('consultQuestion').focus();
                return;
            }

            var payload = window.consultFormState.read();
            payload.gender = payload.gender || null;
            payload.location = payload.location || null;
            window.consultFormState.save();
            var submissionOwner = window.consultSession.owner();
            var visualManifest = readVisualContext();
            payload.request_id = window.consultSession.requestId('consult', JSON.stringify(payload) + '|' + (visualManifest && visualManifest.saved_at || ''));
            submitting = true; submitButton.disabled = true;
            var disabledNodes = Array.from(consultForm.querySelectorAll('input, textarea, select, button')).filter(function (node) { return node !== submitButton && !node.disabled; });
            disabledNodes.forEach(function (node) { node.disabled = true; });
            consultForm.setAttribute('aria-busy', 'true');
            var hint = document.getElementById('consultSubmitHint');
            hint.textContent = '分析进行中，请勿重复提交。';

            activeConsultController = typeof AbortController !== 'undefined' ? new AbortController() : null;
            showConsultLoading();
            if (elements.consultResult && elements.consultResult.classList) {
                elements.consultResult.classList.remove('show');
            }

            try {
                payload.visual_context = await resolveVisualContextForConsult(activeConsultController && activeConsultController.signal) || payload.visual_context || null;
                var response = await requestConsultation(payload, activeConsultController && activeConsultController.signal);
                saveLatestConsultation(response.data, submissionOwner);
                window.consultSession.clearRequestId('consult', submissionOwner);
                if (response.data && response.data.account_history && response.data.account_history.saved && window.authClient) {
                    window.authClient.refreshHistory({ preserveDetail: true }).catch(function () {
                        // Ignore history refresh failures after a successful consult.
                    });
                }
                window.location.href = buildConsultResultUrl(response.data);
            } catch (error) {
                hint.textContent = error.code === 'REQUEST_TIMEOUT'
                    ? '等待超时，分析可能仍在继续。请先查看历史；再次提交相同条件会复用本次请求。'
                    : '分析失败：' + error.message + ' 输入内容已保留，可修改或重试。';
                if (error.code === 'request_aborted') {
                    hint.textContent = '已停止等待，分析可能仍在继续。可查看历史，或重试相同条件。';
                } else { showToast('系统分析失败：' + error.message, 'error'); }
            } finally {
                activeConsultController = null;
                submitting = false; submitButton.disabled = false;
                disabledNodes.forEach(function (node) { node.disabled = false; });
                consultForm.removeAttribute('aria-busy');
                hideConsultLoading();
            }
        });

        var cancelConsultBtn = document.getElementById('cancelConsultBtn');
        if (cancelConsultBtn) {
            cancelConsultBtn.addEventListener('click', function () {
                if (activeConsultController) {
                    activeConsultController.abort();
                    showToast('已停止等待，分析可能仍在继续。', 'info');
                }
            });
        }

        document.getElementById('fillDemoBtn').addEventListener('click', function () {
            fillPersonalProfile();
        });

        var detectConsultLocationBtn = document.getElementById('detectConsultLocationBtn');
        if (detectConsultLocationBtn) {
            detectConsultLocationBtn.addEventListener('click', function () {
                detectConsultLocation();
            });
        }

        Array.prototype.forEach.call(document.querySelectorAll('[data-scenario]'), function (button) {
            button.addEventListener('click', function () {
                applyScenarioPreset(button.getAttribute('data-scenario'));
            });
        });

        document.getElementById('clearConsultBtn').addEventListener('click', function () {
            window.consultFormState.clear();
            hideConsultLoading();
            if (elements.consultResult && elements.consultResult.classList) {
                elements.consultResult.classList.remove('show');
            }
            Array.prototype.forEach.call(document.querySelectorAll('[data-scenario]'), function (button) {
                button.classList.remove('active');
            });
        });

        document.getElementById('saveCurrentConditionBtn').addEventListener('click', async function () {
            if (!window.authClient || !window.authClient.isAuthenticated || !window.authClient.isAuthenticated()) {
                showToast('请先登录后再保存常用条件。', 'warn');
                if (window.authClient && window.authClient.openAuthModal) {
                    window.authClient.openAuthModal('login');
                }
                return;
            }
            var current = readConsultFormState();
            var defaultName = current.question ? current.question.slice(0, 18) : '我的常用问事条件';
            togglePresetSaveModal(true, defaultName);
        });

        var presetSaveForm = document.getElementById('presetSaveForm');
        var presetModal = document.getElementById('presetSaveModal');
        var presetModalClose = document.getElementById('presetModalClose');
        var presetModalCancel = document.getElementById('presetModalCancel');

        if (presetSaveForm) {
            presetSaveForm.addEventListener('submit', async function (event) {
                event.preventDefault();
                var presetName = document.getElementById('presetNameInput').value.trim();
                if (!presetName) {
                    showToast('常用条件名称不能为空。', 'warn');
                    return;
                }
                var current = readConsultFormState();
                try {
                    await window.authClient.saveConsultPreset({
                        name: presetName,
                        question: current.question,
                        year: current.year,
                        month: current.month,
                        day: current.day,
                        hour: current.hour,
                        minute: current.minute,
                        gender: current.gender,
                        location: current.location,
                        is_default: !!document.getElementById('presetDefaultInput').checked
                    });
                    togglePresetSaveModal(false);
                    showToast('已保存到“我的常用条件”。', 'success');
                } catch (error) {
                    showToast('保存失败：' + error.message, 'error');
                }
            });
        }

        if (presetModalClose) {
            presetModalClose.addEventListener('click', function () {
                togglePresetSaveModal(false);
            });
        }
        if (presetModalCancel) {
            presetModalCancel.addEventListener('click', function () {
                togglePresetSaveModal(false);
            });
        }
        if (presetModal) {
            presetModal.addEventListener('click', function (event) {
                if (event.target === presetModal) {
                    togglePresetSaveModal(false);
                }
            });
        }
    }

    window.consultPanel = {
        initialize: initializeConsultPanel,
        initializeResultWorkspace: initializeResultWorkspace,
        renderWorkspaceResult: renderWorkspaceResult,
        buildSyntheticTrace: buildSyntheticTrace,
        moduleNameLabel: moduleNameLabel,
        readLatestConsultation: readLatestConsultation,
        applyDefaultSavedCondition: function () {
            if (!window.consultFormState || !window.consultFormState.canApplyDefault() || !window.authClient || !window.authClient.getDefaultConsultPreset) {
                return;
            }
            var preset = window.authClient.getDefaultConsultPreset();
            if (!preset) {
                return;
            }
            applyConsultCondition(preset);
        },
        applySavedCondition: function (presetId) {
            if (!window.authClient || !window.authClient.getConsultPresets) {
                return;
            }
            var preset = (window.authClient.getConsultPresets() || []).find(function (item) {
                return item.preset_id === presetId;
            });
            if (!preset) {
                showToast('未找到该常用条件。', 'warn');
                return;
            }
            applyConsultCondition(preset);
            showToast('已套用常用条件：' + (preset.name || '未命名条件'), 'success');
        }
    };
})();
