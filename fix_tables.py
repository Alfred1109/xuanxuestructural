import os
import re

def fix_markdown_tables(content):
    """在Markdown表格前添加空行，但保持表格行连续"""
    lines = content.split('\n')
    fixed_lines = []
    in_table = False
    
    for i, line in enumerate(lines):
        # 检查当前行是否是表格行
        is_table_line = line.strip().startswith('|') and '|' in line
        
        if is_table_line:
            if not in_table:
                # 表格开始：检查上一行是否为空
                if fixed_lines and fixed_lines[-1].strip() != '':
                    fixed_lines.append('')  # 在表格前添加空行
                in_table = True
            # 表格行直接添加，不加额外空行
            fixed_lines.append(line)
        else:
            if in_table:
                # 表格结束：在表格后添加空行（如果下一行不是空行）
                if line.strip() != '':
                    fixed_lines.append('')
                in_table = False
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
