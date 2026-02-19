import os
import re

def fix_markdown_tables(content):
    """彻底修复Markdown表格：移除表格内所有空行，确保表格行连续"""
    lines = content.split('\n')
    result = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # 检查是否是表格行的开始
        if stripped.startswith('|') and '|' in stripped:
            # 找到表格的开始，确保前面有空行
            if result and result[-1].strip() != '':
                result.append('')
            
            # 收集所有连续的表格行（跳过中间的空行）
            table_lines = []
            while i < len(lines):
                current = lines[i].strip()
                if current.startswith('|') and '|' in current:
                    table_lines.append(lines[i])
                    i += 1
                elif current == '' and i + 1 < len(lines):
                    # 检查下一行是否还是表格行
                    next_line = lines[i + 1].strip()
                    if next_line.startswith('|') and '|' in next_line:
                        # 跳过空行，继续收集表格
                        i += 1
                        continue
                    else:
                        # 表格结束
                        break
                else:
                    # 表格结束
                    break
            
            # 输出表格（所有行连续）
            result.extend(table_lines)
            
            # 表格后添加空行（如果下一行不是空行）
            if i < len(lines) and lines[i].strip() != '':
                result.append('')
        else:
            # 非表格行直接添加
            result.append(line)
            i += 1
    
    return '\n'.join(result)

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
