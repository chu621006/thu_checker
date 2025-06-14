import pdfplumber
import pandas as pd
import json
import re

def load_category_map():
    with open("data/category_map.json", "r", encoding="utf-8") as f:
        return json.load(f)

def parse_pdf(uploaded_file):
    with pdfplumber.open(uploaded_file) as pdf:
        text = ""
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def extract_courses(text):
    lines = text.splitlines()
    courses = []
    for line in lines:
        match = re.search(r"(.+?)\s+(\d+(?:\.\d+)?)學分\s+GPA[:：]?\s*(\S+)?", line)
        if match:
            name, credit, gpa = match.groups()
            credit = float(credit)
            try:
                gpa_val = float(gpa) if gpa and gpa.replace('.', '', 1).isdigit() else None
            except:
                gpa_val = None
            courses.append({"課程名稱": name.strip(), "學分": credit, "GPA": gpa_val})
    return pd.DataFrame(courses)

def analyze_pdf(uploaded_file):
    import json
    text = parse_pdf(uploaded_file, max_pages=5)  # 最多處理前5頁
    df = extract_courses(text)
    category_map = load_category_map()

    if df.empty:
        return {
            "course_table": pd.DataFrame(),
            "summary_table": pd.DataFrame([{
                "分類": "必修", "已修學分": 0, "應修學分": 84
            }, {
                "分類": "I 類選修", "已修學分": 0, "應修學分": 10
            }, {
                "分類": "II 類選修", "已修學分": 0, "應修學分": 10
            }, {
                "分類": "選修總學分", "已修學分": 0, "應修學分": 44
            }])
        }

    # 建立快速對照表（課名 ➜ 分類）
    name_to_category = {
        name: cat
        for cat, names in category_map.items()
        for name in names
    }

    # 一次完成分類
    df["分類標記"] = df["課程名稱"].map(name_to_category).fillna("一般選修")
    df["必修"] = df["分類標記"] == "必修"
    df["I類選修"] = df["分類標記"] == "I類選修"
    df["II類選修"] = df["分類標記"] == "II類選修"
    df["一般選修"] = df["分類標記"] == "一般選修"

    # 有效學分過濾
    def compute_valid_credit(r):
        try:
            return r["學分"] if r["GPA"] is not None and r["GPA"] >= 1.7 else 0
        except:
            return 0
    df["有效學分"] = df.apply(compute_valid_credit, axis=1)

    summary = {
        "必修": df[df["必修"]]["有效學分"].sum(),
        "I類選修": df[df["I類選修"]]["有效學分"].sum(),
        "II類選修": df[df["II類選修"]]["有效學分"].sum(),
        "一般選修": df[df["一般選修"]]["有效學分"].sum()
    }

    total_elective = summary["I類選修"] + summary["II類選修"] + summary["一般選修"]

    summary_table = pd.DataFrame([{
        "分類": "必修", "已修學分": summary["必修"], "應修學分": 84
    }, {
        "分類": "I 類選修", "已修學分": summary["I類選修"], "應修學分": 10
    }, {
        "分類": "II 類選修", "已修學分": summary["II類選修"], "應修學分": 10
    }, {
        "分類": "選修總學分", "已修學分": total_elective, "應修學分": 44
    }])

    return {
        "course_table": df,
        "summary_table": summary_table
    }

def check_requirements(summary_df):
    summary_df["是否達標"] = summary_df["已修學分"] >= summary_df["應修學分"]
    summary_df["尚缺學分"] = summary_df["應修學分"] - summary_df["已修學分"]
    summary_df["尚缺學分"] = summary_df["尚缺學分"].apply(lambda x: 0 if x < 0 else x)
    return summary_df
