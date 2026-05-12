(function () {
    // Keeps the legacy embedded bazi panel working after index.html script extraction.
    var esc = window.escapeHtml || function (value) { return String(value ?? ''); };
    var DAY_GAN_TO_WUXING = {
        '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
        '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'
    };
    var WUXING_ADJUSTMENTS = {
        '木': '可通过阅读、学习、植物环境来扶木。',
        '火': '可通过运动、社交、作息规律来扶火。',
        '土': '可通过稳定节奏、饮食调理与执行计划来扶土。',
        '金': '可通过纪律、结构化工作与技能打磨来扶金。',
        '水': '可通过深度思考、复盘和睡眠管理来扶水。'
    };

    function renderMarkdown(text) {
        return window.renderMarkdownSimple(text, '#173a34');
    }

    function getBalanceLevel(diff) {
        if (diff < 2) return '平衡';
        if (diff < 4) return '轻度偏颇';
        return '明显偏颇';
    }

    function getDominantElement(wuxingCount) {
        var entries = Object.entries(wuxingCount || {});
        if (!entries.length) {
            return ['未知', 0];
        }
        entries.sort(function (a, b) { return b[1] - a[1]; });
        return entries[0];
    }

    function initializeAIStatusBanner() {
        var monitor = window.createAIStatusMonitor({
            bannerId: 'aiStatusBanner',
            dotId: 'aiStatusDot',
            textId: 'aiStatusText',
            intervalMs: 30000,
            renderStatus: function (state, data, _prev, elements) {
                elements.banner.style.display = 'block';
                if (state === 'available') {
                    elements.banner.classList.add('available');
                    elements.dot.style.background = '#3d7a59';
                    elements.text.textContent = '✓ AI服务正常 (' + (data.model || '模型信息不可用') + ')';
                    elements.text.style.color = '#3d7a59';
                } else if (state === 'degraded') {
                    elements.banner.classList.remove('available');
                    elements.dot.style.background = '#b5802f';
                    elements.text.textContent = '⚠️ AI服务波动中 - 将自动回退基础分析';
                    elements.text.style.color = '#8a6526';
                } else if (state === 'unconfigured') {
                    elements.banner.classList.remove('available');
                    elements.dot.style.background = '#b5802f';
                    elements.text.textContent = '⚠️ AI服务未配置 - 点击右侧查看配置指南';
                    elements.text.style.color = '#8a6526';
                } else {
                    elements.banner.classList.remove('available');
                    elements.dot.style.background = '#aa5548';
                    elements.text.textContent = '⚠️ 后端连接异常 - 请检查服务状态';
                    elements.text.style.color = '#aa5548';
                }
            }
        });
        monitor.start();
    }

    function displayResult(data) {
        var birthInfo = data.birth_info;
        document.getElementById('birthInfoText').innerHTML = [
            '<strong>阳历：</strong>' + esc(birthInfo.solar.year) + '年' + esc(birthInfo.solar.month) + '月' + esc(birthInfo.solar.day) + '日 ' + esc(birthInfo.solar.hour) + '时' + esc(birthInfo.solar.minute) + '分<br>',
            '<strong>农历：</strong>' + esc(birthInfo.lunar.year) + '年' + esc(birthInfo.lunar.month) + '月' + esc(birthInfo.lunar.day) + '日 ' + (birthInfo.lunar.is_leap ? '(闰月)' : '') + '<br>',
            '<strong>性别：</strong>' + esc(birthInfo.gender)
        ].join('');

        var pillars = ['年柱', '月柱', '日柱', '时柱'];
        var baziValues = [data.bazi.year, data.bazi.month, data.bazi.day, data.bazi.hour];
        var baziDisplay = document.getElementById('baziDisplay');
        baziDisplay.innerHTML = '';
        pillars.forEach(function (title, index) {
            baziDisplay.innerHTML += [
                '<div class="pillar">',
                '  <div class="pillar-title">' + title + '</div>',
                '  <div class="pillar-content">' + esc(baziValues[index]) + '</div>',
                '</div>'
            ].join('');
        });

        var wuxingChart = document.getElementById('wuxingChart');
        var wuxingColors = {
            '木': 'wuxing-wood',
            '火': 'wuxing-fire',
            '土': 'wuxing-earth',
            '金': 'wuxing-metal',
            '水': 'wuxing-water'
        };
        wuxingChart.innerHTML = '';
        Object.entries(data.wuxing_count).forEach(function (entry) {
            var element = entry[0];
            var count = entry[1];
            wuxingChart.innerHTML += [
                '<div class="wuxing-item ' + wuxingColors[element] + '">',
                '  <div>' + esc(element) + '</div>',
                '  <div class="count">' + count.toFixed(1) + '</div>',
                '</div>'
            ].join('');
        });

        document.getElementById('shishenInfo').innerHTML = [
            '<div class="shishen-grid">',
            '  <div class="shishen-item"><strong>年干：</strong>' + esc(data.shishen.year_gan) + '</div>',
            '  <div class="shishen-item"><strong>月干：</strong>' + esc(data.shishen.month_gan) + '</div>',
            '  <div class="shishen-item"><strong>日干：</strong>' + esc(data.shishen.day_gan) + '（命主）</div>',
            '  <div class="shishen-item"><strong>时干：</strong>' + esc(data.shishen.hour_gan) + '</div>',
            '</div>'
        ].join('');

        var dayunList = document.getElementById('dayunList');
        dayunList.innerHTML = '';
        data.dayun.forEach(function (dayun) {
            dayunList.innerHTML += [
                '<div class="dayun-item">',
                '  <div class="dayun-ganzhi">' + esc(dayun.ganzhi) + '</div>',
                '  <div class="dayun-age">' + esc(dayun.start_age) + '-' + esc(dayun.end_age) + '岁</div>',
                '</div>'
            ].join('');
        });

        var analysis = data.analysis;
        document.getElementById('analysisContent').innerHTML = [
            '<div class="analysis-box info"><h4>五行概况</h4><p>' + esc(analysis.wuxing_summary) + '</p></div>',
            '<div class="analysis-box success"><h4>最旺五行：' + esc(analysis.strong_element.element) + '</h4><p>' + esc(analysis.strong_element.advice) + '</p></div>',
            '<div class="analysis-box warn"><h4>最弱五行：' + esc(analysis.weak_element.element) + '</h4><p>' + esc(analysis.weak_element.advice) + '</p></div>',
            '<div class="analysis-box"><h4>平衡建议</h4><p>' + esc(analysis.balance_advice) + '</p></div>',
            '<p class="text-muted light-note">' + esc(analysis.disclaimer) + '</p>'
        ].join('');

        var wuxingEntries = Object.entries(data.wuxing_count || {}).sort(function (a, b) { return b[1] - a[1]; });
        var topElement = wuxingEntries[0] || ['未知', 0];
        var weakElement = wuxingEntries[wuxingEntries.length - 1] || ['未知', 0];
        var totalWuxing = wuxingEntries.reduce(function (sum, item) { return sum + Number(item[1] || 0); }, 0);
        var avgWuxing = wuxingEntries.length ? totalWuxing / wuxingEntries.length : 0;
        var gap = Number((topElement[1] - weakElement[1]).toFixed(2));
        var dayMasterGan = data.bazi && data.bazi.day ? String(data.bazi.day).charAt(0) : '';
        var dayMasterElement = DAY_GAN_TO_WUXING[dayMasterGan] || '未知';
        var dominantNayin = getDominantElement(data.wuxing_count || {})[0];

        document.getElementById('baseInsightContent').innerHTML = [
            '<div class="metric-grid">',
            '  <div class="metric-item"><div class="metric-label">平衡等级</div><div class="metric-value">' + esc(getBalanceLevel(gap)) + '</div></div>',
            '  <div class="metric-item"><div class="metric-label">五行最大差值</div><div class="metric-value">' + esc(gap.toFixed(2)) + '</div></div>',
            '  <div class="metric-item"><div class="metric-label">日主五行</div><div class="metric-value">' + esc(dayMasterGan) + ' · ' + esc(dayMasterElement) + '</div></div>',
            '  <div class="metric-item"><div class="metric-label">命局主导元素</div><div class="metric-value">' + esc(dominantNayin) + '</div></div>',
            '</div>',
            '<div class="analysis-box info"><h4>调衡优先级</h4><p>' + wuxingEntries.map(function (item, idx) { return (idx + 1) + '. ' + esc(item[0]) + '(' + Number(item[1]).toFixed(1) + ')'; }).join(' ｜ ') + '</p></div>',
            '<div class="analysis-box warn"><h4>传统补益方向</h4><p><strong>' + esc(weakElement[0]) + '</strong>偏弱，' + esc(WUXING_ADJUSTMENTS[weakElement[0]] || '建议以作息和节奏管理为先。') + '</p><p class="text-muted">均衡参考值约为 ' + avgWuxing.toFixed(1) + '，当前最大偏差为 ' + gap.toFixed(2) + '。</p></div>',
            '<div class="analysis-box success"><h4>纳音提示</h4><p>年柱：' + esc(data.nayin.year) + ' ｜ 月柱：' + esc(data.nayin.month) + ' ｜ 日柱：' + esc(data.nayin.day) + ' ｜ 时柱：' + esc(data.nayin.hour) + '</p></div>'
        ].join('');

        if (data.advanced_analysis) {
            var adv = data.advanced_analysis;
            var geju = adv.geju;
            document.getElementById('gejuContent').innerHTML = [
                '<div class="analysis-box success"><h4>命局强弱：' + esc(geju.strength_level) + ' (' + esc(geju.strength.toFixed(2)) + ')</h4><p><strong>格局类型：</strong>' + esc(geju.pattern_type) + '</p><p class="light-note">' + esc(geju.pattern_description) + '</p></div>',
                '<div class="analysis-box warn"><h4>适合职业</h4><p>' + (geju.suitable_career || []).map(function (item) { return esc(item); }).join('、') + '</p></div>',
                '<div class="analysis-box info"><h4>人生建议</h4><p>' + esc(geju.life_advice) + '</p></div>'
            ].join('');

            var shensha = adv.shensha;
            var shenshaHTML = '<p><strong>' + esc(shensha.summary) + '</strong></p>';
            if (shensha.shensha_list && shensha.shensha_list.length > 0) {
                shensha.shensha_list.forEach(function (item) {
                    var statusClass = item.type === '大吉' ? 'success' : item.type === '吉' ? 'info' : 'warn';
                    shenshaHTML += '<div class="analysis-box ' + statusClass + '"><h4>' + esc(item.name) + ' <span class="tag">' + esc(item.type) + '</span></h4><p>' + esc(item.description) + '</p></div>';
                });
            } else {
                shenshaHTML += '<p class="text-muted">命局中暂无明显神煞，属于平和之象。</p>';
            }
            document.getElementById('shenshaContent').innerHTML = shenshaHTML;

            var liuqin = adv.liuqin;
            document.getElementById('liuqinContent').innerHTML = [
                '<div class="analysis-box"><h4>👨 父亲</h4><p>' + esc(liuqin.father) + '</p></div>',
                '<div class="analysis-box"><h4>👩 母亲</h4><p>' + esc(liuqin.mother) + '</p></div>',
                '<div class="analysis-box"><h4>👫 兄弟姐妹</h4><p>' + esc(liuqin.siblings) + '</p></div>',
                '<div class="analysis-box"><h4>💑 配偶</h4><p>' + esc(liuqin.spouse) + '</p></div>',
                '<div class="analysis-box"><h4>👶 子女</h4><p>' + esc(liuqin.children) + '</p></div>'
            ].join('');
        }

        if (data.ai_analysis) {
            document.getElementById('aiAnalysisSection').style.display = 'block';
            document.getElementById('aiAnalysisContent').innerHTML = renderMarkdown(data.ai_analysis);
        } else {
            document.getElementById('aiAnalysisSection').style.display = 'none';
        }

        document.getElementById('result').classList.add('show');
        document.getElementById('result').scrollIntoView({ behavior: 'smooth' });
    }

    async function calculateWithAI() {
        var data = {
            year: parseInt(document.getElementById('year').value, 10),
            month: parseInt(document.getElementById('month').value, 10),
            day: parseInt(document.getElementById('day').value, 10),
            hour: parseInt(document.getElementById('hour').value, 10),
            minute: parseInt(document.getElementById('minute').value, 10),
            gender: document.getElementById('gender').value
        };

        document.getElementById('loading').classList.add('show');
        document.getElementById('loading').querySelector('p').textContent = '正在进行AI深度分析，请稍候...';
        document.getElementById('result').classList.remove('show');

        try {
            var result = await window.apiClient.postJson('/api/ai/enhance-bazi', data);
            if (!result.ai_enhanced && result.ai_message) {
                showToast(result.ai_message, 'warn');
            }
            displayResult(result.data);
            if (result.data.ai_analysis) {
                setTimeout(function () {
                    document.getElementById('aiAnalysisSection').scrollIntoView({ behavior: 'smooth', block: 'center' });
                }, 500);
            }
        } catch (error) {
            var errorMsg = 'AI分析失败：' + error.message;
            if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                errorMsg += '\n\n❌ 无法连接到后端服务\n\n解决方法：\n1. 确保后端已启动：./start.sh\n2. 检查端口8002是否被占用';
            } else {
                errorMsg += '\n\n请确保：\n1. 后端服务已启动\n2. 已配置ARK_API_KEY环境变量\n\n配置方法见页面顶部“配置指南”链接。';
            }
            showToast(errorMsg, 'error');
        } finally {
            document.getElementById('loading').classList.remove('show');
            document.getElementById('loading').querySelector('p').textContent = '正在计算中...';
        }
    }

    function initializeBaziPanel() {
        var form = document.getElementById('baziForm');
        if (!form) {
            return;
        }

        initializeAIStatusBanner();

        form.addEventListener('submit', async function (e) {
            e.preventDefault();
            var data = {
                year: parseInt(document.getElementById('year').value, 10),
                month: parseInt(document.getElementById('month').value, 10),
                day: parseInt(document.getElementById('day').value, 10),
                hour: parseInt(document.getElementById('hour').value, 10),
                minute: parseInt(document.getElementById('minute').value, 10),
                gender: document.getElementById('gender').value
            };

            document.getElementById('loading').classList.add('show');
            document.getElementById('result').classList.remove('show');

            try {
                var result = await window.apiClient.postJson('/api/bazi', data);
                displayResult(result.data);
            } catch (error) {
                var errorMsg = '计算失败：' + error.message;
                if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                    errorMsg += '\n\n❌ 无法连接到后端服务\n\n解决方法：\n1. 确保后端已启动：./start.sh\n2. 检查端口8002是否被占用\n3. 查看日志：tail -f /tmp/xuanxue-backend.log';
                } else if (error.message.includes('API请求失败')) {
                    errorMsg += '\n\n❌ 服务器返回错误\n\n请查看后端日志了解详情：\ntail -f /tmp/xuanxue-backend.log';
                }
                showToast(errorMsg, 'error');
            } finally {
                document.getElementById('loading').classList.remove('show');
            }
        });

        window.calculateWithAI = calculateWithAI;
    }

    window.indexBaziPanel = {
        initialize: initializeBaziPanel,
        calculateWithAI: calculateWithAI
    };
})();
