# generate_final_report.py - Master Academic Report Generator for OATrack-VLM

import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls
import win32com.client
import fitz

import report_data as rd
import report_sections as rs

print("Starting generation of OATrack-VLM Academic Report...")

doc = docx.Document()

# Configure default style to Times New Roman
style_normal = doc.styles['Normal']
style_normal.font.name = 'Times New Roman'
style_normal.font.size = Pt(12)
style_normal.font.color.rgb = RGBColor(0, 0, 0)
style_normal.paragraph_format.line_spacing = 1.5
style_normal.paragraph_format.space_after = Pt(6)
style_normal.paragraph_format.space_before = Pt(0)
style_normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# Section 1 Setup: Front Matter
sec1 = doc.sections[0]
sec1.page_width = Inches(8.27)
sec1.page_height = Inches(11.69)
sec1.top_margin = Inches(1.0)
sec1.bottom_margin = Inches(1.0)
sec1.left_margin = Inches(1.0)
sec1.right_margin = Inches(1.0)
sec1.different_first_page_header_footer = True

# Helper: Add Dynamic Page Number
def add_page_number_field(p):
    run = p.add_run()
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)
    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = "PAGE"
    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'separate')
    fldChar3 = OxmlElement('w:fldChar')
    fldChar3.set(qn('w:fldCharType'), 'end')
    r = run._r
    r.append(fldChar1)
    r.append(instrText)
    r.append(fldChar2)
    r.append(fldChar3)

# Configure Sec1 Footer (Roman numerals)
foot1 = sec1.footer.paragraphs[0]
foot1.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_page_number_field(foot1)
sectPr1 = sec1._sectPr
pgNumType1 = OxmlElement('w:pgNumType')
pgNumType1.set(qn('w:fmt'), 'upperRoman')
pgNumType1.set(qn('w:start'), '1')
sectPr1.append(pgNumType1)

# Helper: Style Table with Clean Academic Borders
def style_table(table, col_widths=None):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        '<w:top w:val="single" w:sz="6" w:space="0" w:color="000000"/>'
        '<w:left w:val="single" w:sz="6" w:space="0" w:color="000000"/>'
        '<w:bottom w:val="single" w:sz="6" w:space="0" w:color="000000"/>'
        '<w:right w:val="single" w:sz="6" w:space="0" w:color="000000"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>'
        '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="CCCCCC"/>'
        '</w:tblBorders>'
    )
    tblPr.append(borders)
    
    for row_idx, row in enumerate(table.rows):
        # Repeat header on new page
        if row_idx == 0:
            trPr = row._tr.get_or_add_trPr()
            trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
            trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
        else:
            trPr = row._tr.get_or_add_trPr()
            trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
            
        for col_idx, cell in enumerate(row.cells):
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            tcPr = cell._tc.get_or_add_tcPr()
            # Margins
            tcMar = parse_xml(
                f'<w:tcMar {nsdecls("w")}>'
                '<w:top w:w="80" w:type="dxa"/>'
                '<w:bottom w:w="80" w:type="dxa"/>'
                '<w:left w:w="120" w:type="dxa"/>'
                '<w:right w:w="120" w:type="dxa"/>'
                '</w:tcMar>'
            )
            tcPr.append(tcMar)
            if row_idx == 0:
                shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F2F2F2"/>')
                tcPr.append(shd)
            if col_widths and col_idx < len(col_widths):
                cell.width = col_widths[col_idx]

# Helper Functions for Typography
def p_chap_heading(num_str, title_str):
    p1 = doc.add_paragraph()
    p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p1.paragraph_format.space_before = Pt(0)
    p1.paragraph_format.space_after = Pt(4)
    p1.paragraph_format.line_spacing = 1.0
    r1 = p1.add_run(f"CHAPTER {num_str}")
    r1.font.name = 'Times New Roman'
    r1.font.size = Pt(14)
    r1.font.bold = True
    
    p2 = doc.add_paragraph()
    p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p2.paragraph_format.space_before = Pt(0)
    p2.paragraph_format.space_after = Pt(18)
    p2.paragraph_format.line_spacing = 1.0
    r2 = p2.add_run(title_str)
    r2.font.name = 'Times New Roman'
    r2.font.size = Pt(14)
    r2.font.bold = True

def p_sec_heading(title_str):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run(title_str)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(13)
    r.font.bold = True

def p_subsec_heading(title_str):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run(title_str)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(12)
    r.font.bold = True

def p_body(text_str):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.space_before = Pt(0)
    r = p.add_run(text_str)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(12)
    return p

def add_figure(img_path, caption_str, width_in=5.6):
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(10)
    p_img.paragraph_format.space_after = Pt(4)
    p_img.paragraph_format.line_spacing = 1.0
    p_img.add_run().add_picture(img_path, width=Inches(width_in))
    
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(2)
    p_cap.paragraph_format.space_after = Pt(12)
    p_cap.paragraph_format.line_spacing = 1.0
    r = p_cap.add_run(caption_str)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(11)
    r.font.bold = True

def add_table_data(t_info, col_widths=None):
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(10)
    p_cap.paragraph_format.space_after = Pt(4)
    p_cap.paragraph_format.line_spacing = 1.0
    r = p_cap.add_run(f"{t_info['num']} {t_info['title']}")
    r.font.name = 'Times New Roman'
    r.font.size = Pt(12)
    r.font.bold = True
    
    table = doc.add_table(rows=len(t_info['rows']) + 1, cols=len(t_info['headers']))
    style_table(table, col_widths)
    
    # Headers
    for c_idx, h in enumerate(t_info['headers']):
        p = table.cell(0, c_idx).paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(h)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(10.5)
        r.font.bold = True
        
    # Data rows
    for r_idx, row in enumerate(t_info['rows']):
        for c_idx, val in enumerate(row):
            p = table.cell(r_idx + 1, c_idx).paragraphs[0]
            # Center if number/status, else left
            if any(char.isdigit() for char in val) or val in ["Passed", "Failed", "—", "--"]:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(val)
            r.font.name = 'Times New Roman'
            r.font.size = Pt(10)
            if val == "Passed":
                r.font.bold = True

print("Configured layout styles.")
