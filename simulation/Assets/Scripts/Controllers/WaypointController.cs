using System;
using Ik;
using UnityEngine;
using Quaternion = UnityEngine.Quaternion;
using Transform = UnityEngine.Transform;
using Vector3 = UnityEngine.Vector3;

namespace Controllers
{
    public class WaypointController : MonoBehaviour
    {
        public Transform waypoint;
        public float maxSpeed = 1;
        public float maxRotation = 3;

        public WheelController controller;

        public PIDController velocityPID;
        public PIDController yawPID;

        public double allowedTolerance = 0.1f;

        // public void FixedUpdate()
        // {
        //     if (Physics.simulationMode == SimulationMode.FixedUpdate && waypoint != null)
        //     {
        //         StepController();
        //     }
        // }

        public void StepController()
        {
            var baseBody = controller.GetComponent<ArticulationBody>();

            var direction = waypoint.position - transform.position;
            var controlVelocity = velocityPID.Iterate(Mathf.Clamp01(direction.magnitude)) * direction.normalized;
            controlVelocity = controlVelocity.magnitude > maxSpeed ? controlVelocity.normalized * maxSpeed : controlVelocity;
            baseBody.AddForce((controlVelocity - baseBody.linearVelocity) / Time.fixedDeltaTime, ForceMode.Acceleration);

            var forwardAngle = Vector3.SignedAngle(transform.forward, waypoint.position - transform.position, transform.up);
            var backwardAngle = Vector3.SignedAngle(-transform.forward, waypoint.position - transform.position, transform.up);
            var controlAngle = Mathf.Abs(forwardAngle) < Mathf.Abs(backwardAngle) ? forwardAngle : backwardAngle;

            controlAngle = Vector3.SignedAngle(transform.forward, waypoint.forward, transform.up);

            var controlAngular = new Vector3(0, yawPID.Iterate(Mathf.Clamp(controlAngle, -maxRotation, maxRotation)), 0);
            controlAngular = controlAngular.magnitude > maxRotation ? controlAngular.normalized * maxRotation : controlAngular;
            baseBody.AddTorque((controlAngular - baseBody.angularVelocity) / Time.fixedDeltaTime, ForceMode.Acceleration);
        }


        public void ApplyConfiguration(WheelParameters parametersWheelParameters)
        {
            velocityPID.SetParameters(parametersWheelParameters.VelocityPID);
            yawPID.SetParameters(parametersWheelParameters.YawPID);
        }

        public void DoRestart(Transform target)
        {
            velocityPID.Reset();
            yawPID.Reset();
            waypoint.position = target.transform.position;
            waypoint.rotation = target.transform.rotation;
        }

        public void ApplyControls(Vector3? targetPosition, Quaternion? targetRotation)
        {
            if (targetPosition != null) waypoint.localPosition = targetPosition.Value;
            if (targetRotation != null) waypoint.rotation = targetRotation.Value;
            StepController();
        }
    }
}