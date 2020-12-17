# -*- coding: utf-8 -*-

"""
こちらの記事の内容(少し異なる部分もあり)をPythonのみで再現してみる

MayaからUnityへのUVアニメーションエクスポート - SEGA TECH Blog
http://techblog.sega.jp/entry/2018/02/26/100000

===================================================================================================
参考サイト

[OpenMaya] Attributeを作成する | Reincarnation+
http://flame-blaze.net/archives/2516

Christian López Barrón - Building an animation exporter with the Maya Python API 2.0
http://blog.christianlb.io/creating-an-animation-exporter-with-the-maya-api
"""

from __future__ import unicode_literals, print_function

import maya.cmds as mc
import maya.api.OpenMaya as om2
import maya.api.OpenMayaAnim as oma2

from functools import partial

maya_useNewAPI          = True

# =================================================================================================
# Callback ID
exportStarted_ID        = None
afterExport_ID          = None

# =================================================================================================
# OptionVar
doMainActionKey         = "kkUvAnimationExport_doAction"
doCopyNodeKey           = "kkUvAnimationExport_doCopyNode"
doRemoveNodeKey         = "kkUvAnimationExport_doRemoveNode"

# =================================================================================================
# Window Menu Path / Name
testMenuName            = "TestMenu"
testMenuPath            = "MayaWindow|" + testMenuName
menuName                = "UvAnimationExport"
menuPath                = testMenuPath + "|" + menuName
optionWinName           = "UvAnimationExportOption"
copyNodeOptionPath      = "kkUvAnimationExport_copyNodeOptionPath"
removeNodeOptionPath    = "kkUvAnimationExport_removeNodeOptionPath"

# =================================================================================================
# Attribute / Node Name
targetOffsetUAttrName   = "offsetU"
targetOffsetVAttrName   = "offsetV"
targetRepeatUAttrName   = "repeatU"
targetRepeatVAttrName   = "repeatV"

baseOffsetAnimUAttrName = "uvOffsetAnimU"
baseOffsetAnimVAttrName = "uvOffsetAnimV"
baseRepeatAnimUAttrName = "uvRepeatAnimU"
baseRepeatAnimVAttrName = "uvRepeatAnimV"

copyOffsetAnimUNodeName = "copiedOffsetU"
copyOffsetAnimVNodeName = "copiedOffsetV"
copyRepeatAnimUNodeName = "copiedRepeatU"
copyRepeatAnimVNodeName = "copiedRepeatV"

# =================================================================================================


def initializePlugin(plugin):
	if mc.about(uiLanguage=True) == "ja_JP":
		topMenuLabel = u"テスト メニュー"
		menuLabel    = u"書き出し時にUVアニメーションをカスタムアトリビュートに"
	else:
		topMenuLabel = "Test Menu"
		menuLabel    = "UV animation convert to custom attributes"

	try:
		if not mc.about(batch=True):
			mc.menu(testMenuName, label=topMenuLabel, parent="MayaWindow", tearOff=True)

			checkBoxVal = False
			if mc.optionVar(exists=doMainActionKey) == True:
				checkBoxVal = mc.optionVar(q=doMainActionKey)

			mc.menuItem(
				menuName,
				parent=testMenuPath,
				label=menuLabel,
				checkBox=checkBoxVal,
				command=changeCheckBox)
			mc.menuItem(optionBox=True, command=showOptionBox)

			# すでに存在していた場合は initializePlugin でも実行してCallbackを追加しておく
			if mc.optionVar(exists=doMainActionKey) == True and checkBoxVal == True:
				changeCheckBox()

			setDefaultOptionVar()
	except:
		mc.warning("kkUvAnimationExport : it could not add menuItem...")


def uninitializePlugin(plugin):
	try:
		if mc.menuItem(menuPath, exists=True):
			mc.deleteUI(menuPath, menuItem=True)

		if mc.menu(testMenuPath, exists=True):
			mc.deleteUI(testMenuPath, menu=True)

		removeCallbackEvents()

		if mc.window(optionWinName, ex=True):
			mc.deleteUI(optionWinName)
	except:
		mc.warning("kkUvAnimationExport : it could not delete menuItem...")


def changeCheckBox(*args):
	doEvent = mc.menuItem(menuPath, q=True, checkBox=True)

	mc.optionVar(intValue=(doMainActionKey, 1 if doEvent else 0))

	if doEvent == True:
		global exportStarted_ID
		exportStarted_ID = om2.MSceneMessage.addCallback(om2.MSceneMessage.kExportStarted, partial(uvAnimationExport, True))
		global afterExport_ID
		afterExport_ID   = om2.MSceneMessage.addCallback(om2.MSceneMessage.kAfterExport, partial(uvAnimationExport, False))
	else:
		removeCallbackEvents()


def removeCallbackEvents():
	global exportStarted_ID
	if not exportStarted_ID is None:
		om2.MMessage.removeCallback(exportStarted_ID)
		exportStarted_ID = None

	global afterExport_ID
	if not afterExport_ID is None:
		om2.MMessage.removeCallback(afterExport_ID)
		afterExport_ID   = None


def setCheckOptionVar(*args):
	mc.optionVar(intValue=(doRemoveNodeKey, mc.checkBox(removeNodeOptionPath, q=True, value=True)))
	mc.optionVar(intValue=(doCopyNodeKey, mc.checkBox(copyNodeOptionPath, q=True, value=True)))


def showOptionBox(*args):
	if mc.window(optionWinName, ex=True):
		mc.deleteUI(optionWinName)

	window = mc.window(
				optionWinName,
				title="UV Animation Export Options",
				width=400,
				height=80,
				maximizeButton=False)

	mc.columnLayout(adjustableColumn=True)

	mc.text(label="")

	if mc.about(uiLanguage=True) == "ja_JP":
		removeNodeOptionLabel = u"出力時に設定したカスタムアトリビュートを出力後に削除します"
		copyNodeOptionLabel   = u"UVアニメーションノードを複製します ( OFFの場合は使い回します )"
	else:
		removeNodeOptionLabel = "Remove custom attribute that set before output after output"
		copyNodeOptionLabel   = "Copy uv animation node ( When it is OFF, reuse animation node )"

	mc.checkBox(
		removeNodeOptionPath,
		label=removeNodeOptionLabel,
		value=mc.optionVar(q=doRemoveNodeKey),
		changeCommand=setCheckOptionVar)

	mc.text(label="")

	mc.checkBox(
		copyNodeOptionPath,
		label=copyNodeOptionLabel,
		value=mc.optionVar(q=doCopyNodeKey),
		changeCommand=setCheckOptionVar)

	mc.setParent("..")
	mc.showWindow(window)


def setDefaultOptionVar():
	"""[summary]
	OptionVar が存在しなかった場合にデフォルト値をセットしておく
	"""
	if not mc.optionVar(exists=doRemoveNodeKey):
		mc.optionVar(intValue=(doRemoveNodeKey, 1))

	if not mc.optionVar(exists=doCopyNodeKey):
		mc.optionVar(intValue=(doCopyNodeKey, 0))


def getChildrenInSelection():
	selList = om2.MGlobal.getActiveSelectionList()
	childrenList = []
	for i in range(selList.length()):
		mObject = selList.getDependNode(i)
		childrenList.append(mObject) # 選択しているノード自体も追加
		childrenList.extend(getChildrenRecursively(mObject))

	return childrenList


def getChildrenRecursively(mObject):
	dagNode = om2.MFnDagNode(mObject)
	tmpChildrenList = []
	for i in range(dagNode.childCount()):
		child = dagNode.child(i)
		if not child.hasFn(om2.MFn.kTransform):
			continue

		tmpChildrenList.append(child)

		childDagNode = om2.MFnDagNode(child)
		if childDagNode.childCount() > 0:
			tmpChildrenList.extend(getChildrenRecursively(child))

	return tmpChildrenList


def uvAnimationExport(isStartEvent, *args):
	targetObjs = getChildrenInSelection()

	if len(targetObjs) == 0:
		mc.warning("UvAnimationExport : Nothing select..."),
		return

	for target in targetObjs:
		mDagPath  = getDagPathFromMObject(target)
		fnDepNode = om2.MFnDependencyNode(target)

		# メッシュがなければパス
		if not mDagPath.hasFn(om2.MFn.kMesh):
			continue

		mesh = om2.MFnMesh(mDagPath) 
		shadingEngines, polyindeces = mesh.getConnectedShaders(mDagPath.instanceNumber())

		# メッシュに割り当てられているマテリアル
		for sg in shadingEngines:
			matNode = getMaterialNode(sg)
			if matNode is None:
				continue

			p2tNode = getPlace2dTextureNode(sg)
			if p2tNode is None:
				continue

			if isStartEvent == True:
				getSetAnim(targetOffsetUAttrName, baseOffsetAnimUAttrName, copyOffsetAnimUNodeName, fnDepNode, matNode, p2tNode)
				getSetAnim(targetOffsetVAttrName, baseOffsetAnimVAttrName, copyOffsetAnimVNodeName, fnDepNode, matNode, p2tNode)
				getSetAnim(targetRepeatUAttrName, baseRepeatAnimUAttrName, copyRepeatAnimUNodeName, fnDepNode, matNode, p2tNode)
				getSetAnim(targetRepeatVAttrName, baseRepeatAnimVAttrName, copyRepeatAnimVNodeName, fnDepNode, matNode, p2tNode)
			else:
				removeAnim(baseOffsetAnimUAttrName, copyOffsetAnimUNodeName, fnDepNode, matNode)
				removeAnim(baseOffsetAnimVAttrName, copyOffsetAnimVNodeName, fnDepNode, matNode)
				removeAnim(baseRepeatAnimUAttrName, copyRepeatAnimUNodeName, fnDepNode, matNode)
				removeAnim(baseRepeatAnimVAttrName, copyRepeatAnimVNodeName, fnDepNode, matNode)


def getSetAnim(srcAttrName, dstBaseAttrName, animBaseNodeName, fnDepNode, matNode, p2tNode):
	"""[summary]
	Arguments:
		srcAttrName {str} -- source attribute name
		dstBaseAttrName {str} -- destination attribute base name
		animBaseNodeName {str} -- animation node's base name
		fnDepNode {MFnDependencyNode} -- target node
		matNode {MFnDependencyNode} -- material node
		p2tNode {MFnDependencyNode} -- place2dTexture node
	"""
	if p2tNode.hasAttribute(srcAttrName) == False:
		return

	newAttrName = dstBaseAttrName + "_" + matNode.name()

	if not fnDepNode.hasAttribute(newAttrName):
		# attribute.createの引数 (longName, shortName, Type, defaultValue)
		attrObj = om2.MObject()
		newAttr = om2.MFnNumericAttribute()
		attrObj = newAttr.create(newAttrName, newAttrName, om2.MFnNumericData.kFloat, 0.0)
		# create後じゃないと設定できない
		newAttr.writable = True
		newAttr.keyable  = True
		fnDepNode.addAttribute(attrObj)
	dstAttrPlug = fnDepNode.findPlug(newAttrName, False)

	copyAnimNodeName = animBaseNodeName + "_" + matNode.name()

	if fnDepNode.hasAttribute(newAttrName):
		srcAttrPlug = p2tNode.findPlug(srcAttrName, False)
		srcAnimNode = srcAttrPlug.source().node()
		copyAnimObj   = None
		copyAnimCurve = None
		# MGlobal.getSelectionListByName() は mc.ls() と違い、何も取得できなかった場合にエラーになるので、try文の中で取得を検証
		try:
			animNodeList  = om2.MGlobal.getSelectionListByName(copyAnimNodeName)
			copyAnimObj   = animNodeList.getDependNode(0)
			copyAnimCurve = oma2.MFnAnimCurve(copyAnimObj)
		except:
			pass

		if mc.optionVar(q=doCopyNodeKey):
			if copyAnimCurve is None:
				# dstAttrPlug に接続されている MPlugArrayを 取得
				plugs = dstAttrPlug.connectedTo(True, False)
				# すでに srcAttrPlug が接続されているのかを確認
				hasConnected = False
				for p in plugs:
					if p == srcAttrPlug:
						hasConnected = True
						break

				# すでに接続されていた場合は切断しておく（別のものが接続されている場合、MFnAnimCurve.create()でエラーが出る）
				if hasConnected == True:
					mod = om2.MDGModifier()
					mod.disconnect(srcAttrPlug, dstAttrPlug)
					mod.doIt()

				copyAnimCurve = oma2.MFnAnimCurve()
				copyAnimCurve.create(dstAttrPlug, oma2.MFnAnimCurve.kAnimCurveTU)
				copyAnimCurve.setName(copyAnimNodeName)

			srcAnimData = getAnimData(srcAnimNode)
			setAnimData(copyAnimCurve, srcAnimData)
		else:
			if copyAnimCurve is not None:
				mod = om2.MDGModifier()
				mod.deleteNode(copyAnimObj)
				mod.doIt()

			mod = om2.MDGModifier()
			mod.connect(srcAttrPlug, dstAttrPlug)
			mod.doIt()


def removeAnim(dstBaseAttrName, animBaseNodeName, fnDepNode, matNode):
	"""[summary]
	Arguments:
		dstBaseAttrName {str} -- destination attribute base name
		animBaseNodeName {str} -- animation node's base name
		fnDepNode {MFnDependencyNode} -- target node
		matNode {MFnDependencyNode} -- material node
	"""
	# Remove Node Option が OFF だったら削除しない
	if not mc.optionVar(q=doRemoveNodeKey):
		return

	newAttrName = dstBaseAttrName + "_" + matNode.name()
	dstAttrPlug = fnDepNode.findPlug(newAttrName, False)

	# アトリビュートを削除する
	# ※ OpenMaya の removeAttribute() で削除するとなぜかMayaが落ちる（ API 1.0, 2.0 どちらも ）ので、
	#    仕方なく maya.cmds の deleteAttr() を使用
	# if fnDepNode.hasAttribute(newAttrName):
	# 	fnDepNode.removeAttribute(dstAttrPlug.node())
	mc.deleteAttr(dstAttrPlug.name())

	copyAnimNodeName = animBaseNodeName + "_" + matNode.name()

	if mc.optionVar(q=doCopyNodeKey):
		animNodeList = None
		try:
			animNodeList = om2.MGlobal.getSelectionListByName(copyAnimNodeName)
		except:
			pass

		if animNodeList is not None:
			mod = om2.MDGModifier()
			mod.deleteNode(animNodeList.getDependNode(0))
			mod.doIt()


def getDagPathFromMObject(mObject):
	"""[summary]

	Arguments:
		mObject {MObject} -- [description]

	Returns:
		[MDagPath] -- [description]
	"""
	dagNode = om2.MFnDagNode(mObject)
	dagPath = dagNode.getPath()
	return dagPath


def getMaterialNode(sgObj):
	"""[summary]

	Arguments:
		sgObj {MObject} -- shadingEngine object

	Returns:
		[MFnDependencyNode] -- material dependency node
	"""
	sgDepNode      = om2.MFnDependencyNode(sgObj)
	shaderPlugNode = sgDepNode.findPlug("surfaceShader", False)
	matDepNode     = None

	if not shaderPlugNode is None:
		matObj     = shaderPlugNode.source().node()
		matDepNode = om2.MFnDependencyNode(matObj)

	return matDepNode


def getPlace2dTextureNode(sgObj):
	"""[summary]

	Arguments:
		sgObj {MObject} -- shadingEngine object

	Returns:
		[MFnDependencyNode] -- place2dTexture node
	"""
	p2dDepNode         = None
	mItDependencyGraph = om2.MItDependencyGraph(
							sgObj,
							om2.MItDependencyGraph.kUpstream,
							om2.MItDependencyGraph.kPlugLevel)

	while not mItDependencyGraph.isDone():
		currentNode = mItDependencyGraph.currentNode()
		if currentNode.apiType() == om2.MFn.kPlace2dTexture:
			p2dDepNode = om2.MFnDependencyNode(currentNode)
			break
		mItDependencyGraph.next()

	return p2dDepNode


def getAnimData(animCurveNode):
	"""[summary]

	Arguments:
		animCurveNode {MObject} -- animation curve node

	Returns:
		[dict] -- animation data dictionary
	"""
	if animCurveNode is None or not animCurveNode.hasFn(om2.MFn.kAnimCurve):
		return None

	animCurve = oma2.MFnAnimCurve(animCurveNode)

	animDataDict = {}
	keyFrameDict = {}

	# animDataDict["animCurveType"]    = animCurve.animCurveType
	# animDataDict["isStatic"]         = animCurve.isStatic
	# animDataDict["isTimeInput"]      = animCurve.isTimeInput
	# animDataDict["isUnitlessInput"]  = animCurve.isUnitlessInput
	animDataDict["isWeighted"]       = animCurve.isWeighted
	animDataDict["postInfinityType"] = animCurve.postInfinityType
	animDataDict["preInfinityType"]  = animCurve.preInfinityType

	for i in range(animCurve.numKeys):
		keyFrameDict[i]                   = {}
		keyFrameDict[i]["time"]           = animCurve.input(i).value
		keyFrameDict[i]["value"]          = animCurve.value(i)

		# keyFrameDict[i]["inTangentXY"]    = animCurve.getTangentXY(i, True)
		# keyFrameDict[i]["outTangentXY"]   = animCurve.getTangentXY(i, False)
		keyFrameDict[i]["inTangentAW"]    = animCurve.getTangentAngleWeight(i, True)
		keyFrameDict[i]["outTangentAW"]   = animCurve.getTangentAngleWeight(i, False)
		keyFrameDict[i]["inTangentType"]  = animCurve.inTangentType(i)
		keyFrameDict[i]["outTangentType"] = animCurve.outTangentType(i)
		keyFrameDict[i]["isBreakdown"]    = animCurve.isBreakdown(i)
		keyFrameDict[i]["tangentsLocked"] = animCurve.tangentsLocked(i)
		keyFrameDict[i]["weightsLocked"]  = animCurve.weightsLocked(i)

	animDataDict["keyFrames"] = keyFrameDict
	return animDataDict


def setAnimData(animCurve, animDataDict):
	"""[summary]

	Arguments:
		animCurve {MFnAnimCurve} -- anination curve object
		animDataDict {dict} -- animation data dictionary
	"""

	if animCurve is None or animDataDict is None or len(animDataDict) == 0:
		mc.warning("UvAnimationExport : setAnimData - animCurve is None...")
		return

	# まずすでに設定されているキーがあれば削除しておく
	if animCurve.numKeys > 0:
		for i in reversed(range(animCurve.numKeys)):
			animCurve.remove(i)

	if not animDataDict["isWeighted"] is None:
		animCurve.setIsWeighted(animDataDict["isWeighted"])
	if not animDataDict["postInfinityType"] is None:
		animCurve.setPostInfinityType(animDataDict["postInfinityType"])
	if not animDataDict["preInfinityType"] is None:
		animCurve.setPreInfinityType(animDataDict["preInfinityType"])

	keyFrames = animDataDict["keyFrames"]
	if keyFrames is None or len(keyFrames) == 0:
		return

	for index, keyFrameData in keyFrames.items():
		if not keyFrameData["time"] is None and not keyFrameData["value"] is None:
			animCurve.addKey(om2.MTime(keyFrameData["time"], om2.MTime.uiUnit()), keyFrameData["value"])

		if not keyFrameData["isBreakdown"] is None:
			animCurve.setIsBreakdown(index, keyFrameData["isBreakdown"])
		if not keyFrameData["tangentsLocked"] is None:
			animCurve.setTangentsLocked(index, keyFrameData["tangentsLocked"])
		if not keyFrameData["weightsLocked"] is None:
			animCurve.setWeightsLocked(index, keyFrameData["weightsLocked"])

		if not keyFrameData["inTangentAW"] is None:
			inTangentAngle, inTangentWeight = keyFrameData["inTangentAW"]
			animCurve.setTangent(index, inTangentAngle, inTangentWeight, True)

		if not keyFrameData["outTangentAW"] is None:
			outTangentAngle, outTangentWeight = keyFrameData["outTangentAW"]
			animCurve.setTangent(index, outTangentAngle, outTangentWeight, False)

		# animCurve.setInTangentType(index, keyFrameData["inTangentType"])
		# inTangentX, inTangentY = keyFrameData["inTangentXY"]
		# animCurve.setTangent(index, inTangentX, inTangentY, True)
		# print("inTangentX = %s : inTangentY = %s : inTangentType = %s"%(inTangentX, inTangentY, keyFrameData["inTangentType"]))

		# animCurve.setOutTangentType(index, keyFrameData["outTangentType"])
		# outTangentX, outTangentY = keyFrameData["outTangentXY"]
		# animCurve.setTangent(index, outTangentX, outTangentY, False)
		# print("outTangentX = %s : outTangentY = %s : outTangentType = %s"%(outTangentX, outTangentY, keyFrameData["outTangentType"]))
