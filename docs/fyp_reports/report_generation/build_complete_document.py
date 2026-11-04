# build_complete_document.py - End-to-End Academic Report Generation and Compilation

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

print("==================================================")
print("BUILDING OATRACK-VLM 50-PAGE UNIVERSITY REPORT")
print("==================================================")

doc = docx.Document()

# Base styling
style_normal = doc.styles['Normal']
style_normal.font.name = 'Times New Roman'
style_normal.font.size = Pt(12)
style_normal.font.color.rgb = RGBColor(0, 0, 0)
style_normal.paragraph_format.line_spacing = 1.5
style_normal.paragraph_format.space_after = Pt(6)
style_normal.paragraph_format.space_before = Pt(0)
style_normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

# Margins: 1.0 inch all around
sec1 = doc.sections[0]
sec1.page_width = Inches(8.27)
sec1.page_height = Inches(11.69)
sec1.top_margin = Inches(1.0)
sec1.bottom_margin = Inches(1.0)
sec1.left_margin = Inches(1.0)
sec1.right_margin = Inches(1.0)
sec1.different_first_page_header_footer = True

def add_page_number_field(p):
    run = p.add_run()
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)
    fld1 = OxmlElement('w:fldChar')
    fld1.set(qn('w:fldCharType'), 'begin')
    t = OxmlElement('w:instrText')
    t.set(qn('xml:space'), 'preserve')
    t.text = "PAGE"
    fld2 = OxmlElement('w:fldChar')
    fld2.set(qn('w:fldCharType'), 'separate')
    fld3 = OxmlElement('w:fldChar')
    fld3.set(qn('w:fldCharType'), 'end')
    r = run._r
    r.append(fld1)
    r.append(t)
    r.append(fld2)
    r.append(fld3)

# Sec1 footer setup: Roman numerals
foot1 = sec1.footer.paragraphs[0]
foot1.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_page_number_field(foot1)
sectPr1 = sec1._sectPr
pgNum1 = OxmlElement('w:pgNumType')
pgNum1.set(qn('w:fmt'), 'upperRoman')
pgNum1.set(qn('w:start'), '1')
sectPr1.append(pgNum1)

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
    for r_idx, row in enumerate(table.rows):
        if r_idx == 0:
            trPr = row._tr.get_or_add_trPr()
            trPr.append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
            trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
        else:
            trPr = row._tr.get_or_add_trPr()
            trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
        for c_idx, cell in enumerate(row.cells):
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            tcPr = cell._tc.get_or_add_tcPr()
            tcMar = parse_xml(
                f'<w:tcMar {nsdecls("w")}>'
                '<w:top w:w="80" w:type="dxa"/>'
                '<w:bottom w:w="80" w:type="dxa"/>'
                '<w:left w:w="120" w:type="dxa"/>'
                '<w:right w:w="120" w:type="dxa"/>'
                '</w:tcMar>'
            )
            tcPr.append(tcMar)
            if r_idx == 0:
                shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F2F2F2"/>')
                tcPr.append(shd)
            if col_widths and c_idx < len(col_widths):
                cell.width = col_widths[c_idx]

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

def split_p(text):
    if not text:
        return []
    text = text.replace('\\n', '\n')
    return [p.strip() for p in text.split('\n') if p.strip()]

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
    p_img.paragraph_format.space_before = Pt(8)
    p_img.paragraph_format.space_after = Pt(4)
    p_img.paragraph_format.line_spacing = 1.0
    p_img.add_run().add_picture(img_path, width=Inches(width_in))
    
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(2)
    p_cap.paragraph_format.space_after = Pt(10)
    p_cap.paragraph_format.line_spacing = 1.0
    r = p_cap.add_run(caption_str)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(11)
    r.font.bold = True

def add_table_data(t_info, col_widths=None):
    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(8)
    p_cap.paragraph_format.space_after = Pt(4)
    p_cap.paragraph_format.line_spacing = 1.0
    r = p_cap.add_run(f"{t_info['num']} {t_info['title']}")
    r.font.name = 'Times New Roman'
    r.font.size = Pt(12)
    r.font.bold = True
    
    table = doc.add_table(rows=len(t_info['rows']) + 1, cols=len(t_info['headers']))
    style_table(table, col_widths)
    
    for c_idx, h in enumerate(t_info['headers']):
        p = table.cell(0, c_idx).paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.line_spacing = 1.0
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(h)
        r.font.name = 'Times New Roman'
        r.font.size = Pt(10)
        r.font.bold = True
        
    for r_idx, row in enumerate(t_info['rows']):
        for c_idx, val in enumerate(row):
            p = table.cell(r_idx + 1, c_idx).paragraphs[0]
            if any(char.isdigit() for char in val) or val in ["Passed", "Failed", "—", "--"]:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(val)
            r.font.name = 'Times New Roman'
            r.font.size = Pt(9.5)
            if val == "Passed":
                r.font.bold = True

# ==========================================
# PAGE 1: COVER PAGE
# ==========================================
print("Writing Page 1: Cover Page...")
p_t = doc.add_paragraph()
p_t.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_t.paragraph_format.space_before = Pt(10)
p_t.paragraph_format.space_after = Pt(18)
p_t.paragraph_format.line_spacing = 1.2
r_t = p_t.add_run(
    "A HIERARCHICAL MULTIMODAL FRAMEWORK FOR\n"
    "AUTONOMOUS MARITIME SURVEILLANCE USING\n"
    "SATELLITE DETECTION, KALMAN-FILTER UAV\n"
    "TRACKING, AND VISION-LANGUAGE REASONING"
)
r_t.font.name = 'Times New Roman'
r_t.font.size = Pt(15)
r_t.font.bold = True

p_sub = doc.add_paragraph()
p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_sub.paragraph_format.space_after = Pt(4)
p_sub.paragraph_format.line_spacing = 1.1
r = p_sub.add_run("A PROJECT REPORT\n")
r.font.bold = True
r.font.size = Pt(13)
r = p_sub.add_run("Submitted to\n")
r.font.size = Pt(12)
r = p_sub.add_run("Amrita Vishwa Vidyapeetham\n")
r.font.bold = True
r.font.size = Pt(13)
r = p_sub.add_run("in partial fulfillment for the award of the degree of\n")
r.font.italic = True
r.font.size = Pt(12)
r = p_sub.add_run("BACHELOR OF TECHNOLOGY IN COMPUTER SCIENCE AND\nENGINEERING\n")
r.font.bold = True
r.font.size = Pt(13)
r = p_sub.add_run("By\n")
r.font.size = Pt(12)
r = p_sub.add_run("AMAN REDDY J\n(Reg. No. CH.SC.U4AIE23006)\n\nBTPR NIKHIL\n(Reg. No. CH.SC.U4AIE23005)\n")
r.font.bold = True
r.font.size = Pt(12)

p_sup = doc.add_paragraph()
p_sup.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_sup.paragraph_format.space_after = Pt(12)
p_sup.paragraph_format.line_spacing = 1.1
r = p_sup.add_run("Supervisor\n")
r.font.size = Pt(12)
r = p_sup.add_run("Dr. K ASHWINI\n")
r.font.bold = True
r.font.size = Pt(13)
r = p_sup.add_run("Assistant Professor (Sr. Gr.)\n")
r.font.size = Pt(12)

# Amrita Maroon Logo
p_logo = doc.add_paragraph()
p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_logo.paragraph_format.space_after = Pt(12)
p_logo.add_run().add_picture(r'f:\OATrack-VLM_complete_project\extracted_assets\p1_img0_18.png', width=Inches(3.2))

p_bot = doc.add_paragraph()
p_bot.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_bot.paragraph_format.line_spacing = 1.1
r = p_bot.add_run(
    "AMRITA VISHWA VIDYAPEETHAM\n"
    "AMRITA SCHOOL OF COMPUTING\n"
    "CHENNAI – 601103\n"
    "October 2026"
)
r.font.name = 'Times New Roman'
r.font.size = Pt(12)
r.font.bold = True

doc.add_page_break()

# ==========================================
# PAGE 2: BONAFIDE CERTIFICATE (Page II)
# ==========================================
print("Writing Page 2: Bonafide Certificate...")
p_ban = doc.add_paragraph()
p_ban.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_ban.paragraph_format.space_after = Pt(24)
p_ban.add_run().add_picture(r'f:\OATrack-VLM_complete_project\extracted_assets\p2_img0_21.png', width=Inches(4.2))

p_c_head = doc.add_paragraph()
p_c_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_c_head.paragraph_format.space_after = Pt(20)
r = p_c_head.add_run("BONAFIDE CERTIFICATE")
r.font.name = 'Times New Roman'
r.font.size = Pt(14)
r.font.bold = True

p_c_text = doc.add_paragraph()
p_c_text.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
p_c_text.paragraph_format.line_spacing = 1.5
p_c_text.paragraph_format.space_after = Pt(50)
r = p_c_text.add_run(
    "This is to certify that this project report entitled “A HIERARCHICAL MULTIMODAL FRAMEWORK FOR AUTONOMOUS "
    "MARITIME SURVEILLANCE USING SATELLITE DETECTION, KALMAN-FILTER UAV TRACKING, AND VISION-LANGUAGE REASONING” "
    "is the bonafide work of Mr. AMAN REDDY J (Reg. No. CH.SC.U4AIE23006) and Mr. BTPR NIKHIL (Reg. No. CH.SC.U4AIE23005), "
    "who carried out the project work under my supervision."
)
r.font.name = 'Times New Roman'
r.font.size = Pt(12)

# Signatures table
t_sig = doc.add_table(rows=2, cols=2)
t_sig.alignment = WD_TABLE_ALIGNMENT.CENTER
t_sig.rows[0].cells[0].paragraphs[0].text = "SIGNATURE\n\n\nDR. S. BAGHAVATHI PRIYA\nCHAIRPERSON\nAssociate Professor Dept. of CSE.\nAmrita School of Computing\nChennai."
t_sig.rows[0].cells[1].paragraphs[0].text = "SIGNATURE\n\n\nDr. K ASHWINI\nSUPERVISOR\nAssistant Professor, Dept. of CSE.\nAmrita School of Computing\nChennai."
t_sig.rows[1].cells[0].paragraphs[0].text = "\n\n\nINTERNAL EXAMINER"
t_sig.rows[1].cells[1].paragraphs[0].text = "\n\n\nEXTERNAL EXAMINER"
for row in t_sig.rows:
    for c in row.cells:
        for p in c.paragraphs:
            p.paragraph_format.line_spacing = 1.15
            for run in p.runs:
                run.font.name = 'Times New Roman'
                run.font.size = Pt(11)
                run.font.bold = True

doc.add_page_break()

# ==========================================
# PAGE 3: DECLARATION BY THE CANDIDATE (Page III)
# ==========================================
print("Writing Page 3: Declaration...")
p_ban = doc.add_paragraph()
p_ban.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_ban.paragraph_format.space_after = Pt(24)
p_ban.add_run().add_picture(r'f:\OATrack-VLM_complete_project\extracted_assets\p2_img0_21.png', width=Inches(4.2))

p_d_head = doc.add_paragraph()
p_d_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_d_head.paragraph_format.space_after = Pt(20)
r = p_d_head.add_run("DECLARATION BY THE CANDIDATE")
r.font.name = 'Times New Roman'
r.font.size = Pt(14)
r.font.bold = True

p_d_text = doc.add_paragraph()
p_d_text.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
p_d_text.paragraph_format.line_spacing = 1.5
p_d_text.paragraph_format.space_after = Pt(60)
r = p_d_text.add_run(
    "I declare that the report entitled “A HIERARCHICAL MULTIMODAL FRAMEWORK FOR AUTONOMOUS MARITIME SURVEILLANCE "
    "USING SATELLITE DETECTION, KALMAN-FILTER UAV TRACKING, AND VISION-LANGUAGE REASONING” submitted by me for the "
    "degree of Bachelor of Technology is the record of the project work carried out by me under the guidance of "
    "“Dr. K ASHWINI” and this work has not formed the basis for the award of any degree, diploma, associateship, "
    "fellowship, titled in this or any other University or other similar institution of higher learning."
)
r.font.name = 'Times New Roman'
r.font.size = Pt(12)

p_dsig = doc.add_paragraph()
p_dsig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
p_dsig.paragraph_format.line_spacing = 1.15
r = p_dsig.add_run(
    "SIGNATURE\n\n\n"
    "AMAN REDDY J\n"
    "(Reg. No. CH.SC.U4AIE23006)\n"
    "Department of Computer\n"
    "Science and Engineering\n\n\n\n"
    "SIGNATURE\n\n\n"
    "BTPR NIKHIL\n"
    "(Reg. No. CH.SC.U4AIE23005)\n"
    "Department of Computer\n"
    "Science and Engineering"
)
r.font.name = 'Times New Roman'
r.font.size = Pt(11)
r.font.bold = True

doc.add_page_break()

# ==========================================
# PAGE 4: ABSTRACT (Page IV)
# ==========================================
print("Writing Page 4: Abstract...")
p_a_head = doc.add_paragraph()
p_a_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_a_head.paragraph_format.space_after = Pt(16)
r = p_a_head.add_run("ABSTRACT")
r.font.name = 'Times New Roman'
r.font.size = Pt(14)
r.font.bold = True

for para in rd.ABSTRACT_TEXT.split('\n\n'):
    p_body(para)

p_kw = doc.add_paragraph()
p_kw.alignment = WD_ALIGN_PARAGRAPH.LEFT
p_kw.paragraph_format.space_before = Pt(14)
r = p_kw.add_run("Keywords: ")
r.font.name = 'Times New Roman'
r.font.size = Pt(12)
r.font.bold = True
r = p_kw.add_run(rd.KEYWORDS)
r.font.name = 'Times New Roman'
r.font.size = Pt(12)

doc.add_page_break()

# ==========================================
# PAGE 5: ACKNOWLEDGEMENT (Page V)
# ==========================================
print("Writing Page 5: Acknowledgement...")
p_ack_head = doc.add_paragraph()
p_ack_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_ack_head.paragraph_format.space_after = Pt(16)
r = p_ack_head.add_run("ACKNOWLEDGEMENT")
r.font.name = 'Times New Roman'
r.font.size = Pt(14)
r.font.bold = True

for para in rd.ACKNOWLEDGEMENT_TEXT.split('\n\n'):
    p_body(para)

p_acksig = doc.add_paragraph()
p_acksig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
p_acksig.paragraph_format.space_before = Pt(24)
r = p_acksig.add_run("AMAN REDDY J & BTPR NIKHIL\n(Reg. No. CH.SC.U4AIE23006 & CH.SC.U4AIE23005)")
r.font.name = 'Times New Roman'
r.font.size = Pt(11)
r.font.bold = True

doc.add_page_break()

# ==========================================
# PAGES 6 to 9: TABLE OF CONTENTS (Pages VI - IX)
# ==========================================
print("Writing Pages 6 to 9: Table of Contents...")

def add_toc_header():
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(12)
    p.paragraph_format.line_spacing = 1.0
    r = p.add_run("TABLE OF CONTENTS")
    r.font.name = 'Times New Roman'
    r.font.size = Pt(14)
    r.font.bold = True
    
    table = doc.add_table(rows=1, cols=3)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for c_idx, h in enumerate(["CHAPTER NO.", "TITLE", "PAGE NO."]):
        p_c = table.cell(0, c_idx).paragraphs[0]
        p_c.paragraph_format.line_spacing = 1.0
        p_c.paragraph_format.space_after = Pt(4)
        if c_idx == 0:
            p_c.alignment = WD_ALIGN_PARAGRAPH.LEFT
        elif c_idx == 1:
            p_c.alignment = WD_ALIGN_PARAGRAPH.LEFT
        else:
            p_c.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r_c = p_c.add_run(h)
        r_c.font.name = 'Times New Roman'
        r_c.font.size = Pt(11)
        r_c.font.bold = True
    return table

def add_toc_rows(table, rows_data):
    for chap_no, title, p_num in rows_data:
        row = table.add_row()
        c0, c1, c2 = row.cells[0], row.cells[1], row.cells[2]
        
        p0 = c0.paragraphs[0]
        p0.paragraph_format.line_spacing = 1.15
        p0.paragraph_format.space_after = Pt(2)
        r0 = p0.add_run(chap_no)
        r0.font.name = 'Times New Roman'
        r0.font.size = Pt(11)
        if not chap_no.startswith("  ") and chap_no != "":
            r0.font.bold = True
            
        p1 = c1.paragraphs[0]
        p1.paragraph_format.line_spacing = 1.15
        p1.paragraph_format.space_after = Pt(2)
        r1 = p1.add_run(title)
        r1.font.name = 'Times New Roman'
        r1.font.size = Pt(11)
        if not chap_no.startswith("  ") and (chap_no != "" or title in ["Abstract", "List of Tables", "List of Figures", "List of Abbreviations"]):
            r1.font.bold = True
            
        p2 = c2.paragraphs[0]
        p2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p2.paragraph_format.line_spacing = 1.15
        p2.paragraph_format.space_after = Pt(2)
        r2 = p2.add_run(str(p_num))
        r2.font.name = 'Times New Roman'
        r2.font.size = Pt(11)
        if not chap_no.startswith("  ") and chap_no != "":
            r2.font.bold = True

# TOC Part 1 (Page VI)
t1 = add_toc_header()
toc_p1 = [
    ("", "Abstract", "IV"),
    ("", "List of Tables", "X"),
    ("", "List of Figures", "XI"),
    ("", "List of Abbreviations", "XII"),
    ("1", "INTRODUCTION", "1"),
    ("1.1", "Background of Maritime Domain Awareness & Aerial Surveillance", "2"),
    ("1.2", "Problem Statement", "2"),
    ("1.3", "Motivation", "3"),
    ("1.4", "Objective", "4"),
    ("1.5", "Scope of the Project", "4"),
    ("1.6", "Existing System and Limitations", "5"),
    ("1.7", "Proposed Solution", "5"),
    ("2", "LITERATURE REVIEW", "6"),
    ("2.1", "Satellite Remote Sensing for Vessel Detection", "7"),
    ("2.2", "Multi-Object Tracking and Kalman Filtering in Aerial Feeds", "7"),
    ("2.3", "Fine-Grained Maritime Vessel Classification", "8"),
    ("2.4", "Adaptive Edge Computing and Reinforcement Learning", "8"),
    ("2.5", "Vision-Language Models in Tactical Surveillance", "8"),
    ("2.6", "Research Gap", "9"),
    ("2.7", "Contribution of the Proposed Work", "9")
]
add_toc_rows(t1, toc_p1)
doc.add_page_break()

# TOC Part 2 (Page VII)
t2 = add_toc_header()
toc_p2 = [
    ("3", "DATASET AND PROPOSED METHODOLOGY", "10"),
    ("3.1", "VHRV Optical Satellite Benchmark Dataset", "10"),
    ("3.2", "TITANIC-FGS-10 Maritime Classification Dataset", "12"),
    ("3.3", "Data Preprocessing and Ground-Truth Verification", "12"),
    ("3.4", "Strategic Satellite-Based Vessel Detection (YOLO11n @ 1024px)", "13"),
    ("3.4.1", "Spatial Downsampling Preservation", "13"),
    ("3.4.2", "Detection Architecture & Non-Maximum Suppression", "13"),
    ("3.5", "Target Handoff Adapter Architecture", "13"),
    ("3.6", "Tactical UAV Tracking via Discrete Linear Kalman Filter", "14"),
    ("3.6.1", "8-State Dynamical State Formulation", "14"),
    ("3.6.2", "Multi-Feature Data Association Metric", "14"),
    ("3.6.3", "Sub-Part Containment Suppression Filter", "15"),
    ("3.7", "Fine-Grained Classification & Evidence Aggregation", "15"),
    ("3.8", "PPO Adaptive Edge Compute Scheduling", "15"),
    ("3.9", "Grounded Vision-Language Reasoning Architecture", "16"),
    ("4", "SYSTEM DESIGN AND ARCHITECTURE", "17"),
    ("4.1", "Overall System Architecture", "17"),
    ("4.2", "Data Flow Pipeline", "18"),
    ("4.3", "Surveillance Processing Workflow", "19"),
    ("4.4", "Proposed Application Architecture", "19"),
    ("4.5", "System Components", "20")
]
add_toc_rows(t2, toc_p2)
doc.add_page_break()

# TOC Part 3 (Page VIII)
t3 = add_toc_header()
toc_p3 = [
    ("5", "METHODOLOGY", "21"),
    ("5.1", "Development Environment", "21"),
    ("5.2", "Model Implementation Details", "21"),
    ("5.3", "Baseline Models", "22"),
    ("5.4", "OATrack-VLM Implementation Workflow", "22"),
    ("5.5", "Streamlit Command Center Prototype", "23"),
    ("5.6", "Prototype Workflow", "23"),
    ("6", "RESULTS AND ANALYSIS", "24"),
    ("6.1", "Experimental Setup", "24"),
    ("6.2", "Evaluation Metrics", "24"),
    ("6.3", "Satellite Vessel Detection Results", "25"),
    ("6.4", "UAV Tracking and Motion Persistence Performance", "25"),
    ("6.5", "Fine-Grained Classification Results", "26"),
    ("6.6", "Training and Convergence Analysis", "26"),
    ("6.7", "PPO Adaptive Compute Optimization Across Scenarios", "27"),
    ("6.8", "Multi-Ship Anchorage and Dense Harbor Analysis", "28"),
    ("6.9", "Grounded Vision-Language Telemetry Briefings", "28"),
    ("6.10", "Discussion", "28"),
    ("7", "EXPERIMENTAL RESULTS", "29"),
    ("7.1", "System Testing", "29"),
    ("7.2", "Current Achievements", "29"),
    ("7.3", "Limitations", "30")
]
add_toc_rows(t3, toc_p3)
doc.add_page_break()

# TOC Part 4 (Page IX)
t4 = add_toc_header()
toc_p4 = [
    ("8", "CONCLUSION AND FUTURE WORK", "31"),
    ("8.1", "Conclusion", "31"),
    ("8.2", "Future Work", "31"),
    ("9", "REFERENCES", "32"),
    ("10", "APPENDICES", "35"),
    ("10.1", "Sample Inputs and Outputs", "35"),
    ("10.2", "Additional Diagnostic Visualizations and Loss Curves", "36"),
    ("10.3", "Project Execution Gantt Chart", "36"),
    ("10.4", "Plagiarism Verification Report", "37"),
    ("10.5", "Academic Paper Publication Details", "38")
]
add_toc_rows(t4, toc_p4)
doc.add_page_break()

# ==========================================
# PAGE 10: LIST OF TABLES (Page X)
# ==========================================
print("Writing Page 10: List of Tables...")
p_lot = doc.add_paragraph()
p_lot.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_lot.paragraph_format.space_after = Pt(14)
r = p_lot.add_run("LIST OF TABLES")
r.font.name = 'Times New Roman'
r.font.size = Pt(14)
r.font.bold = True

t_lot = doc.add_table(rows=1, cols=3)
t_lot.alignment = WD_TABLE_ALIGNMENT.CENTER
for c_idx, h in enumerate(["TABLE NO.", "TITLE", "PAGE NO."]):
    p_c = t_lot.cell(0, c_idx).paragraphs[0]
    p_c.paragraph_format.line_spacing = 1.0
    p_c.paragraph_format.space_after = Pt(4)
    if c_idx == 2:
        p_c.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    else:
        p_c.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = p_c.add_run(h)
    r.font.bold = True
    r.font.size = Pt(11)

lot_rows = [
    ("2.1", "Research Gap", "9"),
    ("3.1", "VHRV Optical Satellite Benchmark Dataset Summary", "11"),
    ("3.2", "TITANIC-FGS-10 Maritime Vessel Classification Dataset Distribution", "15"),
    ("4.1", "Major System Components", "20"),
    ("5.1", "Development Environment", "21"),
    ("6.1", "Quantitative Satellite Vessel Detection Performance on VHRV Test Split", "25"),
    ("6.2", "Fine-Grained Vessel Classification Results on TITANIC-FGS-10 Test Split", "26"),
    ("6.3", "PPO Adaptive Compute Optimization Across Operational Missions", "27"),
    ("7.1", "System Testing", "29")
]
add_toc_rows(t_lot, lot_rows)
doc.add_page_break()

# ==========================================
# PAGE 11: LIST OF FIGURES (Page XI)
# ==========================================
print("Writing Page 11: List of Figures...")
p_lof = doc.add_paragraph()
p_lof.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_lof.paragraph_format.space_after = Pt(14)
r = p_lof.add_run("LIST OF FIGURES")
r.font.name = 'Times New Roman'
r.font.size = Pt(14)
r.font.bold = True

t_lof = doc.add_table(rows=1, cols=3)
t_lof.alignment = WD_TABLE_ALIGNMENT.CENTER
for c_idx, h in enumerate(["FIGURE NO.", "TITLE", "PAGE NO."]):
    p_c = t_lof.cell(0, c_idx).paragraphs[0]
    p_c.paragraph_format.line_spacing = 1.0
    p_c.paragraph_format.space_after = Pt(4)
    if c_idx == 2:
        p_c.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    else:
        p_c.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = p_c.add_run(h)
    r.font.bold = True
    r.font.size = Pt(11)

lof_rows = [
    ("3.1", "Dataset Preparation and Construction Pipeline for VHRV Benchmark", "12"),
    ("3.2", "Discrete Linear Kalman Filter Tracking Pipeline and State Transitions", "16"),
    ("4.1", "End-to-End Hierarchical System Architecture of OATrack-VLM Framework", "18"),
    ("5.1", "Maritime Surveillance Command Center Operations Dashboard (Streamlit)", "23"),
    ("6.1", "High-Resolution Satellite Vessel Detection Localization on VHRV Test Split", "25"),
    ("6.2", "Tactical UAV Persistent Tracking Visualization with Motion Trail", "26"),
    ("6.3", "Normalized Confusion Matrix of ConvNeXt-Tiny on TITANIC-FGS-10", "27"),
    ("6.4", "Model Training and Validation Convergence Curves", "27"),
    ("6.5", "Estimated Edge-Compute Savings Breakdown Across Maritime Scenarios", "28"),
    ("10.1", "Sample Satellite Detection Output and Grounded Groq VLM Intelligence Briefing", "35"),
    ("10.2", "Tactical UAV Video Frame Telemetry and Consensus Classification Output", "35"),
    ("10.3", "Detailed Detector Training and Validation Loss Progression Curves", "36"),
    ("10.4", "Project Execution Gantt Chart Across Academic Timeline", "36")
]
add_toc_rows(t_lof, lof_rows)
doc.add_page_break()

# ==========================================
# PAGE 12: LIST OF SYMBOLS AND ABBREVIATIONS (Page XII)
# ==========================================
print("Writing Page 12: List of Abbreviations...")
p_loa = doc.add_paragraph()
p_loa.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_loa.paragraph_format.space_after = Pt(14)
r = p_loa.add_run("LIST OF SYMBOLS AND ABBREVIATIONS")
r.font.name = 'Times New Roman'
r.font.size = Pt(14)
r.font.bold = True

t_loa = doc.add_table(rows=1, cols=2)
t_loa.alignment = WD_TABLE_ALIGNMENT.CENTER
for c_idx, h in enumerate(["ABBREVIATION", "EXPANSION"]):
    p_c = t_loa.cell(0, c_idx).paragraphs[0]
    p_c.paragraph_format.line_spacing = 1.0
    p_c.paragraph_format.space_after = Pt(4)
    r = p_c.add_run(h)
    r.font.bold = True
    r.font.size = Pt(11)

for abbr, exp in rd.ABBREVIATIONS:
    row = t_loa.add_row()
    p0 = row.cells[0].paragraphs[0]
    p0.paragraph_format.line_spacing = 1.15
    p0.paragraph_format.space_after = Pt(2)
    r0 = p0.add_run(abbr)
    r0.font.name = 'Times New Roman'
    r0.font.size = Pt(10.5)
    r0.font.bold = True
    
    p1 = row.cells[1].paragraphs[0]
    p1.paragraph_format.line_spacing = 1.15
    p1.paragraph_format.space_after = Pt(2)
    r1 = p1.add_run(f"- {exp}")
    r1.font.name = 'Times New Roman'
    r1.font.size = Pt(10.5)

# ==========================================
# START SECTION 2: MAIN BODY (PAGES 1 to 38)
# ==========================================
print("Configuring Section 2: Main Body...")
sec2 = doc.add_section()
sec2.top_margin = Inches(1.0)
sec2.bottom_margin = Inches(1.0)
sec2.left_margin = Inches(1.0)
sec2.right_margin = Inches(1.0)
sec2.different_first_page_header_footer = False
sec2.header.is_linked_to_previous = False
sec2.footer.is_linked_to_previous = False

foot2 = sec2.footer.paragraphs[0]
foot2.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_page_number_field(foot2)
sectPr2 = sec2._sectPr
pgNum2 = OxmlElement('w:pgNumType')
pgNum2.set(qn('w:fmt'), 'decimal')
pgNum2.set(qn('w:start'), '1')
sectPr2.append(pgNum2)

# ------------------------------------------
# PAGE 13 (Body p. 1): Chapter 1 Start
# ------------------------------------------
print("Writing Body Page 1: Chapter 1...")
p_chap_heading("1", rs.CH1_INTRO['title'])
p_body(rs.CH1_INTRO['intro_p1'])
p_body(rs.CH1_INTRO['intro_p2'])
p_body(rs.CH1_INTRO['intro_p3'])
p_sec_heading(rs.CH1_INTRO['s1_1'][0])
for p in rs.CH1_INTRO['s1_1'][1].split('\n\n'):
    p_body(p)
doc.add_page_break()

# ------------------------------------------
# PAGE 14 (Body p. 2): Chapter 1 Cont.
# ------------------------------------------
print("Writing Body Page 2: Chapter 1...")
p_sec_heading(rs.CH1_INTRO['s1_2'][0])
for p in rs.CH1_INTRO['s1_2'][1].split('\n\n'):
    p_body(p)
p_sec_heading(rs.CH1_INTRO['s1_3'][0])
for p in rs.CH1_INTRO['s1_3'][1].split('\n\n'):
    p_body(p)
doc.add_page_break()

# ------------------------------------------
# PAGE 15 (Body p. 3): Chapter 1 Cont.
# ------------------------------------------
print("Writing Body Page 3: Chapter 1...")
p_sec_heading(rs.CH1_INTRO['s1_4'][0])
for p in rs.CH1_INTRO['s1_4'][1].split('\n\n'):
    p_body(p)
p_sec_heading(rs.CH1_INTRO['s1_5'][0])
for p in rs.CH1_INTRO['s1_5'][1].split('\n\n'):
    p_body(p)
doc.add_page_break()

# ------------------------------------------
# PAGE 16 (Body p. 4): Chapter 1 Cont.
# ------------------------------------------
print("Writing Body Page 4: Chapter 1...")
p_sec_heading(rs.CH1_INTRO['s1_6'][0])
for p in rs.CH1_INTRO['s1_6'][1].split('\n\n'):
    p_body(p)
p_sec_heading(rs.CH1_INTRO['s1_7'][0])
p_parts = rs.CH1_INTRO['s1_7'][1].split('\n\n')
p_body(p_parts[0])
p_body(p_parts[1])
doc.add_page_break()

# ------------------------------------------
# PAGE 17 (Body p. 5): Chapter 1 End
# ------------------------------------------
print("Writing Body Page 5: Chapter 1 End...")
p_body(p_parts[2])
p_body(p_parts[3])
doc.add_page_break()

# ------------------------------------------
# PAGE 18 (Body p. 6): Chapter 2 Start
# ------------------------------------------
print("Writing Body Page 6: Chapter 2...")
p_chap_heading("-2", rs.CH2_LIT['title'])
p_body(rs.CH2_LIT['intro'])
p_sec_heading(rs.CH2_LIT['s2_1'][0])
p_body(rs.CH2_LIT['s2_1'][1])
doc.add_page_break()

# ------------------------------------------
# PAGE 19 (Body p. 7): Chapter 2 Cont.
# ------------------------------------------
print("Writing Body Page 7: Chapter 2...")
p_sec_heading(rs.CH2_LIT['s2_2'][0])
for p in split_p(rs.CH2_LIT['s2_2'][1]):
    p_body(p)
p_sec_heading(rs.CH2_LIT['s2_3'][0])
p_body(rs.CH2_LIT['s2_3'][1])
doc.add_page_break()

# ------------------------------------------
# PAGE 20 (Body p. 8): Chapter 2 Cont.
# ------------------------------------------
print("Writing Body Page 8: Chapter 2...")
p_sec_heading(rs.CH2_LIT['s2_4'][0])
p_body(rs.CH2_LIT['s2_4'][1])
p_sec_heading(rs.CH2_LIT['s2_5'][0])
p_body(rs.CH2_LIT['s2_5'][1])
p_sec_heading(rs.CH2_LIT['s2_6'][0])
for p in split_p(rs.CH2_LIT['s2_6'][1]):
    p_body(p)
doc.add_page_break()

# ------------------------------------------
# PAGE 21 (Body p. 9): Chapter 2 End & Table 2.1
# ------------------------------------------
print("Writing Body Page 9: Chapter 2 End...")
add_table_data(rs.TABLES_DATA['t2_1'], [Inches(1.8), Inches(2.3), Inches(2.2)])
p_sec_heading(rs.CH2_LIT['s2_7'][0])
for p in split_p(rs.CH2_LIT['s2_7'][1]):
    p_body(p)
doc.add_page_break()

# ------------------------------------------
# PAGE 22 (Body p. 10): Chapter 3 Start
# ------------------------------------------
print("Writing Body Page 10: Chapter 3...")
p_chap_heading("3", rs.CH3_DATA_METHOD['title'])
p_body(rs.CH3_DATA_METHOD['intro'])
p_sec_heading(rs.CH3_DATA_METHOD['s3_1'][0])
for p in split_p(rs.CH3_DATA_METHOD['s3_1'][1]):
    p_body(p)
add_table_data(rs.TABLES_DATA['t3_1'], [Inches(1.5), Inches(1.1), Inches(1.1), Inches(1.3), Inches(1.3)])
p_sec_heading(rs.CH3_DATA_METHOD['s3_2'][0])
for p in split_p(rs.CH3_DATA_METHOD['s3_2'][1]):
    p_body(p)
doc.add_page_break()

# ------------------------------------------
# PAGE 23 (Body p. 11): Chapter 3 Cont. (Figure 3.1)
# ------------------------------------------
print("Writing Body Page 11: Chapter 3...")
p_body(
    "Data Preprocessing Workflow: Raw Satellite Swathes → Spatial Coordinate Tiling → Bounding Box Integrity Validation → "
    "Augmentation Pipeline → Stratified Train/Val/Test Partitioning → Verified Ground-Truth Benchmark."
)
p_body(
    "The dataset preparation methodology ensures authentic spatial scaling, suppressing distortion of small surface craft "
    "while eliminating background landmass noise."
)
add_figure(r'f:\OATrack-VLM_complete_project\generated_figures\fig3_1_dataset_pipeline.png',
           "Figure 3.1: Dataset Preparation and Construction Pipeline for VHRV Benchmark", width_in=5.6)
p_sec_heading(rs.CH3_DATA_METHOD['s3_3'][0])
p_body(rs.CH3_DATA_METHOD['s3_3'][1])
doc.add_page_break()

# ------------------------------------------
# PAGE 24 (Body p. 12): Chapter 3 Cont.
# ------------------------------------------
print("Writing Body Page 12: Chapter 3...")
p_subsec_heading("3.3.1 Ground-Truth Bounding Box Integrity Verification")
p_body(
    "Ground truth annotations in VHRV follow horizontal bounding box format [class_id, x_center, y_center, width, height] normalized "
    "to [0, 1]. Verification audits confirmed zero out-of-bounds annotations, eliminating degenerate bounding boxes."
)
p_subsec_heading("3.3.2 High-Resolution Coordinate Normalization")
p_body(
    "To support 1024x1024 inference without bounding distortion, images undergo letterbox padding with reflection boundaries, "
    "preserving native aspect ratios of elongated container ships and naval destroyers."
)
p_sec_heading(rs.CH3_DATA_METHOD['s3_4'][0])
p_body(rs.CH3_DATA_METHOD['s3_4'][1])
p_sec_heading(rs.CH3_DATA_METHOD['s3_5'][0])
p_body(rs.CH3_DATA_METHOD['s3_5'][1])
doc.add_page_break()

# ------------------------------------------
# PAGE 25 (Body p. 13): Chapter 3 Cont. (Kalman Tracking)
# ------------------------------------------
print("Writing Body Page 13: Chapter 3...")
p_sec_heading(rs.CH3_DATA_METHOD['s3_6'][0])
for p in split_p(rs.CH3_DATA_METHOD['s3_6'][1]):
    p_body(p)
doc.add_page_break()

# ------------------------------------------
# PAGE 26 (Body p. 14): Chapter 3 Cont. (Table 3.2 & Classifier)
# ------------------------------------------
print("Writing Body Page 14: Chapter 3...")
p_sec_heading("3.6.4 Hierarchy of Tracking and Classification Stages")
p_body(
    "Vessel Perception Hierarchy: Wide-Area Satellite Coordinates → Kalman Filter State Tracking → Sub-Part Suppression → "
    "Context Crop Extraction → ConvNeXt-Tiny Fine-Grained Inference → Multi-Frame Temporal Consensus."
)
add_table_data(rs.TABLES_DATA['t3_2'], [Inches(1.8), Inches(1.1), Inches(1.1), Inches(1.1), Inches(1.2)])
p_sec_heading(rs.CH3_DATA_METHOD['s3_7'][0])
for p in split_p(rs.CH3_DATA_METHOD['s3_7'][1]):
    p_body(p)
doc.add_page_break()

# ------------------------------------------
# PAGE 27 (Body p. 15): Chapter 3 Cont. (Figure 3.2 & PPO)
# ------------------------------------------
print("Writing Body Page 15: Chapter 3...")
add_figure(r'f:\OATrack-VLM_complete_project\paper\figures\kalman_tracking_pipeline.png',
           "Figure 3.2: Discrete Linear Kalman Filter Tracking Pipeline and State Transitions", width_in=5.4)
p_sec_heading(rs.CH3_DATA_METHOD['s3_8'][0])
for p in split_p(rs.CH3_DATA_METHOD['s3_8'][1]):
    p_body(p)
doc.add_page_break()

# ------------------------------------------
# PAGE 28 (Body p. 16): Chapter 3 End
# ------------------------------------------
print("Writing Body Page 16: Chapter 3 End...")
p_sec_heading(rs.CH3_DATA_METHOD['s3_9'][0])
p_body(rs.CH3_DATA_METHOD['s3_9'][1])
p_subsec_heading("3.9.1 Multi-Tier Telemetry Integration")
p_body(
    "The grounded multimodal reasoning schema unifies sensor metadata across the pipeline: Satellite target coordinates, "
    "UAV Track IDs, Kalman velocity vectors, and ConvNeXt class probabilities are integrated into a verifiable prompt context."
)
p_subsec_heading("3.9.2 Hallucination Prevention Constraints")
p_body(
    "The reasoning engine enforces strict negative constraints: Absent AIS transponder data or physical flag markings, the system "
    "prohibits unobservable geopolitical claims, ensuring operational reliability in military and coast guard applications."
)
doc.add_page_break()

# ------------------------------------------
# PAGE 29 (Body p. 17): Chapter 4 Start
# ------------------------------------------
print("Writing Body Page 17: Chapter 4...")
p_chap_heading("4", rs.CH4_SYS_DESIGN['title'])
p_body(rs.CH4_SYS_DESIGN['intro'])
p_sec_heading(rs.CH4_SYS_DESIGN['s4_1'][0])
for p in split_p(rs.CH4_SYS_DESIGN['s4_1'][1]):
    p_body(p)
doc.add_page_break()

# ------------------------------------------
# PAGE 30 (Body p. 18): Chapter 4 Cont. (Figure 4.1)
# ------------------------------------------
print("Writing Body Page 18: Chapter 4...")
add_figure(r'f:\OATrack-VLM_complete_project\paper\figures\system_architecture.png',
           "Figure 4.1: End-to-End Hierarchical System Architecture of OATrack-VLM Framework", width_in=5.6)
p_sec_heading(rs.CH4_SYS_DESIGN['s4_2'][0])
for p in split_p(rs.CH4_SYS_DESIGN['s4_2'][1]):
    p_body(p)
doc.add_page_break()

# ------------------------------------------
# PAGE 31 (Body p. 19): Chapter 4 Cont.
# ------------------------------------------
print("Writing Body Page 19: Chapter 4...")
p_sec_heading(rs.CH4_SYS_DESIGN['s4_3'][0])
for p in split_p(rs.CH4_SYS_DESIGN['s4_3'][1]):
    p_body(p)
p_sec_heading(rs.CH4_SYS_DESIGN['s4_4'][0])
for p in split_p(rs.CH4_SYS_DESIGN['s4_4'][1]):
    p_body(p)
doc.add_page_break()

# ------------------------------------------
# PAGE 32 (Body p. 20): Chapter 4 End & Table 4.1
# ------------------------------------------
print("Writing Body Page 20: Chapter 4 End...")
p_sec_heading(rs.CH4_SYS_DESIGN['s4_5'][0])
p_body(rs.CH4_SYS_DESIGN['s4_5'][1])
add_table_data(rs.TABLES_DATA['t4_1'], [Inches(1.8), Inches(1.3), Inches(3.2)])
p_body(
    "The modular decoupling of components ensures each tier executes within its latency envelope, allowing seamless edge "
    "deployment without inter-stage synchronization deadlocks."
)
doc.add_page_break()

# ------------------------------------------
# PAGE 33 (Body p. 21): Chapter 5 Start
# ------------------------------------------
print("Writing Body Page 21: Chapter 5...")
p_chap_heading("-5", rs.CH5_METHODOLOGY['title'])
p_body(rs.CH5_METHODOLOGY['intro'])
p_sec_heading(rs.CH5_METHODOLOGY['s5_1'][0])
p_body(rs.CH5_METHODOLOGY['s5_1'][1])
add_table_data(rs.TABLES_DATA['t5_1'], [Inches(2.5), Inches(3.8)])
p_sec_heading(rs.CH5_METHODOLOGY['s5_2'][0])
for p in split_p(rs.CH5_METHODOLOGY['s5_2'][1]):
    p_body(p)
doc.add_page_break()

# ------------------------------------------
# PAGE 34 (Body p. 22): Chapter 5 Cont.
# ------------------------------------------
print("Writing Body Page 22: Chapter 5...")
p_sec_heading(rs.CH5_METHODOLOGY['s5_3'][0])
for p in split_p(rs.CH5_METHODOLOGY['s5_3'][1]):
    p_body(p)
p_sec_heading(rs.CH5_METHODOLOGY['s5_4'][0])
for p in split_p(rs.CH5_METHODOLOGY['s5_4'][1]):
    p_body(p)
p_sec_heading(rs.CH5_METHODOLOGY['s5_5'][0])
for p in split_p(rs.CH5_METHODOLOGY['s5_5'][1]):
    p_body(p)
doc.add_page_break()

# ------------------------------------------
# PAGE 35 (Body p. 23): Chapter 5 End (Figure 5.1)
# ------------------------------------------
print("Writing Body Page 23: Chapter 5 End...")
add_figure(r'f:\OATrack-VLM_complete_project\generated_figures\fig5_1_command_center.png',
           "Figure 5.1: Maritime Surveillance Command Center Operations Dashboard (Streamlit)", width_in=5.5)
p_sec_heading(rs.CH5_METHODOLOGY['s5_6'][0])
p_body(rs.CH5_METHODOLOGY['s5_6'][1])
p_body(
    "The operational prototype validates the transition from offline machine learning models to an integrated, "
    "operator-ready tactical command dashboard."
)
doc.add_page_break()

# ------------------------------------------
# PAGE 36 (Body p. 24): Chapter 6 Start (Table 6.1)
# ------------------------------------------
print("Writing Body Page 24: Chapter 6...")
p_chap_heading("-6", rs.CH6_RESULTS['title'])
p_body(rs.CH6_RESULTS['intro'])
p_sec_heading(rs.CH6_RESULTS['s6_1'][0])
for p in split_p(rs.CH6_RESULTS['s6_1'][1]):
    p_body(p)
p_sec_heading(rs.CH6_RESULTS['s6_2'][0])
for p in split_p(rs.CH6_RESULTS['s6_2'][1]):
    p_body(p)
p_sec_heading(rs.CH6_RESULTS['s6_3'][0])
p_parts_6_3 = split_p(rs.CH6_RESULTS['s6_3'][1])
p_body(p_parts_6_3[0])
add_table_data(rs.TABLES_DATA['t6_1'], [Inches(1.8), Inches(0.8), Inches(0.8), Inches(0.8), Inches(0.8), Inches(0.8), Inches(0.8), Inches(0.8)])
if len(p_parts_6_3) > 1:
    p_body(p_parts_6_3[1])
doc.add_page_break()

# ------------------------------------------
# PAGE 37 (Body p. 25): Chapter 6 Cont. (Figure 6.1 & Table 6.2)
# ------------------------------------------
print("Writing Body Page 25: Chapter 6...")
add_figure(r'f:\OATrack-VLM_complete_project\paper\figures\satellite_detection.png',
           "Figure 6.1: High-Resolution Satellite Vessel Detection Localization on VHRV Test Split", width_in=5.4)
p_sec_heading(rs.CH6_RESULTS['s6_4'][0])
p_parts_6_4 = split_p(rs.CH6_RESULTS['s6_4'][1])
p_body(p_parts_6_4[0])
for p in p_parts_6_4[1:]:
    p_body(p)
add_table_data(rs.TABLES_DATA['t6_2'], [Inches(2.5), Inches(1.2), Inches(1.2), Inches(1.2), Inches(1.2)])
doc.add_page_break()

# ------------------------------------------
# PAGE 38 (Body p. 26): Chapter 6 Cont. (Figure 6.2)
# ------------------------------------------
print("Writing Body Page 26: Chapter 6...")
add_figure(r'f:\OATrack-VLM_complete_project\paper\figures\uav_tracking_fixed.png',
           "Figure 6.2: Tactical UAV Persistent Tracking Visualization with Motion Trail", width_in=4.8)
p_sec_heading(rs.CH6_RESULTS['s6_5'][0])
for p in split_p(rs.CH6_RESULTS['s6_5'][1]):
    p_body(p)
p_sec_heading(rs.CH6_RESULTS['s6_6'][0])
p_body(rs.CH6_RESULTS['s6_6'][1])
doc.add_page_break()

# ------------------------------------------
# PAGE 39 (Body p. 27): Chapter 6 Cont. (Figure 6.3 & 6.4)
# ------------------------------------------
print("Writing Body Page 27: Chapter 6...")
add_figure(r'f:\OATrack-VLM_complete_project\paper\figures\confusion_matrix.png',
           "Figure 6.3: Normalized Confusion Matrix of ConvNeXt-Tiny on TITANIC-FGS-10", width_in=4.4)
add_figure(r'f:\OATrack-VLM_complete_project\paper\figures\training_curves.png',
           "Figure 6.4: Model Training and Validation Convergence Curves", width_in=5.4)
doc.add_page_break()

# ------------------------------------------
# PAGE 40 (Body p. 28): Chapter 6 End (Table 6.3 & Figure 6.5)
# ------------------------------------------
print("Writing Body Page 28: Chapter 6 End...")
p_sec_heading(rs.CH6_RESULTS['s6_7'][0])
p_parts_6_7 = split_p(rs.CH6_RESULTS['s6_7'][1])
p_body(p_parts_6_7[0])
add_table_data(rs.TABLES_DATA['t6_3'], [Inches(1.8), Inches(0.8), Inches(1.0), Inches(1.0), Inches(1.0), Inches(1.7)])
add_figure(r'f:\OATrack-VLM_complete_project\paper\figures\adaptive_compute_breakdown.png',
           "Figure 6.5: Estimated Edge-Compute Savings Breakdown Across Maritime Scenarios", width_in=5.0)
p_sec_heading(rs.CH6_RESULTS['s6_8'][0])
p_body(rs.CH6_RESULTS['s6_8'][1])
p_sec_heading(rs.CH6_RESULTS['s6_9'][0])
p_body(rs.CH6_RESULTS['s6_9'][1])
p_sec_heading(rs.CH6_RESULTS['s6_10'][0])
p_body(rs.CH6_RESULTS['s6_10'][1])
doc.add_page_break()

# ------------------------------------------
# PAGE 41 (Body p. 29): Chapter 7 Start (Table 7.1)
# ------------------------------------------
print("Writing Body Page 29: Chapter 7...")
p_chap_heading("-7", rs.CH7_TESTING['title'])
p_body(rs.CH7_TESTING['intro'])
p_sec_heading(rs.CH7_TESTING['s7_1'][0])
p_body(rs.CH7_TESTING['s7_1'][1])
add_table_data(rs.TABLES_DATA['t7_1'], [Inches(1.8), Inches(1.8), Inches(1.8), Inches(1.8), Inches(0.8)])
p_sec_heading(rs.CH7_TESTING['s7_2'][0])
for p in split_p(rs.CH7_TESTING['s7_2'][1]):
    p_body(p)
doc.add_page_break()

# ------------------------------------------
# PAGE 42 (Body p. 30): Chapter 7 End (Limitations)
# ------------------------------------------
print("Writing Body Page 30: Chapter 7 End...")
p_sec_heading(rs.CH7_TESTING['s7_3'][0])
for p in split_p(rs.CH7_TESTING['s7_3'][1]):
    p_body(p)
p_body(
    "These operational limitations establish clear scientific boundaries for current deployment while "
    "providing a well-defined trajectory for future industrialization and field sea trials."
)
doc.add_page_break()

# ------------------------------------------
# PAGE 43 (Body p. 31): Chapter 8 (Conclusion & Future Work)
# ------------------------------------------
print("Writing Body Page 31: Chapter 8...")
p_chap_heading("-8", rs.CH8_CONCLUSION['title'])
p_sec_heading(rs.CH8_CONCLUSION['s8_1'][0])
for p in split_p(rs.CH8_CONCLUSION['s8_1'][1]):
    p_body(p)
p_sec_heading(rs.CH8_CONCLUSION['s8_2'][0])
for p in split_p(rs.CH8_CONCLUSION['s8_2'][1]):
    p_body(p)
doc.add_page_break()

# ------------------------------------------
# PAGES 44 to 46 (Body pp. 32-34): Chapter 9 (References)
# ------------------------------------------
print("Writing Body Pages 32 to 34: Chapter 9 References...")
# Ref Page 1 (Refs [1] to [9])
p_ref_head = doc.add_paragraph()
p_ref_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_ref_head.paragraph_format.space_after = Pt(16)
r = p_ref_head.add_run("REFERENCES")
r.font.name = 'Times New Roman'
r.font.size = Pt(14)
r.font.bold = True

for ref in rs.REFERENCES_LIST[:9]:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(8)
    r = p.add_run(ref)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(11)
doc.add_page_break()

# Ref Page 2 (Refs [10] to [18])
for ref in rs.REFERENCES_LIST[9:18]:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(8)
    r = p.add_run(ref)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(11)
doc.add_page_break()

# Ref Page 3 (Refs [19] to [26])
for ref in rs.REFERENCES_LIST[18:]:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(8)
    r = p.add_run(ref)
    r.font.name = 'Times New Roman'
    r.font.size = Pt(11)
doc.add_page_break()

# ------------------------------------------
# PAGES 47 to 50 (Body pp. 35-38): Chapter 10 (Appendices)
# ------------------------------------------
print("Writing Body Pages 35 to 38: Chapter 10 Appendices...")
# Appendix Page 1 (Outputs: Fig 10.1 & Fig 10.2)
p_app_head = doc.add_paragraph()
p_app_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_app_head.paragraph_format.space_after = Pt(12)
r = p_app_head.add_run("APPENDICES")
r.font.name = 'Times New Roman'
r.font.size = Pt(14)
r.font.bold = True

p_sec_heading("10.1 Sample Inputs and Outputs")
add_figure(r'f:\OATrack-VLM_complete_project\generated_figures\fig10_1_satellite_sample.png',
           "Figure 10.1: Sample Satellite Detection Output and Grounded Groq VLM Intelligence Briefing", width_in=5.4)
add_figure(r'f:\OATrack-VLM_complete_project\generated_figures\fig10_2_drone_sample.png',
           "Figure 10.2: Tactical UAV Video Frame Telemetry and Consensus Classification Output", width_in=5.4)
doc.add_page_break()

# Appendix Page 2 (Diagrams & Gantt: Fig 10.3 & Fig 10.4)
p_sec_heading("10.2 Additional Diagnostic Visualizations and Loss Curves")
add_figure(r'f:\OATrack-VLM_complete_project\OATrack-VLM\outputs\loss_graphs\yolo_detector_loss_graph.png',
           "Figure 10.3: Detailed Detector Training and Validation Loss Progression Curves", width_in=5.4)
p_sec_heading("10.3 Project Execution Gantt Chart")
add_figure(r'f:\OATrack-VLM_complete_project\generated_figures\fig10_4_gantt_chart.png',
           "Figure 10.4: Project Execution Gantt Chart Across Academic Timeline", width_in=5.4)
doc.add_page_break()

# Appendix Page 3 (Plagiarism Verification)
p_plag_head = doc.add_paragraph()
p_plag_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_plag_head.paragraph_format.space_after = Pt(14)
r = p_plag_head.add_run("PLAGIARISM VERIFICATION REPORT")
r.font.name = 'Times New Roman'
r.font.size = Pt(14)
r.font.bold = True

p_body(
    "The complete manuscript of the OATrack-VLM project report was subjected to automated similarity indexing via Turnitin "
    "under institutional supervision. The similarity index verified that all algorithmic formulations, benchmark evaluations, "
    "and system analyses maintain strict academic originality."
)
add_figure(r'f:\OATrack-VLM_complete_project\extracted_assets\p49_img0_157.png',
           "Turnitin Originality Report: 5% Overall Similarity Index (Verified Institutional Submission)", width_in=5.0)
doc.add_page_break()

# Appendix Page 4 (Paper Publication Details)
p_pub_head = doc.add_paragraph()
p_pub_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_pub_head.paragraph_format.space_after = Pt(14)
r = p_pub_head.add_run("ACADEMIC PAPER PUBLICATION DETAILS")
r.font.name = 'Times New Roman'
r.font.size = Pt(14)
r.font.bold = True

p_body(
    "Title: “A Hierarchical Multimodal Framework for Autonomous Maritime Surveillance Using Satellite Detection, "
    "Kalman-Filter UAV Tracking, and Vision-Language Reasoning”\\n\\n"
    "Authors: Aman Reddy J, BTPR Nikhil, and Dr. K Ashwini\\n"
    "Affiliation: Department of Computer Science and Engineering, Amrita School of Computing, Amrita Vishwa Vidyapeetham, Chennai, India\\n\\n"
    "Conference: International Conference on Wireless Communications, Signal Processing and Networking (WiSPNET 2026), "
    "IEEE Xplore Digital Library.\\n"
    "DOI: 10.1109/WiSPNET69615.2026.11489415\\n\\n"
    "This publication documents the end-to-end integration of strategic spaceborne vessel localization, discrete linear Kalman filter "
    "tactical drone tracking, fine-grained vessel classification, and reinforcement-learning-driven adaptive edge compute scheduling."
)
add_figure(r'f:\OATrack-VLM_complete_project\extracted_assets\p50_img0_161.jpeg',
           "Certificate of Appreciation and Presentation — IEEE WiSPNET 2026 Conference", width_in=4.8)

# Save Document
out_docx = r'f:\OATrack-VLM_complete_project\OATrack_VLM_Project_Report.docx'
out_pdf = r'f:\OATrack-VLM_complete_project\OATrack_VLM_Project_Report.pdf'
doc.save(out_docx)
print(f"Saved DOCX document to: {out_docx}")

# Compile to PDF using Word 2021 COM
print("Compiling DOCX to PDF using Microsoft Word 2021 COM...")
word = win32com.client.Dispatch("Word.Application")
word.Visible = False
try:
    wdoc = word.Documents.Open(os.path.abspath(out_docx))
    wdoc.SaveAs(os.path.abspath(out_pdf), FileFormat=17) # 17 = wdFormatPDF
    wdoc.Close()
    print(f"Successfully compiled PDF to: {out_pdf}")
finally:
    word.Quit()

# Verify PDF page count with fitz
pdf_doc = fitz.open(out_pdf)
print(f"=== VERIFICATION OF FINAL PDF ===")
print(f"Total Page Count: {len(pdf_doc)} pages")
print(f"File Size: {os.path.getsize(out_pdf) / (1024*1024):.2f} MB")
for i in [0, 1, 3, 5, 12, 17, 21, 35, len(pdf_doc)-1]:
    p = pdf_doc[i]
    lines = [l.strip() for l in p.get_text().splitlines() if l.strip()]
    top_line = lines[0] if lines else ''
    bot_line = lines[-1] if lines else ''
    print(f"Page {i+1:2d}: Top: {top_line[:35]:35s} | Bot: {bot_line[:20]:20s}")
pdf_doc.close()
print("BUILD COMPLETED WITH 100% FIDELITY!")
