"""Base package
"""
PACKAGE_NAME = "PyFlowBase"
from collections import OrderedDict

from PyFlow.UI.UIInterfaces import IPackage

# Pins
from PyFlow.Packages.PyFlowBase.Pins.AnyPin import AnyPin
from PyFlow.Packages.PyFlowBase.Pins.BoolPin import BoolPin
from PyFlow.Packages.PyFlowBase.Pins.ExecPin import ExecPin
from PyFlow.Packages.PyFlowBase.Pins.FloatPin import FloatPin
from PyFlow.Packages.PyFlowBase.Pins.IntPin import IntPin
from PyFlow.Packages.PyFlowBase.Pins.StringPin import StringPin

# Function based nodes
from PyFlow.Packages.PyFlowBase.FunctionLibraries.BiitLib import BiitLib
from PyFlow.Packages.PyFlowBase.FunctionLibraries.SimpleITKLib import createSimpleITKNodes

from PyFlow.Packages.PyFlowBase.Nodes.commentNode import commentNode
from PyFlow.Packages.PyFlowBase.Nodes.stickyNote import stickyNote

from PyFlow.Packages.PyFlowBase.Tools.ScreenshotTool import ScreenshotTool
from PyFlow.Packages.PyFlowBase.Tools.NodeBoxTool import NodeBoxTool
from PyFlow.Packages.PyFlowBase.Tools.TableTool import TableTool
from PyFlow.Packages.PyFlowBase.Tools.WebViewTool import WebViewTool
from PyFlow.Packages.PyFlowBase.Tools.WorkflowTool import WorkflowTool
from PyFlow.Packages.PyFlowBase.Tools.ExecutionTool import ExecutionTool
from PyFlow.Packages.PyFlowBase.Tools.HistoryTool import HistoryTool
from PyFlow.Packages.PyFlowBase.Tools.PropertiesTool import PropertiesTool
from PyFlow.Packages.PyFlowBase.Tools.CompileTool import CompileTool
from PyFlow.Packages.PyFlowBase.Tools.LoggerTool import LoggerTool

from PyFlow.Packages.PyFlowBase.Exporters.PythonScriptExporter import (
    PythonScriptExporter,
)

# Factories
from PyFlow.Packages.PyFlowBase.Factories.UIPinFactory import createUIPin
from PyFlow.Packages.PyFlowBase.Factories.PinInputWidgetFactory import getInputWidget
from PyFlow.Packages.PyFlowBase.Factories.UINodeFactory import createUINode

# Prefs widgets
from PyFlow.Packages.PyFlowBase.PrefsWidgets.General import GeneralPreferences
from PyFlow.Packages.PyFlowBase.PrefsWidgets.InputPrefs import InputPreferences
from PyFlow.Packages.PyFlowBase.PrefsWidgets.ThemePrefs import ThemePreferences


_FOO_LIBS = {
    BiitLib.__name__: BiitLib(PACKAGE_NAME),
}


_NODES = {
    commentNode.__name__: commentNode,
    stickyNote.__name__: stickyNote,
}

for biitClass in BiitLib.classes.values():
    _NODES[biitClass.name()] = biitClass

_NODES.update(createSimpleITKNodes())

_PINS = {
    AnyPin.__name__: AnyPin,
    BoolPin.__name__: BoolPin,
    ExecPin.__name__: ExecPin,
    FloatPin.__name__: FloatPin,
    IntPin.__name__: IntPin,
    StringPin.__name__: StringPin,
}

# Toolbar will be created in following order
_TOOLS = OrderedDict()
_TOOLS[CompileTool.__name__] = CompileTool
_TOOLS[ScreenshotTool.__name__] = ScreenshotTool
_TOOLS[PropertiesTool.__name__] = PropertiesTool
_TOOLS[LoggerTool.__name__] = LoggerTool
_TOOLS[HistoryTool.__name__] = HistoryTool
_TOOLS[NodeBoxTool.__name__] = NodeBoxTool
_TOOLS[TableTool.__name__] = TableTool
_TOOLS[WebViewTool.__name__] = WebViewTool
_TOOLS[WorkflowTool.__name__] = WorkflowTool
_TOOLS[ExecutionTool.__name__] = ExecutionTool
try:
    from PyFlow.Packages.PyFlowBase.Tools.ImageViewerTool import ImageViewerTool
    _TOOLS[ImageViewerTool.__name__] = ImageViewerTool
except Exception as e:
    pass

_EXPORTERS = OrderedDict()
_EXPORTERS[PythonScriptExporter.__name__] = PythonScriptExporter


_PREFS_WIDGETS = OrderedDict()
_PREFS_WIDGETS["General"] = GeneralPreferences
_PREFS_WIDGETS["Input"] = InputPreferences
_PREFS_WIDGETS["Theme"] = ThemePreferences


class PyFlowBase(IPackage):
    """Base pyflow package
    """

    def __init__(self):
        super(PyFlowBase, self).__init__()

    @staticmethod
    def GetExporters():
        return _EXPORTERS

    @staticmethod
    def GetFunctionLibraries():
        return _FOO_LIBS

    @staticmethod
    def GetNodeClasses():
        return _NODES
    
    @staticmethod
    def addClass(nodeClassName, nodeClass):
        _NODES[nodeClassName] = nodeClass

    @staticmethod
    def GetPinClasses():
        return _PINS

    @staticmethod
    def GetToolClasses():
        return _TOOLS

    @staticmethod
    def UIPinsFactory():
        return createUIPin

    @staticmethod
    def UINodesFactory():
        return createUINode

    @staticmethod
    def PinsInputWidgetFactory():
        return getInputWidget

    @staticmethod
    def PrefsWidgets():
        return _PREFS_WIDGETS
