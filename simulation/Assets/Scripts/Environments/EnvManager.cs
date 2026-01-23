using System.ComponentModel;
using DefaultNamespace;
using ExternalCommunication;
using Ik;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace Environments
{
    public abstract class EnvManager : MonoBehaviour
    {
        public abstract void DoRestart(ResetParameters parameters);
        public abstract void DoRestart();

        public abstract void ApplyParameters(ConfigureParameters parameters);
        public abstract GrpcMessage BuildObservationMessage();

        public abstract void RecieveMessage(GrpcControl control);
        public abstract ArticulationChainComponent GetArticulationChain();

        public abstract void UpdateSync();
    }

    public enum Environment
    {
        [Description("CubeBowl")] EnvCubeBowl = 1,
        [Description("TrashPicking")] EnvTrashPicking = 2,
        [Description("Tableware")] EnvTableware = 3,
        [Description("Spheres")] EnvSpheres = 4
    }


    public static class EnvironmentEnumExtensions
    {
        public static string GetSceneString(this Environment val)
        {
            DescriptionAttribute[] attributes = (DescriptionAttribute[])val
                .GetType()
                .GetField(val.ToString())
                .GetCustomAttributes(typeof(DescriptionAttribute), false);
            return attributes.Length > 0 ? attributes[0].Description : string.Empty;
        }

        public static string GetSceneStringFromParams(ResetParameters val)
        {
            if (val?.EnvCubeBowl != null) return GetSceneString(Environment.EnvCubeBowl);
            if (val?.EnvTableware != null) return GetSceneString(Environment.EnvTableware);
            if (val?.EnvTrashPicking != null) return GetSceneString(Environment.EnvTrashPicking);
            if (val?.EnvSpheres != null) return GetSceneString(Environment.EnvSpheres);
            return GetSceneString(Environment.EnvCubeBowl);
        }

        public static Environment GetEnvironmentFromString(string env)
        {
            if (env.ToLower() == "cubebowl") return Environment.EnvCubeBowl;
            if (env.ToLower() == "trashpicking") return Environment.EnvTrashPicking;
            if (env.ToLower() == "tableware") return Environment.EnvTableware;
            if (env.ToLower() == "spheres") return Environment.EnvSpheres;
            return Environment.EnvCubeBowl;
        }
    }
}