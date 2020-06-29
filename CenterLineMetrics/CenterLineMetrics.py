import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
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
    parent.contributors = ["SET (chir.set@free.fr)"]
    self.parent.helpText = """
This module plots average diameters around a VMTK centerline model. The graphical plot is more readable for a non-bifurcated centerline.
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
    for i, radius in enumerate(radii):
        distanceArray.SetValue(i, points[i][2])
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
