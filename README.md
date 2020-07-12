# CenterLineMetrics
A custom Slicer module to plot average diameters of a CMTK centerline model. It is intended for non-bifurcated centerlines.

The diameter distribution can be displayed along the cumulated distance of the centerline, or projected on a selected RAS axis. The latter case allows to identify a 2D view location on the plot's X axis.

**Usage**

Select an input centerline already computed by the [Extract Centerline](https://github.com/vmtk/SlicerExtension-VMTK) module.
Select the distance retrieval mode : cumulative or projected.

In Projected Distance Mode, select an appropriate axis. For most arteries, the S axis is conveniant and is by default selected. For horizontal arteries, like renal or sub-clavian arteries, the R axis is appropriate.

Click on Apply button and the Plot view shows the diameter distribution.

**Acknowledgement**

This module is almost entirely based on the [Line Profile](https://github.com/PerkLab/SlicerSandbox/tree/master/LineProfile) module.


