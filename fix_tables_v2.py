import os
import re

def fix_markdown_tables(content):
    """修复Markdown表格：移除表格内的空行，确保表格前后有空行"""
    lines = content.split('\n')
    fixed_lines = []
    table_buffer = []
    in_table = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # 检查是否是表格行
        is_table_line = stripped.startswith('|') and '|' in stripped
        
        if is_table_line:
            # 收集表格行
            table_buffer.append(line)
            in_table = True
        else:
            # 非表格行
            if in_table:
                # 表格结束，输出收集的表格
                # 确保表格前有空行
                if fixed_lines and fixed_lines[-1].strip() != '':
                    fixed_lines.append('')
                
                # 输出表格（所有行连续，无空行）
                fixed_lines.extend(table_buffer)
                
                # 确保表格后有空行（如果当前行不是空行）
                if stripped != '':
                    fixed_lines.append('')
                
                # 重置
                table_buffer = []
                in_table = False
            
            # 添加当前非表格行
            fixed_lines.append(line)
    
    # 处理文件末尾的表格
    if table_buffer:
        if fixed_lines and fixed_lines[-1].strip() != '':
            fixed_lines.append('')
        fixed_lines.extend(table_buffer)
    
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
