using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using DefaultNamespace;
using Environments;
using Google.Protobuf.Collections;
using Ik;
using UnityEngine;
using UnityEngine.Events;
using UnityEngine.SceneManagement;
using Quaternion = UnityEngine.Quaternion;
using Random = UnityEngine.Random;


namespace ExternalCommunication
{
    public class CommunicationService : MonoBehaviour
    {
        public static int decisionPeriod = 10;
        public static bool noGraphics = false;

        private Dictionary<int, EnvManager> _envManagers;
        private bool _processingStep;
        private int _stepsCompleted = 0;
        private int _stepsToSimulate = 0;
        private float _startTime;
        private float _timeScale;
        private EnvironmentSpawner _spawner;
        private ScreenshotManager _screenshotManager;
        private FlyCamera _flyCamera;
        private bool _initialized;


        public void Initialize(RepeatedField<ResetParameters> resetMsgEnvsToReset)
        {
            _spawner = FindAnyObjectByType<EnvironmentSpawner>();
            _screenshotManager = FindAnyObjectByType<ScreenshotManager>();
            _flyCamera = FindAnyObjectByType<FlyCamera>();

            _screenshotManager.DoAwake();
            _spawner.DoAwake(resetMsgEnvsToReset);

            _envManagers = _spawner.GetEnvs();
            _initialized = true;
        }

        public void ApplyParameters(Configure parameters)
        {
            foreach (var configureParameters in parameters.EnvsToConfigure)
            {
                _envManagers.TryGetValue(configureParameters.Index, out var env);
                env?.ApplyParameters(configureParameters);
            }
        }

        public IEnumerator DoReset(Reset resetMsg, Action<Observations> callback = null)
        {
            if (resetMsg.ReloadScene || !_initialized)
            {
                Resources.UnloadUnusedAssets();
                Random.InitState(0);

                if (SceneManager.sceneCount == 1)
                {
                    var op = SceneManager.LoadSceneAsync("Empty", new LoadSceneParameters(LoadSceneMode.Additive, LocalPhysicsMode.Physics3D));
                    yield return op;
                }

                var opr = SceneManager.UnloadSceneAsync("ExternalControlScene");
                yield return opr;
                opr = SceneManager.LoadSceneAsync("ExternalControlScene", new LoadSceneParameters(LoadSceneMode.Additive, LocalPhysicsMode.Physics3D));
                yield return opr;

                yield return null;
                SceneManager.SetActiveScene(SceneManager.GetSceneByName("ExternalControlScene"));

                opr = SceneManager.UnloadSceneAsync("Empty");
                yield return opr;
            }

            yield return null;
            Resources.UnloadUnusedAssets();

            Initialize(resetMsg.EnvsToReset);
            ResetEnvironments(resetMsg);
            SceneManager.GetActiveScene().GetPhysicsScene().Simulate(Time.fixedDeltaTime);

            _processingStep = false;
            _stepsCompleted = Mathf.Max(decisionPeriod, _stepsToSimulate);
            var prepareObservations = PrepareObservations();
            callback?.Invoke(prepareObservations);
            yield return null;
        }

        public Observations DoStep(Step stepMsg)
        {
            if (!_processingStep)
            {
                ProcessStep(stepMsg);
                _processingStep = true;
                _stepsCompleted = 0;
                _stepsToSimulate = stepMsg.StepCount > 0 ? stepMsg.StepCount : decisionPeriod;
                _timeScale = stepMsg.TimeScale > 0 ? stepMsg.TimeScale : Time.timeScale;
                _startTime = Time.time;
            }


            while ((Time.time > (_startTime + _stepsCompleted * Time.fixedDeltaTime / _timeScale) || _timeScale > 10 || noGraphics) && _stepsCompleted < _stepsToSimulate)
            {
                SceneManager.GetActiveScene().GetPhysicsScene().Simulate(Time.fixedDeltaTime);
                foreach (var keyValuePair in _envManagers)
                {
                    keyValuePair.Value.UpdateSync();
                }

                _stepsCompleted++;
            }

            if (_stepsCompleted >= _stepsToSimulate)
            {
                _processingStep = false;
                return PrepareObservations();
            }

            return null;
        }

        public Observations PrepareObservations()
        {
            var controlRequest = new Observations();
            controlRequest.Agents.AddRange(_envManagers.Select(env =>
            {
                var buildArmControllerMessage = BuildObservations(env.Value.BuildObservationMessage(), env.Value.GetArticulationChain());
                buildArmControllerMessage.Index = env.Key;
                return buildArmControllerMessage;
            }));
            return controlRequest;
        }

        public void ResetEnvironments(Reset reset)
        {
            if (_flyCamera != null && reset?.CameraPosition != null)
            {
                ResetCamera(reset);
            }

            if (reset.EnvsToReset == null || reset.EnvsToReset.Count == 0)
            {
                _envManagers.Values.ToList().ForEach(env => env.DoRestart());
            }
            else
            {
                for (int i = 0; i < reset.EnvsToReset.Count; i++)
                {
                    var resetParameters = reset.EnvsToReset[i];
                    var index = resetParameters.Index;
                    if (_envManagers.ContainsKey(index))
                    {
                        _envManagers[index].DoRestart(resetParameters);
                    }
                }
            }
        }

        private void ResetCamera(Reset reset)
        {
            var transformPosition = reset.CameraPosition.Position.ToUnityVector();
            _flyCamera.transform.position = transformPosition;
            var transformRotation = reset.CameraPosition.Euler != null ? Quaternion.Euler(reset.CameraPosition.Euler.ToUnityVector()) : reset.CameraPosition.Orientation != null ? reset.CameraPosition.Orientation.ToUnityQuaternion() : Quaternion.identity;
            _flyCamera.transform.rotation = transformRotation;
        }

        private void ProcessStep(Step responseMsg)
        {
            if (responseMsg.Controls != null)
            {
                foreach (var msg in responseMsg.Controls)
                {
                    _envManagers[msg.Index].RecieveMessage(BuildControl(msg));
                }
            }
        }

        private GrpcControl BuildControl(AgentControls msg)
        {
            var grpcControl = new GrpcControl();
            grpcControl.grasp = msg.ActivateGrip;
            grpcControl.immobile = msg.BaseImmobile;

            grpcControl.angles = new float[msg.JointTargetsDeg.Count];
            for (int i = 0; i < msg.JointTargetsDeg.Count; i++)
            {
                grpcControl.angles[i] = msg.JointTargetsDeg[i];
            }

            if (msg.TargetBasePose != null)
            {
                if (msg.TargetBasePose.Position != null) grpcControl.basePosition = msg.TargetBasePose.Position.ToUnityVector();
                if (msg.TargetBasePose.Orientation != null) grpcControl.baseRotation = msg.TargetBasePose.Orientation.ToUnityQuaternion();
                if (msg.TargetBasePose.Euler != null) grpcControl.baseRotation = Quaternion.Euler(msg.TargetBasePose.Euler.ToUnityVector());
            }

            return grpcControl;
        }


        private static AgentObservation BuildObservations(GrpcMessage msg, ArticulationChainComponent controller)
        {
            var ikRequest = new AgentObservation()
            {
                CurrentJointAnglesDeg =
                {
                    0.0f,
                    msg.floats[0],
                    msg.floats[1],
                    msg.floats[2],
                    msg.floats[3],
                    msg.floats[4],
                    msg.floats[5],
                    0.0f
                },
                IsBetweenGripper = msg.bools[0],
                GripSuccessful = msg.bools[1],
                BetweenGripper = msg.strings["gripper"],
            };

            ikRequest.TransformsByNameArmFrame.Add(msg.namedTransforms.ToDictionary(
                pair => pair.Key,
                pair => MessageUtils.BuildLocalTransform(pair.Value, controller.bodyParts[0].gameObject)
            ));

            ikRequest.TransformsByNameEnvFrame.Add(msg.namedTransforms.ToDictionary(
                pair => pair.Key,
                pair => MessageUtils.BuildLocalTransform(pair.Value, controller.transform.parent.gameObject)
            ));

            var armBaseTransform = msg.transforms[0];
            var inverse = Quaternion.Inverse(armBaseTransform.rotation);
            foreach (var childTransform in msg.transforms.GetRange(1, msg.transforms.Count - 1))
            {
                var values = new Ik.Transform();
                values.Position = armBaseTransform.InverseTransformPoint(childTransform.position).BuildVector3();
                values.Euler = (inverse * childTransform.rotation).eulerAngles.BuildVector3();
                values.Orientation = (inverse * childTransform.rotation).BuildQuaternion();
                ikRequest.LinkTransformsArm.Add(values);

                values = new Ik.Transform();
                values.Position = childTransform.localPosition.BuildVector3();
                values.Euler = childTransform.localEulerAngles.BuildVector3();
                values.Orientation = childTransform.localRotation.BuildQuaternion();
                ikRequest.LinkTransformsArmRelative.Add(values);
            }

            return ikRequest;
        }
    }
}