import sys
from PyQt5 import QtWidgets, QtCore

class ReorderableListModel(QtCore.QAbstractListModel):
    dragDropFinished = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        QtCore.QAbstractItemModel.__init__(self, parent)
        self.nodes = []
        self.lastDroppedItems = []
        self.pendingRemoveRowsAfterDrop = False

    def setNodes(self, nodes):
        self.nodes = nodes

    def getNodes(self):
        return self.nodes

    def rowForItem(self, text):
        try:
            row = self.nodes.index(text)
        except ValueError:
            return None
        return row

    def index(self, row, column, parent):
        if row < 0 or row >= len(self.nodes):
            return QtCore.QModelIndex()
        return self.createIndex(row, column)

    def parent(self, index):
        return QtCore.QModelIndex()

    def rowCount(self, index):
        if index.isValid():
            return 0
        return len(self.nodes)

    def data(self, index, role):
        if not index.isValid():
            return None
        if role == QtCore.Qt.DisplayRole:
            row = index.row()
            if row < 0 or row >= len(self.nodes):
                return None
            return self.nodes[row]
        else:
            return None

    def supportedDropActions(self):
        return QtCore.Qt.MoveAction

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | \
               QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled

    def insertRows(self, row, count, index):
        if index.isValid():
            return False
        if count <= 0:
            return False
        self.beginInsertRows(QtCore.QModelIndex(), row, row + count - 1)
        for i in range(0, count):
            self.nodes.insert(row + i, '')
        self.endInsertRows()
        return True

    def removeRows(self, row, count, index):
        if index.isValid():
            return False
        if count <= 0:
            return False
        num_rows = self.rowCount(QtCore.QModelIndex())
        self.beginRemoveRows(QtCore.QModelIndex(), row, row + count - 1)
        for i in range(count, 0, -1):
            self.nodes.pop(row - i + 1)
        self.endRemoveRows()

        if self.pendingRemoveRowsAfterDrop:
            self.pendingRemoveRowsAfterDrop = False
            self.dragDropFinished.emit()

        return True

    def setData(self, index, value, role):
        if not index.isValid():
            return False
        if index.row() < 0 or index.row() > len(self.nodes):
            return False
        self.nodes[index.row()] = str(value)
        self.dataChanged.emit(index, index)
        return True

    def mimeTypes(self):
        return ['application/vnd.treeviewdragdrop.list']

    def mimeData(self, indexes):
        mimedata = QtCore.QMimeData()
        encoded_data = QtCore.QByteArray()
        stream = QtCore.QDataStream(encoded_data, QtCore.QIODevice.WriteOnly)
        for index in indexes:
            if index.isValid():
                text = self.data(index, 0)
        stream << QtCore.QByteArray(text.encode('utf-8'))
        mimedata.setData('application/vnd.treeviewdragdrop.list', encoded_data)
        return mimedata

    def dropMimeData(self, data, action, row, column, parent):
        if action == QtCore.Qt.IgnoreAction:
            return True
        if not data.hasFormat('application/vnd.treeviewdragdrop.list'):
            return False
        if column > 0:
            return False

        num_rows = self.rowCount(QtCore.QModelIndex())
        if num_rows <= 0:
            return False

        if row < 0:
            if parent.isValid():
                row = parent.row()
            else:
                return False

        encoded_data = data.data('application/vnd.treeviewdragdrop.list')
        stream = QtCore.QDataStream(encoded_data, QtCore.QIODevice.ReadOnly)

        new_items = []
        rows = 0
        while not stream.atEnd():
            text = QtCore.QByteArray()
            stream >> text
            text = bytes(text).decode('utf-8')
            index = self.nodes.index(text)
            new_items.append((text, index))
            rows += 1

        self.lastDroppedItems = []
        for (text, index) in new_items:
            target_row = row
            if index < row:
                target_row += 1
            self.beginInsertRows(QtCore.QModelIndex(), target_row, target_row)
            self.nodes.insert(target_row, text)
            self.endInsertRows()
            self.lastDroppedItems.append(text)
            row += 1

        self.pendingRemoveRowsAfterDrop = True
        return True

class SelectionModel(QtCore.QItemSelectionModel):
    def __init__(self, parent=None):
        QtCore.QItemSelectionModel.__init__(self, parent)

    def onModelItemsReordered(self):
        new_selection = QtCore.QItemSelection()
        new_index = QtCore.QModelIndex()
        for item in self.model().lastDroppedItems:
            row = self.model().rowForItem(item)
            if row is None:
                continue
            new_index = self.model().index(row, 0, QtCore.QModelIndex())
            new_selection.select(new_index, new_index)

        self.clearSelection()
        flags = QtCore.QItemSelectionModel.ClearAndSelect | \
                QtCore.QItemSelectionModel.Rows | \
                QtCore.QItemSelectionModel.Current
        self.select(new_selection, flags)
        self.setCurrentIndex(new_index, flags)
