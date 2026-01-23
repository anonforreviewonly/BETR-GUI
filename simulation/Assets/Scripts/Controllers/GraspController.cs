using System;
using UnityEngine;

namespace Controllers
{
    public class GraspController : MonoBehaviour
    {
        public ArticulationBody armAb;
        public Detector sensor;
        public bool graspEnabled;
        public bool graspPossible;
        private FixedJoint _connectionJoint;

        public ArticulationBody fingerA;
        public ArticulationBody fingerB;

        private const float FingerInitialPosition = 0.02f;
        private float _targetA = FingerInitialPosition;
        private float _targetB = FingerInitialPosition;
        private float storedMass = 1f;
        private Vector3 storedInertia;

        // private void Start()
        // {
        //     if (Physics.simulationMode != SimulationMode.Script) RemoveGrasp();
        // }
        //
        // private void FixedUpdate()
        // {
        //     if (Physics.simulationMode != SimulationMode.Script) UpdateController(graspEnabled);
        // }

        public void UpdateController(bool grasp)
        {
            graspEnabled = grasp;

            if (graspEnabled && sensor.collidedWith != null && _connectionJoint == null)
            {
                var targetRigidBody = sensor.collidedWith.GetComponent<Rigidbody>();
                if (targetRigidBody == null) targetRigidBody = sensor.collidedWith.GetComponentInParent<Rigidbody>();

                if (targetRigidBody != null)
                {
                    var body = sensor.collidedWith;
                    graspPossible = body != null; // && collisionDetectors.All(det => det.collidedWith.Count > 0 && body == det.collidedgit With[0]);
                    if (graspPossible && _connectionJoint == null)
                    {
                        _connectionJoint = targetRigidBody.gameObject.AddComponent<FixedJoint>();
                        storedMass = targetRigidBody.mass;
                        storedInertia = targetRigidBody.inertiaTensor;
                        targetRigidBody.automaticInertiaTensor = false;
                        targetRigidBody.mass = 0.001f;
                        targetRigidBody.inertiaTensor = new Vector3(0.000001f, 0.000001f, 0.000001f);

                        if (armAb != null)
                        {
                            _connectionJoint.connectedArticulationBody = armAb;
                        }
                    }
                }
            }

            UpdateFingers();

            if (!graspEnabled && HaveGrasp())
            {
                RemoveGrasp();
            }
        }

        public bool HaveGrasp()
        {
            return _connectionJoint != null;
        }

        public void UpdateFingers()
        {
            if (_connectionJoint != null)
            {
                if (fingerA.GetComponent<Detector>().objectDetected == false) _targetA += -0.0005f;
                if (fingerB.GetComponent<Detector>().objectDetected == false) _targetB += -0.0005f;
                fingerA.SetDriveTarget(ArticulationDriveAxis.Z, _targetA);
                fingerB.SetDriveTarget(ArticulationDriveAxis.Z, _targetB);
                fingerA.GetComponent<Collider>().isTrigger = true;
                fingerB.GetComponent<Collider>().isTrigger = true;
            }
        }

        private void RemoveGrasp()
        {
            if (_connectionJoint != null)
            {
                _connectionJoint.GetComponent<Rigidbody>().mass = storedMass;
                _connectionJoint.GetComponent<Rigidbody>().inertiaTensor = storedInertia;
                DestroyImmediate(_connectionJoint);
                _connectionJoint = null;
            }

            fingerA.SetDriveTarget(ArticulationDriveAxis.Z, FingerInitialPosition);
            fingerB.SetDriveTarget(ArticulationDriveAxis.Z, FingerInitialPosition);
            fingerA.GetComponent<Collider>().isTrigger = false;
            fingerB.GetComponent<Collider>().isTrigger = false;
        }

        public void Restart()
        {
            RemoveGrasp();
        }
    }
}