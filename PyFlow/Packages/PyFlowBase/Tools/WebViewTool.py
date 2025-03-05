from qtpy import QtCore
from qtpy.QtWebEngineWidgets import QWebEngineView
from PyFlow.UI.Tool.Tool import DockTool
		
class WebViewTool(DockTool):
	"""docstring for Table tool."""

	def __init__(self):
		super(WebViewTool, self).__init__()
		self.content = None

	def onShow(self):
		super(WebViewTool, self).onShow()
		self.setMinimumSize(QtCore.QSize(200, 50))
		self.content = QWebEngineView()
		self.content.load(QtCore.QUrl("http://qt-project.org/"))
		self.content.show()
		self.setWidget(self.content)

	@staticmethod
	def isSingleton():
		return False

	@staticmethod
	def defaultDockArea():
		return QtCore.Qt.BottomDockWidgetArea

	@staticmethod
	def toolTip():
		return "Web view"

	@staticmethod
	def name():
		return "Web view"