using UnityEngine;
using UnityEditor;
using System.Linq;

public class UvAnimPostprocess : AssetPostprocessor
{
	void OnPreprocessModel()
	{
		var modelImporter = assetImporter as ModelImporter;
		if (modelImporter == null) { return; }

		var isChanged     = false;

		if (modelImporter.extraUserProperties.IsNullOrEmpty() == false)
		{
			var beforeExUserPropList = modelImporter.extraUserProperties.ToList();
			// Tex もしくは Map と付くカスタムアトリビュートを一旦全部削除する
			beforeExUserPropList.RemoveAll(p => p.Contains("Tex") || p.Contains("Map"));
			modelImporter.extraUserProperties = beforeExUserPropList.ToArray();
		}

		if (isChanged)
		{
			EditorUtility.SetDirty(modelImporter);
		}
	}

	void OnPostprocessGameObjectWithUserProperties(
		GameObject importedGameObject,
		string[] propNames,
		System.Object[] values)
	{
		var modelImporter  = assetImporter as ModelImporter;
		if (modelImporter == null) { return; }

		var exUserPropList = modelImporter.extraUserProperties.ToList();
		var isChanged      = false;

		for (int i = 0; i < propNames.Length; i++)
		{
			var propName  = propNames[i];
			var propValue = values[i] as string;

			// カスタムアトリビュート名が TargetTexProp から始まっていなければパス
			if (propName.StartsWith("TargetTexProp") == false) { continue; }
			// カスタムアトリビュート値に Tex もしくは Map がついてなければパス
			if (propValue.Contains("Tex") == false && propValue.Contains("Map") == false) { continue; }

			exUserPropList.Add(propValue + "___" + importedGameObject.name);
			isChanged = true;
		}

		if (isChanged)
		{
			modelImporter.extraUserProperties = exUserPropList.ToArray();
			EditorUtility.SetDirty(modelImporter);
		}
	}

	void OnPostprocessGameObjectWithAnimatedUserProperties(
		GameObject importedGameObject,
		EditorCurveBinding[] bindings)
	{
		var modelImporter  = assetImporter as ModelImporter;
		if (modelImporter == null) { return; }

		var exUserPropList = modelImporter.extraUserProperties.ToList();
		var targetPropName = "_MainTex";
		foreach (var exUserProp in exUserPropList)
		{
			// exUserProp の末尾に importedGameObject名 がなければパス
			if (exUserProp.EndsWith(importedGameObject.name) == false) { continue; }

			var underIndexPos = exUserProp.LastIndexOf("___");
			// exUserProp に ___ がなければパス
			if (underIndexPos == -1) { continue; }

			var targetTexProp = exUserProp.Substring(0, underIndexPos);
			targetPropName = targetTexProp;
			break;
		}

		var importedTrans = importedGameObject.transform;
		// ルートの Transform からの相対パスを取得できる（ルートは含まれない）
		var relativePath  = AnimationUtility.CalculateTransformPath(importedTrans, importedTrans.root);

		var isMeshRenderer        = false;
		var isSkinnedMeshRenderer = false;
		var mr = importedGameObject.GetComponents<MeshRenderer>();
		if (mr != null)
		{
			isMeshRenderer = true;
		}
		else
		{
			var smr = importedGameObject.GetComponents<SkinnedMeshRenderer>();
			if (smr != null)
			{
				isSkinnedMeshRenderer = true;
			}
		}

		if (isMeshRenderer == false && isSkinnedMeshRenderer == false) { return; }

		for (var i = 0; i < bindings.Length; i++)
		{
			var propName = bindings[i].propertyName;

			if (propName.StartsWith("uvRepeatAnimU") == false
			&&  propName.StartsWith("uvRepeatAnimV") == false
			&&  propName.StartsWith("uvOffsetAnimU") == false
			&&  propName.StartsWith("uvOffsetAnimV") == false)
			{
				continue;
			}

			bindings[i].path = relativePath;
			if (isMeshRenderer)
			{
				bindings[i].type = typeof(MeshRenderer);
			}
			else if (isSkinnedMeshRenderer)
			{
				bindings[i].type = typeof(SkinnedMeshRenderer);
			}

			// Legacy パイプラインですとメインテクスチャーのプロパティ名は _MainTex ですが、
			// URP では _BaseMap : HDRP では _BaseColorMap となっているので注意（ Unityさん、なぜ統一しない… ）
			if (propName.StartsWith("uvRepeatAnimU"))
			{
				bindings[i].propertyName = "material." + targetPropName + "_ST.x";
			}
			if (propName.StartsWith("uvRepeatAnimV"))
			{
				bindings[i].propertyName = "material." + targetPropName + "_ST.y";
			}
			if (propName.StartsWith("uvOffsetAnimU"))
			{
				bindings[i].propertyName = "material." + targetPropName + "_ST.z";
			}
			if (propName.StartsWith("uvOffsetAnimV"))
			{
				bindings[i].propertyName = "material." + targetPropName + "_ST.w";
			}
		}
	}
}
