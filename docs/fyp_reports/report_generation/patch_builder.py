import re

with open('build_complete_document.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace p_parts_3_1 handling
old_ch3_start = """p_sec_heading(rs.CH3_DATA_METHOD['s3_1'][0])
p_parts_3_1 = rs.CH3_DATA_METHOD['s3_1'][1].split('\\\\n\\\\n')
p_body(p_parts_3_1[0])
p_body(p_parts_3_1[1])
add_table_data(rs.TABLES_DATA['t3_1'], [Inches(1.5), Inches(1.1), Inches(1.1), Inches(1.3), Inches(1.3)])
p_sec_heading(rs.CH3_DATA_METHOD['s3_2'][0])
p_body(rs.CH3_DATA_METHOD['s3_2'][1])"""

new_ch3_start = """p_sec_heading(rs.CH3_DATA_METHOD['s3_1'][0])
for p in split_p(rs.CH3_DATA_METHOD['s3_1'][1]):
    p_body(p)
add_table_data(rs.TABLES_DATA['t3_1'], [Inches(1.5), Inches(1.1), Inches(1.1), Inches(1.3), Inches(1.3)])
p_sec_heading(rs.CH3_DATA_METHOD['s3_2'][0])
for p in split_p(rs.CH3_DATA_METHOD['s3_2'][1]):
    p_body(p)"""

# Add split_p helper
helper_def = """def split_p(text):
    if not text:
        return []
    text = text.replace('\\\\n', '\\n')
    return [p.strip() for p in text.split('\\n') if p.strip()]
"""

code = code.replace("def p_body(text_str):", helper_def + "\ndef p_body(text_str):")

# Universal replacements for the rest of split calls
code = code.replace("rs.CH2_LIT['s2_2'][1].split('\\\\n\\\\n')", "split_p(rs.CH2_LIT['s2_2'][1])")
code = code.replace("rs.CH2_LIT['s2_6'][1].split('\\\\n')", "split_p(rs.CH2_LIT['s2_6'][1])")
code = code.replace("rs.CH2_LIT['s2_7'][1].split('\\\\n')", "split_p(rs.CH2_LIT['s2_7'][1])")

code = code.replace(old_ch3_start, new_ch3_start)

code = code.replace("rs.CH3_DATA_METHOD['s3_6'][1].split('\\\\n\\\\n')", "split_p(rs.CH3_DATA_METHOD['s3_6'][1])")
code = code.replace("rs.CH3_DATA_METHOD['s3_7'][1].split('\\\\n\\\\n')", "split_p(rs.CH3_DATA_METHOD['s3_7'][1])")
code = code.replace("rs.CH3_DATA_METHOD['s3_8'][1].split('\\\\n\\\\n')", "split_p(rs.CH3_DATA_METHOD['s3_8'][1])")

code = code.replace("rs.CH4_SYS_DESIGN['s4_1'][1].split('\\\\n\\\\n')", "split_p(rs.CH4_SYS_DESIGN['s4_1'][1])")
code = code.replace("rs.CH4_SYS_DESIGN['s4_2'][1].split('\\\\n\\\\n')", "split_p(rs.CH4_SYS_DESIGN['s4_2'][1])")
code = code.replace("rs.CH4_SYS_DESIGN['s4_3'][1].split('\\\\n\\\\n')", "split_p(rs.CH4_SYS_DESIGN['s4_3'][1])")
code = code.replace("rs.CH4_SYS_DESIGN['s4_4'][1].split('\\\\n\\\\n')", "split_p(rs.CH4_SYS_DESIGN['s4_4'][1])")

code = code.replace("rs.CH5_METHODOLOGY['s5_2'][1].split('\\\\n')", "split_p(rs.CH5_METHODOLOGY['s5_2'][1])")
code = code.replace("rs.CH5_METHODOLOGY['s5_3'][1].split('\\\\n')", "split_p(rs.CH5_METHODOLOGY['s5_3'][1])")
code = code.replace("rs.CH5_METHODOLOGY['s5_4'][1].split('\\\\n')", "split_p(rs.CH5_METHODOLOGY['s5_4'][1])")
code = code.replace("rs.CH5_METHODOLOGY['s5_5'][1].split('\\\\n')", "split_p(rs.CH5_METHODOLOGY['s5_5'][1])")

code = code.replace("rs.CH6_RESULTS['s6_1'][1].split('\\\\n')", "split_p(rs.CH6_RESULTS['s6_1'][1])")
code = code.replace("rs.CH6_RESULTS['s6_2'][1].split('\\\\n')", "split_p(rs.CH6_RESULTS['s6_2'][1])")

old_ch6_p3 = """p_sec_heading(rs.CH6_RESULTS['s6_3'][0])
p_parts_6_3 = rs.CH6_RESULTS['s6_3'][1].split('\\\\n\\\\n')
p_body(p_parts_6_3[0])
add_table_data(rs.TABLES_DATA['t6_1'], [Inches(1.8), Inches(0.8), Inches(0.8), Inches(0.8), Inches(0.8), Inches(0.8), Inches(0.8), Inches(0.8)])
p_body(p_parts_6_3[1])"""

new_ch6_p3 = """p_sec_heading(rs.CH6_RESULTS['s6_3'][0])
p_parts_6_3 = split_p(rs.CH6_RESULTS['s6_3'][1])
p_body(p_parts_6_3[0])
add_table_data(rs.TABLES_DATA['t6_1'], [Inches(1.8), Inches(0.8), Inches(0.8), Inches(0.8), Inches(0.8), Inches(0.8), Inches(0.8), Inches(0.8)])
if len(p_parts_6_3) > 1:
    p_body(p_parts_6_3[1])"""

code = code.replace(old_ch6_p3, new_ch6_p3)

code = code.replace("p_parts_6_4 = rs.CH6_RESULTS['s6_4'][1].split('\\\\n')", "p_parts_6_4 = split_p(rs.CH6_RESULTS['s6_4'][1])")
code = code.replace("rs.CH6_RESULTS['s6_5'][1].split('\\\\n\\\\n')", "split_p(rs.CH6_RESULTS['s6_5'][1])")
code = code.replace("p_parts_6_7 = rs.CH6_RESULTS['s6_7'][1].split('\\\\n')", "p_parts_6_7 = split_p(rs.CH6_RESULTS['s6_7'][1])")

code = code.replace("rs.CH7_TESTING['s7_2'][1].split('\\\\n')", "split_p(rs.CH7_TESTING['s7_2'][1])")
code = code.replace("rs.CH7_TESTING['s7_3'][1].split('\\\\n')", "split_p(rs.CH7_TESTING['s7_3'][1])")

code = code.replace("rs.CH8_CONCLUSION['s8_1'][1].split('\\\\n\\\\n')", "split_p(rs.CH8_CONCLUSION['s8_1'][1])")
code = code.replace("rs.CH8_CONCLUSION['s8_2'][1].split('\\\\n')", "split_p(rs.CH8_CONCLUSION['s8_2'][1])")

with open('build_complete_document.py', 'w', encoding='utf-8') as f:
    f.write(code)

print('Patched build_complete_document.py successfully!')
