import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import numpy
import logging

"""
  CenterLineMetrics
  This file is almost totally derived from LineProfile.py.
  The core diameter calculation code is poked from VMTK's
  README.md file.
"""

class CenterLineMetrics(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Centerline metrics"
    self.parent.categories = ["Utilities"]
    self.parent.dependencies = []
    parent.contributors = ["SET (Hobbyist)"]
    self.parent.helpText = """
This module plots average diameters around a VMTK centerline model. It is intended for non-bifurcated centerlines.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# CenterLineMetricsWidget
#

class CenterLineMetricsWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    self.logic = CenterLineMetricsLogic()

    # Instantiate and connect widgets ...

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # input model selector
    #
    self.inputModelSelector = slicer.qMRMLNodeComboBox()
    self.inputModelSelector.nodeTypes = ["vtkMRMLModelNode"]
    self.inputModelSelector.selectNodeUponCreation = True
    self.inputModelSelector.addEnabled = False
    self.inputModelSelector.removeEnabled = False
    self.inputModelSelector.noneEnabled = False
    self.inputModelSelector.showHidden = False
    self.inputModelSelector.setMRMLScene(slicer.mrmlScene)
    self.inputModelSelector.setToolTip("Pick the input VMTK centerline.")
    parametersFormLayout.addRow("Input centerline: ", self.inputModelSelector)

    #
    # output table selector
    #
    self.outputTableSelector = slicer.qMRMLNodeComboBox()
    self.outputTableSelector.nodeTypes = ["vtkMRMLTableNode"]
    self.outputTableSelector.addEnabled = True
    self.outputTableSelector.renameEnabled = True
    self.outputTableSelector.removeEnabled = True
    self.outputTableSelector.noneEnabled = True
    self.outputTableSelector.showHidden = False
    self.outputTableSelector.setMRMLScene( slicer.mrmlScene )
    self.outputTableSelector.setToolTip( "Pick the output table to the algorithm." )
    parametersFormLayout.addRow("Output table: ", self.outputTableSelector)

    #
    # output plot selector
    #
    self.outputPlotSeriesSelector = slicer.qMRMLNodeComboBox()
    self.outputPlotSeriesSelector.nodeTypes = ["vtkMRMLPlotSeriesNode"]
    self.outputPlotSeriesSelector.addEnabled = True
    self.outputPlotSeriesSelector.renameEnabled = True
    self.outputPlotSeriesSelector.removeEnabled = True
    self.outputPlotSeriesSelector.noneEnabled = True
    self.outputPlotSeriesSelector.showHidden = False
    self.outputPlotSeriesSelector.setMRMLScene( slicer.mrmlScene )
    self.outputPlotSeriesSelector.setToolTip( "Pick the output plot series to the algorithm." )
    parametersFormLayout.addRow("Output plot series: ", self.outputPlotSeriesSelector)
    
    #
    # Distance mode selector
    #
    self.distModeWidget = qt.QWidget()
    self.distModeLayout = qt.QHBoxLayout()
    self.distModeGroup = ctk.ctkButtonGroup(self.distModeWidget)
    self.radioCumulative = qt.QRadioButton()
    self.radioProjected = qt.QRadioButton()
    self.radioCumulative.setText("Cumulative")
    self.radioProjected.setText("Projected")
    self.distModeLayout.addWidget(self.radioCumulative)
    self.distModeLayout.addWidget(self.radioProjected)
    self.distModeGroup.addButton(self.radioCumulative)
    self.distModeGroup.addButton(self.radioProjected)
    self.distModeWidget.setLayout(self.distModeLayout)
    self.radioProjected.setChecked(True)
    self.radioCumulative.setToolTip("Cumulative distance along the centerline")
    self.radioProjected.setToolTip("Projected distance on the selected axis. This allows to locate a point in a 2D view.")
    parametersFormLayout.addRow("Distance mode: ", self.distModeWidget)
    
    #
    # Axis selector
    # https://cpp.hotexamples.com/it/examples/-/-/spy3/cpp-spy3-function-examples.html
    #
    self.axisWidget = qt.QWidget()
    self.rasLayout = qt.QHBoxLayout()
    self.group = ctk.ctkButtonGroup(self.axisWidget)
    self.radioR = qt.QRadioButton()
    self.radioA = qt.QRadioButton()
    self.radioS = qt.QRadioButton()
    self.radioR.setText("R")
    self.radioA.setText("A")
    self.radioS.setText("S")
    self.rasLayout.addWidget(self.radioR)
    self.rasLayout.addWidget(self.radioA)
    self.rasLayout.addWidget(self.radioS)
    self.group.addButton(self.radioR)
    self.group.addButton(self.radioA)
    self.group.addButton(self.radioS)
    self.axisWidget.setLayout(self.rasLayout)
    self.radioS.setChecked(True) # Default to superior
    self.radioR.setToolTip("X axis")
    self.radioA.setToolTip("Z axis")
    self.radioS.setToolTip("Y axis")
    parametersFormLayout.addRow("Axis: ", self.axisWidget)
    
    #
    # Apply Button
    #
    self.applyButton = ctk.ctkPushButton()
    self.applyButton.text = "Compute diameters"
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    parametersFormLayout.addRow(self.applyButton)

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.inputModelSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelectNode)
    self.outputPlotSeriesSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelectNode)
    self.outputTableSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelectNode)
    self.radioR.connect("clicked()", self.onRadioR)
    self.radioA.connect("clicked()", self.onRadioA)
    self.radioS.connect("clicked()", self.onRadioS)
    self.radioCumulative.connect("clicked()", self.onRadioCumulative)
    self.radioProjected.connect("clicked()", self.onRadioProjected)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelectNode()

  def cleanup(self):
      return

  def onSelectNode(self):
    self.applyButton.enabled = self.inputModelSelector.currentNode()
    self.logic.setInputModelNode(self.inputModelSelector.currentNode())
    self.logic.setOutputTableNode(self.outputTableSelector.currentNode())
    self.logic.setOutputPlotSeriesNode(self.outputPlotSeriesSelector.currentNode())

  def createOutputNodes(self):
    if not self.outputTableSelector.currentNode():
      outputTableNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode")
      self.outputTableSelector.setCurrentNode(outputTableNode)
    if not self.outputPlotSeriesSelector.currentNode():
      outputPlotSeriesNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotSeriesNode")
      self.outputPlotSeriesSelector.setCurrentNode(outputPlotSeriesNode)

  def onApplyButton(self):
    self.createOutputNodes()
    self.logic.update()
  
  def onRadioR(self):
    self.group.setId(self.radioR, 0)
    self.logic.setAxis(self.group.id(self.radioR)) # Why not pass 0 ?
    
  def onRadioA(self):
    self.group.setId(self.radioA, 1)
    self.logic.setAxis(self.group.id(self.radioA))
    
  def onRadioS(self):
    self.group.setId(self.radioS, 2)
    self.logic.setAxis(self.group.id(self.radioS))
    
  def onRadioCumulative(self):
    self.axisWidget.hide()
    self.logic.distanceMode = 0

  def onRadioProjected(self):
    self.axisWidget.show()
    self.logic.distanceMode = 1
#
# CenterLineMetricsLogic
#

class CenterLineMetricsLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self):
    self.inputModelNode = None
    self.outputPlotSeriesNode = None
    self.outputTableNode = None
    self.plotChartNode = None
    self.axis = 2 # Default to vertical
    self.distanceMode = 1 # Default to projected

  def __del__(self):
      return

  def setInputModelNode(self, modelNode):
    if self.inputModelNode == modelNode:
      return
    self.inputModelNode = modelNode

  def setOutputTableNode(self, tableNode):
    if self.outputTableNode == tableNode:
      return
    self.outputTableNode = tableNode

  def setOutputPlotSeriesNode(self, plotSeriesNode):
    if self.outputPlotSeriesNode == plotSeriesNode:
      return
    self.outputPlotSeriesNode = plotSeriesNode
    
  def setAxis(self, selAxis):
    self.axis = selAxis

  def update(self):
    self.updateOutputTable(self.inputModelNode, self.outputTableNode)
    self.updatePlot(self.outputPlotSeriesNode, self.outputTableNode, self.inputModelNode.GetName())
    self.showPlot()

  def getArrayFromTable(self, outputTable, arrayName):
    distanceArray = outputTable.GetTable().GetColumnByName(arrayName)
    if distanceArray:
      return distanceArray
    newArray = vtk.vtkDoubleArray()
    newArray.SetName(arrayName)
    outputTable.GetTable().AddColumn(newArray)
    return newArray

  def updateOutputTable(self, inputModel, outputTable):

    # Create arrays of data
    distanceArray = self.getArrayFromTable(outputTable, DISTANCE_ARRAY_NAME)
    diameterArray = self.getArrayFromTable(outputTable, DIAMETER_ARRAY_NAME)

    # From VMTK README.md
    points = slicer.util.arrayFromModelPoints(inputModel)
    radii = slicer.util.arrayFromModelPointData(inputModel, 'Radius')
    outputTable.GetTable().SetNumberOfRows(radii.size)
    if self.distanceMode == 0:
        cumArray = vtk.vtkDoubleArray()
        self.cumulateDistances(points, cumArray)
    for i, radius in enumerate(radii):
        if self.distanceMode != 0:
            distanceArray.SetValue(i, points[i][self.axis])
        else:
            distanceArray.SetValue(i, cumArray.GetValue(i))
        diameterArray.SetValue(i, radius * 2)
    distanceArray.Modified()
    diameterArray.Modified()
    outputTable.GetTable().Modified()

  def updatePlot(self, outputPlotSeries, outputTable, name=None):

    # Create plot
    if name:
      outputPlotSeries.SetName(name)
    outputPlotSeries.SetAndObserveTableNodeID(outputTable.GetID())
    outputPlotSeries.SetXColumnName(DISTANCE_ARRAY_NAME)
    outputPlotSeries.SetYColumnName(DIAMETER_ARRAY_NAME)
    outputPlotSeries.SetPlotType(slicer.vtkMRMLPlotSeriesNode.PlotTypeScatter)
    outputPlotSeries.SetMarkerStyle(slicer.vtkMRMLPlotSeriesNode.MarkerStyleNone)
    outputPlotSeries.SetColor(0, 0.6, 1.0)

  def showPlot(self):

    # Create chart and add plot
    if not self.plotChartNode:
      plotChartNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLPlotChartNode")
      self.plotChartNode = plotChartNode
      self.plotChartNode.SetXAxisTitle(DISTANCE_ARRAY_NAME+" (mm)")
      self.plotChartNode.SetYAxisTitle(DIAMETER_ARRAY_NAME+" (mm)")
      self.plotChartNode.AddAndObservePlotSeriesNodeID(self.outputPlotSeriesNode.GetID())

    # Show plot in layout
    slicer.modules.plots.logic().ShowChartInLayout(self.plotChartNode)
    slicer.app.layoutManager().plotWidget(0).plotView().fitToContent()
    
  def cumulateDistances(self, arrPoints, cumArray):
    cumArray.SetNumberOfValues(arrPoints.size)
    previous = arrPoints[0]
    dist = 0
    for i, point in enumerate(arrPoints):
      # https://stackoverflow.com/questions/1401712/how-can-the-euclidean-distance-be-calculated-with-numpy
      dist += numpy.linalg.norm(point - previous)
      cumArray.SetValue(i, dist)
      previous = point

class CenterLineMetricsTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_CenterLineMetrics1()

  def test_CenterLineMetrics1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import SampleData
    sampleDataLogic = SampleData.SampleDataLogic()
    modelNode = sampleDataLogic.downloadMRHead()

    logic = CenterLineMetricsLogic()

    self.delayDisplay('Test passed!')

DISTANCE_ARRAY_NAME = "Distance"
DIAMETER_ARRAY_NAME = "Diameter"
