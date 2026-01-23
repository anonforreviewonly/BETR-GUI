using System.Collections.Generic;
using Controllers;
using ExternalCommunication;
using Ik;
using UnityEngine;
using Quaternion = UnityEngine.Quaternion;
using Transform = Ik.Transform;
using Vector3 = UnityEngine.Vector3;

namespace Environments
{
    public class GeneralEnvManager : EnvManager
    {
        public ArmController armController;
        public WheelController wheelController;
        public WaypointController waypointController;
        public ArticulationChainComponent articulationChain;

        public List<GameObject> gameObjects = new();
        public Environment scene;

        public override void DoRestart()
        {
            DoRestart(null);
        }

        public override void ApplyParameters(ConfigureParameters parameters)
        {
            armController.ApplyConfiguration(parameters.LinkParameters);
            wheelController?.ApplyConfiguration(parameters.WheelParameters);
            waypointController?.ApplyConfiguration(parameters.WheelParameters);
        }

        public override void DoRestart(ResetParameters parameters)
        {
            armController.DoRestart();
            wheelController?.DoRestart();

            if (parameters == null) articulationChain.Restart(transform.position, Quaternion.identity);

            UnityEngine.Transform waypoint = transform;
            if (parameters?.EnvCubeBowl != null)
            {
                EnvResetMapping.ResetCubeBowl(parameters.EnvCubeBowl, gameObjects, transform);
                waypoint = RestartAgent(parameters.EnvCubeBowl.AgentPosition);
            }

            if (parameters?.EnvTableware != null)
            {
                EnvResetMapping.ResetTableWare(parameters.EnvTableware, gameObjects, transform);
                waypoint = RestartAgent(parameters.EnvTableware.AgentPosition);
            }

            if (parameters?.EnvTrashPicking != null)
            {
                EnvResetMapping.ResetTrashPicking(parameters.EnvTrashPicking, gameObjects, transform);
                waypoint = RestartAgent(parameters.EnvTrashPicking.AgentPosition);
            }

            if (parameters?.EnvSpheres != null)
            {
                EnvResetMapping.ResetSpheres(parameters.EnvSpheres, gameObjects, transform);
                waypoint = RestartAgent(parameters.EnvSpheres.AgentPosition);
            }

            waypointController?.DoRestart(waypoint);
        }

        private UnityEngine.Transform RestartAgent(Transform protoTransform)
        {
            if (protoTransform != null)
            {
                var agentTransform = protoTransform.ToUnity();
                agentTransform.position = transform.TransformPoint(agentTransform.position);
                articulationChain.Restart(agentTransform.position, agentTransform.rotation);
                return agentTransform;
            }
            else
            {
                articulationChain.Restart(transform.position, Quaternion.identity);
                return transform;
            }
        }

        public override GrpcMessage BuildObservationMessage()
        {
            GrpcMessage grpcMessage = new GrpcMessage();
            foreach (var obj in gameObjects)
            {
                grpcMessage.namedTransforms[obj.name] = obj.transform;
            }

            return armController.BuildGrpcMessage(grpcMessage);
        }

        public override void RecieveMessage(GrpcControl control)
        {
            waypointController?.ApplyControls(control.basePosition, control.baseRotation);
            armController?.ApplyControls(control);
            articulationChain.GetRoot().immovable = control.immobile;

            if (control.reset) DoRestart();
        }

        public override ArticulationChainComponent GetArticulationChain()
        {
            return articulationChain;
        }

        public override void UpdateSync()
        {
            armController.UpdateController();
            armController.graspController.UpdateFingers();
            waypointController?.StepController();
        }
    }
}