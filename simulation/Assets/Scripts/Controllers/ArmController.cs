using DefaultNamespace;
using ExternalCommunication;
using Google.Protobuf.Collections;
using Ik;
using UnityEngine;
using Transform = UnityEngine.Transform;
using Vector3 = UnityEngine.Vector3;

namespace Controllers
{
    public class ArmController : MonoBehaviour
    {
        public ArticulationChainComponent chain;
        public Detector sensor;
        public GraspController graspController;
        public Transform target;

        public bool topOrientation;
        public bool forwardOrientation;

        public float[] currentControlAngles;
        private bool _doReset;
        private bool _doGrasp;

        public void DoRestart()
        {
            graspController.Restart();
        }

        // public void FixedUpdate()
        // {
        //     if (Physics.simulationMode != SimulationMode.Script) UpdateController();
        // }

        public void UpdateController()
        {
            if (_doReset)
            {
                DoRestart();
                _doReset = false;
            }

            graspController.graspEnabled = _doGrasp;
            ApplyJointAngles(currentControlAngles);
        }


        void ApplyJointAngles(float[] angles)
        {
            int max_angle_diff = 5;
            for (int i = 0; i < angles.Length; i++)
            {
                var controller = chain.controllers[i + 1];
                // var current = controller.articulationBody.GetRotationInReducedSpace()[0];
                var target = angles[i];
                // if (Mathf.Abs(target - current) > 1f) target = current + Mathf.Clamp(target - current, -max_angle_diff, max_angle_diff);
                controller.SetDriveTargetsNorm(controller.ComputeNormalizedDriveTarget(controller.XParameters, target), 0, 0);
            }
        }

        public GrpcMessage BuildGrpcMessage(GrpcMessage grpcMessage)
        {
            grpcMessage.floats.Add(chain.bodyParts[1].GetRotationInReducedSpace()[0]);
            grpcMessage.floats.Add(chain.bodyParts[2].GetRotationInReducedSpace()[0]);
            grpcMessage.floats.Add(chain.bodyParts[3].GetRotationInReducedSpace()[0]);
            grpcMessage.floats.Add(chain.bodyParts[4].GetRotationInReducedSpace()[0]);
            grpcMessage.floats.Add(chain.bodyParts[5].GetRotationInReducedSpace()[0]);
            grpcMessage.floats.Add(chain.bodyParts[6].GetRotationInReducedSpace()[0]);

            var rotation = new Vector3(0, 0, 0);
            if (topOrientation)
            {
                rotation = new Vector3(0, -1, 0);
            }

            if (forwardOrientation)
            {
                topOrientation = false;
                rotation = new Vector3(0, 0, 1);
            }

            grpcMessage.vectors.Add(rotation);
            grpcMessage.bools.Add(sensor.objectDetected);
            grpcMessage.bools.Add(graspController.HaveGrasp());

            grpcMessage.transforms.Add(chain.bodyParts[0].transform);
            grpcMessage.transforms.Add(chain.bodyParts[1].transform);
            grpcMessage.transforms.Add(chain.bodyParts[2].transform);
            grpcMessage.transforms.Add(chain.bodyParts[3].transform);
            grpcMessage.transforms.Add(chain.bodyParts[4].transform);
            grpcMessage.transforms.Add(chain.bodyParts[5].transform);
            grpcMessage.transforms.Add(chain.bodyParts[6].transform);
            grpcMessage.transforms.Add(target.transform);

            grpcMessage.strings.Add("gripper", graspController.sensor.collidedWithName);

            return grpcMessage;
        }

        public void ApplyControls(GrpcControl message)
        {
            currentControlAngles = message.angles;
            _doReset = message.reset;
            _doGrasp = message.grasp;

            UpdateController();
            graspController.UpdateController(message.grasp);
        }

        public void ApplyConfiguration(RepeatedField<LinkParameters> parameters)
        {
            foreach (var parametersLinkParameter in parameters)
            {
                if (parametersLinkParameter.LinkIndex > 0 && parametersLinkParameter.LinkIndex < 7)
                {
                    var link = chain.bodyParts[parametersLinkParameter.LinkIndex];
                    if (parametersLinkParameter.Stiffness != 0) link.SetDriveStiffness(ArticulationDriveAxis.X, parametersLinkParameter.Stiffness);
                    if (parametersLinkParameter.Damping != 0) link.SetDriveDamping(ArticulationDriveAxis.X, parametersLinkParameter.Damping);
                    if (parametersLinkParameter.ForceLimit != 0) link.SetDriveForceLimit(ArticulationDriveAxis.X, parametersLinkParameter.ForceLimit);
                }
            }
        }
    }
}