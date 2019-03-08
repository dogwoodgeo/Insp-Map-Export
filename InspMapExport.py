"""
InspMapExport.py
--------------------
Bradley Jones
bjones@dogwoodgeo.com
12/21/2017
-------------------------
Description:
A geoprocessing tool that is used to export a pdf map series for a designated subbasin number.
Parameter 1: Subbasin number
Parameter 2: Destination directory for exported pdf
"""

import arcpy
from arcpy import env
env.overwriteOutput = True
env.workspace = r"PATH\TO\SDE\CONNECTION\File.sde"

mxd = arcpy.mapping.MapDocument("CURRENT")
df = arcpy.mapping.ListDataFrames(mxd, "")[0]

# Variables
subbasinCode = arcpy.GetParameterAsText(0)
exportPath = arcpy.GetParameterAsText(1)
pdfName = "\\" + subbasinCode + ".pdf"
subbasinSelection = "Subbasin " + subbasinCode
mshSelection = "AI Mapsheets"
queryString = "AREA_CODE =" + "'" + subbasinCode + "'"
subbasins = "SDE.SEWERMAN.SUBBASIN"
mapsheets = "SDE.SEWERMAN.QSGRID"
msh = "Mapsheets"
subbasinSymbol = r"PATH\TO\LAYER\FILE\Subbasin_Selection.lyr"
mshSymbol = r"PATH\TO\LAYER\FILE\Mapsheets.lyr"
mshSelectSymbol = r"PATH\TO\LAYER\FILE\AI_Mapsheets.lyr"
mshShapefile = r"PATH\TO\LAYER\FILE\AI_Mapsheets_Chris.shp"

try:
    # Check for Subbasins and AI Sewers layers
    layer_list = arcpy.mapping.ListLayers(mxd, "Subbasins", df)
    layer_list2 = arcpy.mapping.ListLayers(mxd, "AI Sewers", df)
    layer_list3 = arcpy.mapping.ListLayers(mxd, "AI Mapsheets", df)
    if len(layer_list) == 0:
        arcpy.AddError("Subbasins layer not present in ArcMap document.\nSubbasins must be added for tool to function.")

    elif len(layer_list2) == 0:
        arcpy.AddError("AI Sewers layer not present in ArcMap document.\nAI Sewers must be added for tool to function.")

    elif len(layer_list3) == 0:
        arcpy.AddError("AI Mapsheets layer not present in ArcMap document."
                       "\nAI Mapsheets must be added for tool to function.")

    else:
        # Remove existing Subbasin Selection layer
        layerRemove = arcpy.mapping.ListLayers(mxd, "Subbasin *", df)
        if len(layerRemove) == 0:
            arcpy.AddMessage("Previous AI Subbasin selection layer not present.")
        else:
            arcpy.AddMessage("Previous AI Subbasin layer present.")
            for layer in layerRemove:
                arcpy.mapping.RemoveLayer(df, layer)
                arcpy.AddMessage("Previous AI Subbasin layer removed.")

        # Create feature layer based on subbasin selection
        arcpy.MakeFeatureLayer_management(subbasins,
                                          subbasinSelection,
                                          queryString)
        subbasinCount = int(arcpy.GetCount_management(subbasinSelection).getOutput(0))
        if subbasinCount == 0:
            arcpy.AddError("Subbasin AREA_CODE entered resulted in no subbasins returned."
                           "\nVerify AREA_CODE entered is correct.")

        else:
            arcpy.AddMessage("Subbasin selection made.")

            # Apply symbology to subbasin layer
            arcpy.ApplySymbologyFromLayer_management(subbasinSelection, subbasinSymbol)
            arcpy.AddMessage("Symbology applied to subbasin selection.")

            # Add layer to map
            refLayer = arcpy.mapping.ListLayers(mxd, "Mapsheets", df)[0]
            subbasinLayer = arcpy.mapping.Layer(subbasinSelection)
            arcpy.mapping.InsertLayer(df, refLayer, subbasinLayer, "AFTER")

            # Select AI sewers in subbasin
            sewersSelect = arcpy.SelectLayerByLocation_management("AI Sewers",
                                                                  "WITHIN",
                                                                  subbasinSelection,
                                                                  0,
                                                                  "NEW_SELECTION")
            arcpy.AddMessage("AI Sewers associated with subbasin " + subbasinCode + " selected")

            # Select mapsheets and intersect chosen subbasin
            mshSelect = arcpy.SelectLayerByLocation_management("Mapsheets",
                                                               "INTERSECT",
                                                               sewersSelect,
                                                               0,
                                                               "NEW_SELECTION")
            mshCount = arcpy.GetCount_management(mshSelect).getOutput(0)
            arcpy.AddWarning(mshCount + " mapsheet(s) associated with subbasin " + subbasinCode + " AI Sewers selected.")

            # Export selected mapsheets to shapefile
            arcpy.CopyFeatures_management(mshSelect, mshShapefile)
            arcpy.AddMessage("Selected mapsheets associated with subbasin " + subbasinCode + " exported to " + mshShapefile)

            # Clear previous mapsheet selection
            arcpy.SelectLayerByAttribute_management(sewersSelect, "CLEAR_SELECTION")
            arcpy.AddMessage("AI Sewers selection cleared")
            arcpy.SelectLayerByAttribute_management(mshSelect, "CLEAR_SELECTION")
            arcpy.AddMessage("Mapsheets selection cleared")

            # Change subbasin number in layout Text Element
            elm = arcpy.mapping.ListLayoutElements(mxd, "TEXT_ELEMENT")[-1]
            elm.text = "Subbasin:\n" + subbasinCode

            # Refresh map/datadriven pages to update subbasin number in text element and update map extent.
            mxd.dataDrivenPages.refresh()

            # Export mapbook pdf
            mxd.dataDrivenPages.exportToPDF(exportPath + pdfName,
                                            "ALL",
                                            "PDF_SINGLE_FILE")
            arcpy.AddWarning("Mapbook " + subbasinCode + " exported successfully.")

except Exception, e:
    arcpy.AddError(e)
    arcpy.AddError("Take a screen capture of this message and contact Brad Jones in IS for help.")