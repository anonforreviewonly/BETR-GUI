using DefaultNamespace;
using UnityEngine;

namespace ExternalCommunication
{
    public static class MessageUtils
    {
        public static Transform ToUnity(this Ik.Transform transform)
        {
            var gameObject = new GameObject();
            gameObject.hideFlags = HideFlags.HideAndDontSave;
            gameObject.transform.position = transform.Position.ToUnityVector();
            gameObject.transform.rotation = transform.Euler != null ? Quaternion.Euler(transform.Euler.ToUnityVector()) : transform.Orientation?.ToUnityQuaternion() ?? Quaternion.Euler(Vector3.zero);
            return gameObject.transform;
        }

        public static Ik.Transform BuildWorldTransform(Transform transformUnity)
        {
            Ik.Transform transf = new Ik.Transform();
            transf.Position = BuildVector3(transformUnity.position);
            transf.Euler = BuildVector3(transformUnity.rotation.eulerAngles);
            transf.Orientation = BuildQuaternion(transformUnity.rotation);
            return transf;
        }

        public static Ik.Transform BuildLocalTransform(Transform transformUnity, GameObject parent)
        {
            Ik.Transform transf = new Ik.Transform();
            transf.Position = BuildVector3(parent.transform.InverseTransformPoint(transformUnity.position));
            transf.Euler = BuildVector3(parent.transform.InverseTransformDirection(transformUnity.rotation.eulerAngles));
            transf.Orientation = BuildQuaternion(transformUnity.localRotation);
            return transf;
        }

        public static Ik.Vector3 BuildVector3(this Vector3 position)
        {
            var vector3 = new Ik.Vector3();
            vector3.X = position.x;
            vector3.Y = position.y;
            vector3.Z = position.z;
            return vector3;
        }

        public static Ik.Quaternion BuildQuaternion(this Quaternion quat)
        {
            var quatern = new Ik.Quaternion();
            quatern.X = quat.x;
            quatern.Y = quat.y;
            quatern.Z = quat.z;
            quatern.W = quat.w;
            return quatern;
        }
    }
}