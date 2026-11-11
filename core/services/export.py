"""
Excel export service using openpyxl.
Generates styled, professional spreadsheets for participant lists.
"""
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from django.http import HttpResponse

def export_participants_to_excel(queryset, filename_prefix: str = "ishtirokchilar") -> HttpResponse:
    """
    Exports a queryset of Participant objects to a styled Excel workbook.
    Columns include:
      1. № (T/r)
      2. ID Raqami (reg_number)
      3. Ism (first_name)
      4. Familiya (last_name)
      5. Telefon Raqami (phone_number)
      6. Maktab Nomeri (school_number)
      7. Viloyat (region)
      8. Tuman / Shahar (district)
      9. Imtihonga Keldi (is_attended)
      10. Ro'yxatdan O'tgan Vaqt (created_at)
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Ishtirokchilar"

    # Freeze top row so header stays fixed while scrolling
    ws.freeze_panes = "A2"

    headers = [
        "№",
        "ID Raqami",
        "Ism",
        "Familiya",
        "Telefon Raqami",
        "Maktab Nomeri",
        "Viloyat",
        "Tuman / Shahar",
        "Imtihonga Keldi",
        "Ro'yxatdan O'tgan Vaqt"
    ]
    ws.append(headers)

    # Styles
    header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    
    even_row_fill = PatternFill(start_color="F2F5F8", end_color="F2F5F8", fill_type="solid")
    regular_font = Font(name="Calibri", size=10)
    
    thin_border_side = Side(border_style="thin", color="D3D3D3")
    cell_border = Border(
        left=thin_border_side,
        right=thin_border_side,
        top=thin_border_side,
        bottom=thin_border_side
    )
    
    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")

    # Format Header Row (Row 1)
    ws.row_dimensions[1].height = 28
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align
        cell.border = cell_border

    # Populate Data Rows
    participants_iterable = queryset.iterator(chunk_size=1000) if hasattr(queryset, 'iterator') else queryset
    for row_idx, p in enumerate(participants_iterable, start=2):
        ws.row_dimensions[row_idx].height = 20
        is_even = (row_idx % 2 == 0)
        row_fill = even_row_fill if is_even else None

        attended_text = "Ha" if p.is_attended else "Yo'q"
        created_str = p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else ""

        row_data = [
            row_idx - 1,
            p.reg_number,
            p.first_name,
            p.last_name,
            p.phone_number,
            p.school_number,
            p.region,
            p.district,
            attended_text,
            created_str
        ]
        ws.append(row_data)

        # Style each cell in the row
        for col_num in range(1, len(row_data) + 1):
            cell = ws.cell(row=row_idx, column=col_num)
            cell.font = regular_font
            cell.border = cell_border
            if row_fill:
                cell.fill = row_fill

            # Align numbers and dates centered, names and places left-aligned
            if col_num in (1, 2, 5, 9, 10):
                cell.alignment = center_align
            else:
                cell.alignment = left_align

    # Auto-adjust column widths based on maximum content length
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or '')
            if len(val_str) > max_len:
                max_len = len(val_str)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    # Build HTTP response
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"{filename_prefix}_{timestamp}.xlsx"

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response
