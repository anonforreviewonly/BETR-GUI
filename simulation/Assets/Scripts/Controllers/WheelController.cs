using Ik;
using UnityEngine;
using UnityEngine.Serialization;

namespace Controllers
{
    public class WheelController : MonoBehaviour
    {
        public ArticulationBody leftWheel;
        public ArticulationBody rightWheel;
        public ArticulationBody robotBase;
        [FormerlySerializedAs("wheelMultiplier")] public float wheelBaseTorque = 750;

        public void ApplyControls(float left, float right)
        {
            left = Mathf.Clamp(left, -1f, 1f);
            right = Mathf.Clamp(right, -1f, 1f);
            leftWheel.SetDriveTargetVelocity(ArticulationDriveAxis.X, left * wheelBaseTorque);
            rightWheel.SetDriveTargetVelocity(ArticulationDriveAxis.X, right * wheelBaseTorque);
        }


        public void ApplyConfiguration(WheelParameters parametersWheelParameters)
        {
            wheelBaseTorque = parametersWheelParameters.Torque;
        }

        public void DoRestart()
        {
            
        }
    }
}