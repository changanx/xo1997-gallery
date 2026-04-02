"""
将Excel数据导入到SQLite数据库
"""
import sqlite3
import pandas as pd
from pathlib import Path


def excel_to_sqlite(excel_file='data_template.xlsx', db_file='employee.db'):
    """
    将Excel文件中的数据导入到SQLite数据库

    Args:
        excel_file: Excel文件路径
        db_file: SQLite数据库文件路径
    """
    project_dir = Path(__file__).parent
    excel_path = project_dir / excel_file
    db_path = project_dir / db_file

    if not excel_path.exists():
        print(f'错误: Excel文件不存在 - {excel_path}')
        return

    # 读取Excel文件
    print(f'正在读取Excel文件: {excel_path}')
    xls = pd.ExcelFile(excel_path)

    print(f'包含的Sheet: {xls.sheet_names}')

    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 导入department表（sheet1）
        if 'department' in xls.sheet_names:
            dept_df = pd.read_excel(xls, sheet_name='department')
            print(f'\n导入department表，共{len(dept_df)}条记录')

            # 清空现有数据
            cursor.execute('DELETE FROM department')

            # 插入数据
            for _, row in dept_df.iterrows():
                cursor.execute('''
                    INSERT INTO department (id, parent_id, name, level)
                    VALUES (?, ?, ?, ?)
                ''', (
                    int(row['id']) if pd.notna(row['id']) else None,
                    int(row['parent_id']) if pd.notna(row['parent_id']) else None,
                    row['name'] if pd.notna(row['name']) else None,
                    int(row['level']) if pd.notna(row['level']) else None
                ))

            print('department表导入完成')

        # 导入employee表（sheet2）
        if 'employee' in xls.sheet_names:
            emp_df = pd.read_excel(xls, sheet_name='employee')
            print(f'\n导入employee表，共{len(emp_df)}条记录')

            # 清空现有数据
            cursor.execute('DELETE FROM employee')

            # 插入数据
            for _, row in emp_df.iterrows():
                cursor.execute('''
                    INSERT INTO employee (id, name, employee_number, department_level1,
                                        department_level2, department_level3,
                                        department_level4, department_level5, rank, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    int(row['id']) if pd.notna(row['id']) else None,
                    row['name'] if pd.notna(row['name']) else None,
                    row['employee_number'] if pd.notna(row['employee_number']) else None,
                    row['department_level1'] if pd.notna(row['department_level1']) else None,
                    row['department_level2'] if pd.notna(row['department_level2']) else None,
                    row['department_level3'] if pd.notna(row['department_level3']) else None,
                    row['department_level4'] if pd.notna(row['department_level4']) else None,
                    row['department_level5'] if pd.notna(row['department_level5']) else None,
                    row['rank'] if pd.notna(row['rank']) else None,
                    row['category'] if pd.notna(row['category']) else None
                ))

            print('employee表导入完成')

        conn.commit()
        print(f'\n数据导入成功，数据库文件: {db_path}')

    except Exception as e:
        conn.rollback()
        print(f'导入失败: {e}')
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    excel_to_sqlite()
