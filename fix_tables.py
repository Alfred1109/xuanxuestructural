import os
import re

def fix_markdown_tables(content):
    """在Markdown表格前添加空行"""
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # 检查当前行是否是表格行（以|开头或包含|）
        is_table_line = line.strip().startswith('|') and '|' in line
        
        # 检查上一行是否为空
        prev_line_empty = i == 0 or fixed_lines[-1].strip() == ''
        
        # 如果是表格行且上一行不为空，添加空行
        if is_table_line and not prev_line_empty and i > 0:
            fixed_lines.append('')
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

# 处理docs目录下的所有md文件
docs_dir = r'c:\Users\alfred\Desktop\玄学体系\docs'

for filename in os.listdir(docs_dir):
    if filename.endswith('.md'):
        filepath = os.path.join(docs_dir, filename)
        print(f'处理文件: {filename}')
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        fixed_content = fix_markdown_tables(content)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f'完成: {filename}')

print('\n所有文件处理完成！')
