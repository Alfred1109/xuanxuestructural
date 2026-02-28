(function () {
    function renderMarkdownSimple(text, headingColor) {
        if (!text) return '';

        var color = headingColor || '#667eea';

        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/^### (.*$)/gim, '<h4 style="margin-top: 15px; margin-bottom: 10px; color: ' + color + ';">$1</h4>')
            .replace(/^## (.*$)/gim, '<h3 style="margin-top: 15px; margin-bottom: 10px; color: ' + color + ';">$1</h3>')
            .replace(/^# (.*$)/gim, '<h2 style="margin-top: 15px; margin-bottom: 10px; color: ' + color + ';">$1</h2>')
            .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.+?)\*/g, '<em>$1</em>')
            .replace(/^\- (.+)$/gim, '<li style="margin-left: 20px;">$1</li>')
            .replace(/^\* (.+)$/gim, '<li style="margin-left: 20px;">$1</li>')
            .replace(/\n\n/g, '<br><br>')
            .replace(/\n/g, '<br>');
    }

    window.renderMarkdownSimple = renderMarkdownSimple;
})();
