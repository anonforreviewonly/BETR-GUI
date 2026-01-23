using System.Collections.Generic;
using UnityEngine;

namespace ExternalCommunication
{
    public class GrpcControl
    {
        public float[] angles;
        public bool grasp;
        public bool reset;
        public Vector3? basePosition;
        public Quaternion? baseRotation;
        public bool immobile;
    }

    public class GrpcMessage
    {
        public Dictionary<string, Transform> namedTransforms = new();
        public List<float> floats = new();
        public List<Vector3> vectors = new();
        public List<Transform> transforms = new();
        public List<bool> bools = new();
        public Dictionary<string, string> strings = new ();
    }
}