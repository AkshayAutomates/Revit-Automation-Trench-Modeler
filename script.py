# -*- coding: utf-8 -*-
__doc__     = """Version = 2.0
Date    = 03.26.2026
________________________________________________________________
Description: This Add-In will create Default Cable trays as a Trenches to all pipe work, to support Excavation work. 
________________________________________________________________
How-To:

1. Press Trench Modeller Push-Button
2. Select Pipes and Conduits to provide Trench.
3. Once Trench is Created, check if all pipes are having trench modelled at given level.
________________________________________________________________
Last Updates:
-[03.26.2026] v2.0 Included Conduits with pipes category to cover it by Trench
-[02.08.2026] v1.0 Removed Mulitple pressing of pushbuttons for every process, merged in single press with one after one eteration.
-[02.04.2026] v0.3 Covering for different pipe elevations in single trenches.
-[01.27.2026] v0.2 Tray modeling at -50 below BOP 
-[01.26.2026] v0.1 Tray modeling at -100 below BOP 
________________________________________________________________
Author: Akshay Pawar """


from Autodesk.Revit import DB
from Autodesk.Revit.DB import (
    FilteredElementCollector, BuiltInCategory, BuiltInParameter, StorageType
)
from Autodesk.Revit.UI.Selection import ObjectType
from pyrevit import forms, revit
import math

doc = revit.doc
uidoc = revit.uidoc

# ----------------------------
# Helpers
# ----------------------------
def mm_to_internal(mm):
    return mm / 304.8


def get_element_diameter_param(el):
    if el is None:
        return None

    # Pipe (outer diameter)
    try:
        p = el.get_Parameter(BuiltInParameter.RBS_PIPE_OUTER_DIAMETER)
        if p and p.AsDouble() > 0:
            return p
    except:
        pass

    # Conduit (trade size)
    try:
        p = el.get_Parameter(BuiltInParameter.RBS_CONDUIT_DIAMETER_PARAM)
        if p and p.AsDouble() > 0:
            return p
    except:
        pass

    # Fallback (works in many families)
    try:
        p = el.LookupParameter("Diameter")
        if p and p.AsDouble() > 0:
            return p
    except:
        pass

    # Last fallback (your case)
    try:
        p = el.LookupParameter("Diameter(Trade Size)")
        if p and p.AsDouble() > 0:
            return p
    except:
        pass

    return None


def is_pipe(el):
    if el is None:
        return False
    try:
        if el.Category and el.Category.Id.IntegerValue == int(BuiltInCategory.OST_PipeCurves):
            return True
    except Exception:
        pass
    if has_pipe_diameter_parameter(el):
        return True
    return False


def pick_pipes_prompt():
    refs = uidoc.Selection.PickObjects(ObjectType.Element, "Pick pipe elements (pick multiple, press Esc when done)")
    return [doc.GetElement(r) for r in refs]


def get_pipe_curve_and_mid(pipe):
    loc = getattr(pipe, "Location", None)
    if not loc or not getattr(loc, "Curve", None):
        raise Exception("Selected element has no curve location")
    curve = loc.Curve
    mid = curve.Evaluate(0.5, True)
    return curve, mid


def get_pipe_length(pipe_curve):
    try:
        return pipe_curve.Length
    except Exception:
        p0 = pipe_curve.GetEndPoint(0)
        p1 = pipe_curve.GetEndPoint(1)
        dx = p1.X - p0.X
        dy = p1.Y - p0.Y
        dz = p1.Z - p0.Z
        return math.sqrt(dx*dx + dy*dy + dz*dz)


# ----------------------------
# Select pipes (multi)
# ----------------------------
forms.alert(
    "Trench Modeller started.\n\n"
    "Select pipes for a trench and press Finish.\n"
    "Repeat selection for next trench.\n"
    "Press Esc to stop."
)

while True:
    try:
        pipes = pick_pipes_prompt()
    except Exception:
        # User pressed Esc → exit cleanly
        forms.alert("Trench Modeller finished.")
        break

    if not pipes:
        continue

# ----------------------------
# Collect geometry for all pipes
# ----------------------------
    pipe_infos = []  
    for p in pipes:
        if not (p.Category and p.Category.Id.IntegerValue in [
            int(BuiltInCategory.OST_PipeCurves),
            int(BuiltInCategory.OST_Conduit)
        ]):
            continue

        curve, mid = get_pipe_curve_and_mid(p)
        length = get_pipe_length(curve)

        pdiam_param = get_element_diameter_param(p)

        if not pdiam_param:
            forms.alert("Element missing diameter parameter. Cannot continue.")
            raise Exception("Missing diameter")

        diam = pdiam_param.AsDouble()
        radius = diam / 2.0
        bop = mid.Z - radius
        top = mid.Z + radius

        pipe_infos.append({
            "elem": p,
            "curve": curve,
            "mid": mid,
            "diam": diam,
            "radius": radius,
            "bop": bop,
            "top": top,
            "length": length
        })

    if not pipe_infos:
        forms.alert("No valid pipe geometry found.")
        raise Exception("No valid pipes")

    # ----------------------------
    # Determine shortest pipe (by physical length)
    # ----------------------------
    shortest = min(pipe_infos, key=lambda x: x["length"])
    short_curve = shortest["curve"]
    short_start = short_curve.GetEndPoint(0)
    short_end = short_curve.GetEndPoint(1)

    lowest_bop = min(info["bop"] for info in pipe_infos)

    start = DB.XYZ(short_start.X, short_start.Y, lowest_bop)
    end = DB.XYZ(short_end.X, short_end.Y, lowest_bop)

    # ----------------------------
    # Perpendicular axis for width
    # ----------------------------
    dx = end.X - start.X
    dy = end.Y - start.Y
    len2d = math.hypot(dx, dy)

    if len2d < 1e-9:
        perp_x, perp_y = 0.0, 1.0
    else:
        perp_x = -dy / len2d
        perp_y = dx / len2d

    projections_min = []
    projections_max = []

    for info in pipe_infos:
        m = info["mid"]
        proj = m.X * perp_x + m.Y * perp_y
        projections_min.append(proj - info["radius"])
        projections_max.append(proj + info["radius"])

    min_proj = min(projections_min)
    max_proj = max(projections_max)

    span_internal = max_proj - min_proj
    trench_width = span_internal + mm_to_internal(100.0)   # 50 mm each side

    # ----------------------------
    # Height
    # ----------------------------
    highest_top = max(info["top"] for info in pipe_infos)
    lowest_bop = min(info["bop"] for info in pipe_infos)

    height_value = (highest_top - lowest_bop) + mm_to_internal(50.0)

    # ----------------------------
    # Bottom elevation
    # ----------------------------
    # ----------------------------
    target_bottom_abs = lowest_bop - mm_to_internal(50.0)


    # ----------------------------
    # Shift tray to center of pipes
    # ----------------------------
    start_proj = start.X * perp_x + start.Y * perp_y
    end_proj = end.X * perp_x + end.Y * perp_y
    tray_center_proj = (start_proj + end_proj) / 2.0
    group_center_proj = (min_proj + max_proj) / 2.0
    offset_proj = group_center_proj - tray_center_proj

    shift_dx = offset_proj * perp_x
    shift_dy = offset_proj * perp_y

    start = DB.XYZ(start.X + shift_dx, start.Y + shift_dy, start.Z)
    end = DB.XYZ(end.X + shift_dx, end.Y + shift_dy, end.Z)

    # ----------------------------
    # NEW: Use the pipe's own Reference Level
    # ----------------------------
    pipe_level_param = shortest["elem"].LookupParameter("Reference Level")
    level_for_tray = doc.GetElement(pipe_level_param.AsElementId())


    # ----------------------------
    # Convert absolute BOT to level-relative BOT (FIX)
    # ----------------------------
    level_elev = level_for_tray.Elevation
    target_bottom = target_bottom_abs - level_elev


    # ----------------------------
    # Cable tray type
    # ----------------------------
    tray_types = FilteredElementCollector(doc) \
        .OfCategory(BuiltInCategory.OST_CableTray) \
        .WhereElementIsElementType() \
        .ToElements()

    if not tray_types:
        forms.alert("No Cable Tray types found in project.")
        raise Exception("No Cable Tray Type Found")

    tray_type = tray_types[0]

    # ----------------------------
    # Create Tray
    # ----------------------------
    with revit.Transaction("Create Trench Cable Tray (multi-pipe)"):

        try:
            tray = DB.Electrical.CableTray.Create(doc, tray_type.Id, start, end, level_for_tray.Id)
        except Exception:
            tray = DB.CableTray.Create(doc, tray_type.Id, start, end, level_for_tray.Id)

        # WIDTH
        try:
            width_param = tray.LookupParameter("Width")
            if width_param:
                if width_param.StorageType == StorageType.Double:
                    width_param.Set(trench_width)
                else:
                    width_param.SetValueString(str(round(trench_width * 304.8, 2)))
        except:
            pass

        # HEIGHT
        try:
            height_param = tray.LookupParameter("Height")
            if height_param:
                if height_param.StorageType == StorageType.Double:
                    height_param.Set(height_value)
                else:
                    height_param.SetValueString(str(round(height_value * 304.8, 2)))
        except:
            pass

        # BOTTOM ELEVATION PARAMETER
        try:
            bottom_param = tray.LookupParameter("Lower End Bottom Elevation")
            if bottom_param:
                if bottom_param.StorageType == StorageType.Double:
                    bottom_param.Set(target_bottom)
                else:
                    bottom_param.SetValueString(str(round(target_bottom * 304.8, 2)))
        except:
            pass

    forms.alert("Trench Cable Tray Created Successfully!")
