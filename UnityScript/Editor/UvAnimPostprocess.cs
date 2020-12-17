using UnityEngine;
using UnityEditor;

public class UvAnimPostprocess : AssetPostprocessor
{
	void OnPostprocessGameObjectWithAnimatedUserProperties(
		GameObject importedGameObject,
		EditorCurveBinding[] bindings)
	{
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

			Debug.Log("PropName = " + propName + " : type = " + bindings[i].type + " : path = " + bindings[i].path);

			bindings[i].path = "";
			bindings[i].type = typeof(MeshRenderer);
			// Legacy パイプラインですとメインテクスチャーのプロパティ名は _MainTex ですが、
			// URP では _BaseMap : HDRP では _BaseColorMap となっているので注意（ Unityさん、なぜ統一しない… ）
			if (propName.StartsWith("uvRepeatAnimU"))
			{
				bindings[i].propertyName = "material._MainTex_ST.x";
			}
			if (propName.StartsWith("uvRepeatAnimV"))
			{
				bindings[i].propertyName = "material._MainTex_ST.y";
			}
			if (propName.StartsWith("uvOffsetAnimU"))
			{
				bindings[i].propertyName = "material._MainTex_ST.z";
			}
			if (propName.StartsWith("uvOffsetAnimV"))
			{
				bindings[i].propertyName = "material._MainTex_ST.w";
			}
		}
	}
}
