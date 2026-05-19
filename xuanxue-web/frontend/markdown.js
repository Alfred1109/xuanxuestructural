(function () {
    function escapeHtml(value) {
        return String(value || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');
    }

    function createFallbackRenderer() {
        function applyInlineMarkdown(text) {
            return String(text || '')
                .replace(/`([^`]+)`/g, '<code>$1</code>')
                .replace(/\*\*([^*]+?)\*\*/g, '<strong>$1</strong>')
                .replace(/__([^_]+?)__/g, '<strong>$1</strong>')
                .replace(/(^|[\s(])\*([^*\n]+?)\*(?=[\s).,!?;:]|$)/g, '$1<em>$2</em>')
                .replace(/(^|[\s(])_([^_\n]+?)_(?=[\s).,!?;:]|$)/g, '$1<em>$2</em>');
        }

        return function renderFallback(text, headingColor) {
            if (!text) return '';

            var color = headingColor || '#667eea';
            var lines = escapeHtml(text).replace(/\r\n/g, '\n').split('\n');
            var html = [];
            var paragraphLines = [];
            var listItems = [];
            var quoteLines = [];
            var inCodeBlock = false;
            var codeLines = [];

            function flushParagraph() {
                if (!paragraphLines.length) {
                    return;
                }
                html.push('<p>' + applyInlineMarkdown(paragraphLines.join('<br>')) + '</p>');
                paragraphLines = [];
            }

            function flushList() {
                if (!listItems.length) {
                    return;
                }
                html.push('<ul style="margin: 10px 0 14px 20px; padding-left: 18px;">' + listItems.join('') + '</ul>');
                listItems = [];
            }

            function flushQuote() {
                if (!quoteLines.length) {
                    return;
                }
                html.push(
                    '<blockquote style="margin: 12px 0; padding: 10px 14px; border-left: 4px solid ' + color + '; background: rgba(23, 58, 52, 0.06); color: #35574f; border-radius: 0 10px 10px 0;">'
                    + applyInlineMarkdown(quoteLines.join('<br>'))
                    + '</blockquote>'
                );
                quoteLines = [];
            }

            function flushCodeBlock() {
                if (!inCodeBlock) {
                    return;
                }
                html.push(
                    '<pre style="margin: 12px 0; padding: 12px 14px; background: rgba(23, 58, 52, 0.06); border-radius: 10px; overflow-x: auto;"><code>'
                    + codeLines.join('\n')
                    + '</code></pre>'
                );
                inCodeBlock = false;
                codeLines = [];
            }

            lines.forEach(function (line) {
                var trimmed = line.trim();
                var headingMatch;
                var listMatch;

                if (/^```/.test(trimmed)) {
                    flushParagraph();
                    flushList();
                    flushQuote();
                    if (inCodeBlock) {
                        flushCodeBlock();
                    } else {
                        inCodeBlock = true;
                        codeLines = [];
                    }
                    return;
                }

                if (inCodeBlock) {
                    codeLines.push(line);
                    return;
                }

                if (!trimmed) {
                    flushParagraph();
                    flushList();
                    flushQuote();
                    return;
                }

                headingMatch = trimmed.match(/^(#{1,6})\s+(.*)$/);
                if (headingMatch) {
                    flushParagraph();
                    flushList();
                    flushQuote();
                    html.push(
                        '<h' + Math.min(headingMatch[1].length + 1, 6)
                        + ' style="margin-top: 15px; margin-bottom: 10px; color: ' + color + ';">'
                        + applyInlineMarkdown(headingMatch[2])
                        + '</h' + Math.min(headingMatch[1].length + 1, 6) + '>'
                    );
                    return;
                }

                listMatch = trimmed.match(/^([-*]|\d+\.)\s+(.*)$/);
                if (listMatch) {
                    flushParagraph();
                    flushQuote();
                    listItems.push('<li style="margin: 4px 0;">' + applyInlineMarkdown(listMatch[2]) + '</li>');
                    return;
                }

                if (/^&gt;\s?/.test(trimmed)) {
                    flushParagraph();
                    flushList();
                    quoteLines.push(trimmed.replace(/^&gt;\s?/, ''));
                    return;
                }

                flushList();
                flushQuote();
                paragraphLines.push(trimmed);
            });

            flushParagraph();
            flushList();
            flushQuote();
            flushCodeBlock();

            return html.join('');
        };
    }

    function createMarkdownItRenderer() {
        if (typeof window.markdownit !== 'function') {
            return null;
        }

        var renderer = window.markdownit({
            html: false,
            linkify: true,
            typographer: false,
            breaks: true
        });

        renderer.validateLink = function (url) {
            var normalized = String(url || '').trim().toLowerCase();
            if (!normalized) {
                return false;
            }
            if (
                normalized.indexOf('javascript:') === 0
                || normalized.indexOf('vbscript:') === 0
                || normalized.indexOf('data:') === 0
                || normalized.indexOf('file:') === 0
            ) {
                return false;
            }
            return true;
        };

        renderer.renderer.rules.link_open = function (tokens, idx, options, env, self) {
            var token = tokens[idx];
            var href = token.attrGet('href') || '';
            if (/^(https?:)?\/\//i.test(href) || /^mailto:/i.test(href)) {
                token.attrSet('target', '_blank');
                token.attrSet('rel', 'noopener noreferrer');
            }
            return self.renderToken(tokens, idx, options);
        };

        return function renderMarkdown(text, headingColor) {
            var color = headingColor || '#667eea';
            var source = String(text || '');
            var html = renderer.render(source);
            return [
                '<div class="markdown-body" style="--md-heading-color: ' + escapeHtml(color) + ';">',
                html,
                '</div>'
            ].join('');
        };
    }

    var fallbackRenderer = createFallbackRenderer();
    var fullRenderer = createMarkdownItRenderer();

    function renderMarkdownSimple(text, headingColor) {
        if (fullRenderer) {
            return fullRenderer(text, headingColor);
        }
        return fallbackRenderer(text, headingColor);
    }

    window.escapeHtml = window.escapeHtml || escapeHtml;
    window.renderMarkdownSimple = renderMarkdownSimple;
})();
