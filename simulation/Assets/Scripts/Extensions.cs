using System;
using System.Collections.Generic;
using UnityEngine;

public static class Extensions
{
    public static Quaternion ToUnityQuaternion(this Ik.Quaternion vector)
    {
        return new Quaternion(vector.X, vector.Y, vector.Z, vector.W);
    }

    public static Vector3 ToUnityVector(this Ik.Vector3 vector)
    {
        return new Vector3(vector.X, vector.Y, vector.Z);
    }

    // https://gist.github.com/Gustorvo/50fb28e7b348f4a3f74c631891c535bf
    public static Vector3 ToTargetRotationInReducedSpace(this ArticulationBody body, Quaternion targetLocalRotation)
    {
        if (body.isRoot)
            return Vector3.zero;
        Vector3 axis;
        float angle;

        //Convert rotation to angle-axis representation (angles in degrees)
        targetLocalRotation.ToAngleAxis(out angle, out axis);

        // Converts into reduced coordinates and combines rotations (anchor rotation and target rotation)
        Vector3 rotInReducedSpace = Quaternion.Inverse(body.anchorRotation) * axis * angle;

        return rotInReducedSpace;
    }

    public static Vector3 GetRotationInReducedSpace(this ArticulationBody body)
    {
        if (body.isRoot)
            return Vector3.zero;
        Vector3 axis;
        float angle;

        //Convert rotation to angle-axis representation (angles in degrees)
        body.transform.localRotation.ToAngleAxis(out angle, out axis);

        // Converts into reduced coordinates and combines rotations (anchor rotation and target rotation)
        Vector3 rotInReducedSpace = Quaternion.Inverse(body.anchorRotation) * axis * angle;

        return rotInReducedSpace;
    }

    
    public static Vector3 NormalizeVector(this Vector3 vec, float maxValue)
    {
        return Vector3.Max(Vector3.one * -1, Vector3.Min(Vector3.one, vec / maxValue));
    }

    public static float SafeTarget(this ArticulationDrive drive)
    {
        var driveTarget = drive.target;
        if (driveTarget >= drive.upperLimit) driveTarget -= 0.1f;
        if (driveTarget <= drive.lowerLimit) driveTarget += 0.1f;
        return driveTarget;
    }

    public static TSource MinBy<TSource, TValue>(
        this IEnumerable<TSource> source, Func<TSource, TValue> selector)
    {
        using (var iter = source.GetEnumerator())
        {
            if (!iter.MoveNext()) throw new InvalidOperationException("no data");
            var comparer = Comparer<TValue>.Default;
            var minItem = iter.Current;
            var minValue = selector(minItem);
            while (iter.MoveNext())
            {
                var item = iter.Current;
                var value = selector(item);
                if (comparer.Compare(minValue, value) > 0)
                {
                    minItem = item;
                    minValue = value;
                }
            }

            return minItem;
        }
    }
}