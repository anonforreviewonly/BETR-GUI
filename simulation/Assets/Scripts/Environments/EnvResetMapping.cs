using System;
using System.Collections.Generic;
using ExternalCommunication;
using Ik;
using UnityEngine;
using Quaternion = UnityEngine.Quaternion;
using Transform = Ik.Transform;
using Vector3 = UnityEngine.Vector3;

namespace Environments
{
    public static class EnvResetMapping
    {
        public static void ResetTableWare(EnvTablewareParameters parameters, List<GameObject> objects, UnityEngine.Transform parent)
        {
            var glass = objects.Find(go => go.name == "glass");
            var knife = objects.Find(go => go.name == "knife");
            var fork = objects.Find(go => go.name == "fork");
            var spoon = objects.Find(go => go.name == "spoon");
            var plate = objects.Find(go => go.name == "plate");

            if (parameters.Knife != null) ResetItem(knife, parameters.Knife, parent);
            if (parameters.Fork != null) ResetItem(fork, parameters.Fork, parent);
            if (parameters.Spoon != null) ResetItem(spoon, parameters.Spoon, parent);
            if (parameters.Plate != null) ResetItem(plate, parameters.Plate, parent);
            if (parameters.Glass != null) ResetItem(glass, parameters.Glass, parent);
        }

        public static void ResetTrashPicking(EnvTrashPickingParameters parameters, List<GameObject> objects, UnityEngine.Transform parent)
        {
            var binBlue = objects.Find(go => go.name == "binBlue");
            var binGreen = objects.Find(go => go.name == "binGreen");
            var binYellow = objects.Find(go => go.name == "binYellow");
            var trashFood = objects.Find(go => go.name == "trashFood");
            var trashMetal = objects.Find(go => go.name == "trashMetal");
            var trashPaper = objects.Find(go => go.name == "trashPaper");

            if (parameters.BinBlue != null) ResetItem(binBlue, parameters.BinBlue, parent);
            if (parameters.BinGreen != null) ResetItem(binGreen, parameters.BinGreen, parent);
            if (parameters.BinYellow != null) ResetItem(binYellow, parameters.BinYellow, parent);
            if (parameters.TrashFood != null) ResetItem(trashFood, parameters.TrashFood, parent);
            if (parameters.TrashMetal != null) ResetItem(trashMetal, parameters.TrashMetal, parent);
            if (parameters.TrashPaper != null) ResetItem(trashPaper, parameters.TrashPaper, parent);
        }

        public static void ResetCubeBowl(EnvCubeBowlParameters parameters, List<GameObject> objects, UnityEngine.Transform parent)
        {
            var bowl = objects.Find(go => go.name == "bowl");
            var cubeBlue = objects.Find(go => go.name == "cubeBlue");
            var cubeRed = objects.Find(go => go.name == "cubeRed");
            var cubeGreen = objects.Find(go => go.name == "cubeGreen");
            var cubeYellow = objects.Find(go => go.name == "cubeYellow");

            if (parameters.Bowl != null)
            {
                ResetItem(bowl, parameters.Bowl, parent);
            }
            else
            {
                ResetItem(bowl, new Vector3(0.215f, 0.0629f, 0.705f), parent);
            }

            if (parameters.CubeBlue != null)
            {
                ResetItem(cubeBlue, parameters.CubeBlue, parent);
            }
            else
            {
                ResetItem(cubeBlue, new Vector3(-0.163f, 0.168f, 0.697f), parent);
            }

            if (parameters.CubeRed != null)
            {
                ResetItem(cubeRed, parameters.CubeRed, parent);
            }
            else
            {
                ResetItem(cubeRed, new Vector3(0.034f, 0.169f, 0.697f), parent);
            }

            if (parameters.CubeGreen != null)
            {
                ResetItem(cubeGreen, parameters.CubeGreen, parent);
            }
            else
            {
                ResetItem(cubeGreen, new Vector3(0.182f, 0.168f, 0.697f), parent);
            }

            if (parameters.CubeYellow != null)
            {
                ResetItem(cubeYellow, parameters.CubeYellow, parent);
            }
            else
            {
                ResetItem(cubeYellow, new Vector3(-0.0753f, 0.168f, 0.697f), parent);
            }
        }

        private static void ResetItem(GameObject item, Vector3 pos, UnityEngine.Transform parent)
        {
            var transform = new Transform();
            transform.Position = pos.BuildVector3();
            ResetItem(item, transform, parent);
        }

        private static void ResetItem(GameObject item, Transform transformMsg, UnityEngine.Transform parent)
        {
            var component = item.GetComponent<Rigidbody>();
            if (component != null)
            {
                var transformLocalPosition = transformMsg.Position.ToUnityVector();
                if (transformLocalPosition != Vector3.zero)
                {
                    component.position = parent.TransformPoint(transformLocalPosition);
                }

                component.rotation = transformMsg.Euler != null ? Quaternion.Euler(transformMsg.Euler.ToUnityVector()) : transformMsg.Orientation != null ? transformMsg.Orientation.ToUnityQuaternion() : Quaternion.Euler(Vector3.zero);
                component.linearVelocity = Vector3.zero;
                component.angularVelocity = Vector3.zero;
            }
            else
            {
                var transformLocalPosition = transformMsg.Position.ToUnityVector();
                if (transformLocalPosition != Vector3.zero)
                {
                    item.transform.position = parent.TransformPoint(transformLocalPosition);
                }
                
                item.transform.rotation = transformMsg.Euler != null ? Quaternion.Euler(transformMsg.Euler.ToUnityVector()) : transformMsg.Orientation != null ? transformMsg.Orientation.ToUnityQuaternion() : Quaternion.Euler(Vector3.zero);
            }
        }

        public static void ResetSpheres(EnvSpheresParameters parameters, List<GameObject> objects, UnityEngine.Transform parent)
        {
            var red = objects.Find(go => go.name == "sphereRed");
            var green = objects.Find(go => go.name == "sphereGreen");
            var yellow = objects.Find(go => go.name == "sphereYellow");
            var goal = objects.Find(go => go.name == "goal");

            if (parameters.SphereRed != null) ResetItem(red, parameters.SphereRed, parent);
            if (parameters.SphereGreen != null) ResetItem(green, parameters.SphereGreen, parent);
            if (parameters.SphereYellow != null) ResetItem(yellow, parameters.SphereYellow, parent);
            if (parameters.Goal != null) ResetItem(goal, parameters.Goal, parent);
        }
    }
}