"""
core/i18n.py
------------
Arabic/English translation helpers extracted from dashboard_app.py
(Phase 1 extraction). COLUMN_AR must be preserved exactly — i18n
correctness matters for Arabic-speaking users.

`tr()` and the column-label/localization helpers depend on the page's
active language (`is_ar`), which lives in Streamlit session state in the
page-rendering layer. To keep this module free of implicit global state,
each function takes `is_ar` explicitly instead of reading a module-level
global.
"""

COLUMN_AR = {
    "Work Type": "نوع العنصر", "Total": "الإجمالي", "Done": "مكتمل",
    "Completion %": "نسبة الاكتمال", "State": "الحالة", "Category": "التصنيف",
    "Items": "العناصر", "Iteration": "الدورة", "Total Dev Items": "إجمالي عناصر التسليم",
    "User Stories": "قصص المستخدم", "Stories Done": "القصص المكتملة",
    "Scope Done %": "اكتمال النطاق", "Tasks": "المهام", "Tasks Done": "المهام المكتملة",
    "Task Done %": "اكتمال المهام", "Active": "قيد التنفيذ", "Unassigned": "بدون مسؤول",
    "ID": "المعرف", "Title": "العنوان", "Type": "النوع", "State Category": "تصنيف الحالة",
    "Board Column": "عمود اللوحة", "Board Lane": "مسار اللوحة", "Assignee": "المسؤول",
    "Area": "المجال", "Tags": "الوسوم", "Priority": "الأولوية", "Created": "تاريخ الإنشاء",
    "Changed": "تاريخ التعديل", "Age (d)": "العمر بالأيام", "Parent ID": "معرف الأصل",
    "Azure Link": "رابط Azure", "Tag": "الوسم", "Stories": "القصص", "Scope %": "النطاق",
    "Task %": "نسبة اكتمال المهام", "Areas": "المجالات", "Task Completion %": "اكتمال المهام",
    "Open": "مفتوح", "Stories Involved": "القصص المشاركة", "Stories Fully Done": "القصص المكتملة",
    "SP": "النقاط", "Done SP": "النقاط المكتملة", "Risk": "المخاطر", "Age": "العمر",
    "Sprint": "السبرينت", "Check": "الفحص", "Count": "العدد", "Interpretation": "التفسير",
    "Work Item ID": "معرف العنصر", "Work Item Type": "نوع العنصر", "Assigned To": "المسؤول",
    "Iteration Path": "مسار الدورة", "Area Path": "مسار المجال", "Story Points": "نقاط القصة",
    "Created Date": "تاريخ الإنشاء", "Changed Date": "تاريخ التعديل", "Board Column Done": "اكتمال عمود اللوحة",
    "Repository": "المستودع", "Repository ID": "معرف المستودع", "Default Branch": "الفرع الافتراضي",
    "Size (bytes)": "الحجم بالبايت", "Disabled": "معطّل", "Remote URL": "رابط الاستنساخ",
    "Contributor": "المساهم", "Email": "البريد", "Repositories": "المستودعات", "Commits": "Commits",
    "Pushes": "عمليات الرفع", "Pull Requests": "Pull Requests", "Commit ID": "معرف Commit",
    "Short ID": "المعرف المختصر", "Message": "الرسالة", "Author": "الكاتب", "Author Email": "بريد الكاتب",
    "Author Date": "تاريخ الكتابة", "Committer": "منفذ Commit", "Commit Date": "تاريخ Commit",
    "Change Counts": "ملخص التغييرات", "Push ID": "معرف الرفع", "Pushed By": "رفع بواسطة",
    "Pusher Email": "بريد من قام بالرفع", "Push Date": "تاريخ الرفع", "Branches": "الفروع",
    "PR ID": "معرف PR", "Description": "الوصف", "Status": "الحالة", "Draft": "مسودة",
    "Created By": "أنشأ بواسطة", "Creator Email": "بريد المنشئ", "Closed Date": "تاريخ الإغلاق",
    "Source Branch": "فرع المصدر", "Target Branch": "الفرع المستهدف", "Reviewers": "المراجعون",
    "Merge Status": "حالة الدمج", "Merge Commit": "Commit الدمج", "Change #": "رقم التغيير",
    "Change Type": "نوع التغيير", "Path": "المسار", "Original Path": "المسار الأصلي",
    "Git Object Type": "نوع Git", "Object ID": "معرف الكائن", "Operation": "العملية", "Error": "الخطأ",
}


def tr(english, arabic, is_ar):
    return arabic if is_ar else english


def column_label(name, is_ar):
    return COLUMN_AR.get(name, name) if is_ar else name


def localized_frame(frame, is_ar):
    if not is_ar:
        return frame
    return frame.rename(columns={name: column_label(name, is_ar) for name in frame.columns})
